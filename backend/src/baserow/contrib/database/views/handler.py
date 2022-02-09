from collections import defaultdict
from copy import deepcopy
from typing import Dict, Any, List, Optional, Iterable, Tuple

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models as django_models
from django.db.models import F, Count

from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.fields.field_filters import FilterBuilder
from baserow.contrib.database.fields.field_sortings import AnnotatedOrder
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.signals import row_created
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import (
    extract_allowed,
    set_allowed_attrs,
    get_model_reference_field_name,
)
from .exceptions import (
    ViewDoesNotExist,
    ViewNotInTable,
    UnrelatedFieldError,
    ViewFilterDoesNotExist,
    ViewFilterNotSupported,
    ViewFilterTypeNotAllowedForField,
    ViewSortDoesNotExist,
    ViewSortNotSupported,
    ViewSortFieldAlreadyExist,
    ViewSortFieldNotSupported,
    ViewDoesNotSupportFieldOptions,
    FieldAggregationNotSupported,
    CannotShareViewTypeError,
)
from .models import View, ViewFilter, ViewSort
from .registries import (
    view_type_registry,
    view_filter_type_registry,
    view_aggregation_type_registry,
)
from .signals import (
    view_created,
    view_updated,
    view_deleted,
    views_reordered,
    view_filter_created,
    view_filter_updated,
    view_filter_deleted,
    view_sort_created,
    view_sort_updated,
    view_sort_deleted,
    view_field_options_updated,
)
from .validators import EMPTY_VALUES
from ..table.models import Table, GeneratedTableModel


class ViewHandler:
    def get_view(self, view_id, view_model=None, base_queryset=None):
        """
        Selects a view and checks if the user has access to that view. If everything
        is fine the view is returned.

        :param view_id: The identifier of the view that must be returned.
        :type view_id: int
        :param view_model: If provided that models objects are used to select the
            view. This can for example be useful when you want to select a GridView or
            other child of the View model.
        :type view_model: Type[View]
        :param base_queryset: The base queryset from where to select the view
            object. This can for example be used to do a `select_related`. Note that
            if this is used the `view_model` parameter doesn't work anymore.
        :type base_queryset: Queryset
        :raises ViewDoesNotExist: When the view with the provided id does not exist.
        :type view_model: View
        :return:
        """

        if not view_model:
            view_model = View

        if base_queryset is None:
            base_queryset = view_model.objects

        try:
            view = base_queryset.select_related("table__database__group").get(
                pk=view_id
            )
        except View.DoesNotExist:
            raise ViewDoesNotExist(f"The view with id {view_id} does not exist.")

        if TrashHandler.item_has_a_trashed_parent(view.table, check_item_also=True):
            raise ViewDoesNotExist(f"The view with id {view_id} does not exist.")

        return view

    def create_view(self, user, table, type_name, **kwargs):
        """
        Creates a new view based on the provided type.

        :param user: The user on whose behalf the view is created.
        :type user: User
        :param table: The table that the view instance belongs to.
        :type table: Table
        :param type_name: The type name of the view.
        :type type_name: str
        :param kwargs: The fields that need to be set upon creation.
        :type kwargs: object
        :return: The created view instance.
        :rtype: View
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        # Figure out which model to use for the given view type.
        view_type = view_type_registry.get(type_name)
        model_class = view_type.model_class
        view_values = view_type.prepare_values(kwargs, table, user)
        allowed_fields = [
            "name",
            "filter_type",
            "filters_disabled",
        ] + view_type.allowed_fields
        view_values = extract_allowed(view_values, allowed_fields)
        last_order = model_class.get_last_order(table)

        instance = model_class.objects.create(
            table=table, order=last_order, **view_values
        )

        view_type.view_created(view=instance)
        view_created.send(self, view=instance, user=user, type_name=type_name)

        return instance

    def update_view(self, user, view, **kwargs):
        """
        Updates an existing view instance.

        :param user: The user on whose behalf the view is updated.
        :type user: User
        :param view: The view instance that needs to be updated.
        :type view: View
        :param kwargs: The fields that need to be updated.
        :type kwargs: object
        :raises ValueError: When the provided view not an instance of View.
        :return: The updated view instance.
        :rtype: View
        """

        if not isinstance(view, View):
            raise ValueError("The view is not an instance of View.")

        group = view.table.database.group
        group.has_user(user, raise_error=True)

        view_type = view_type_registry.get_by_model(view)
        view_values = view_type.prepare_values(kwargs, view.table, user)
        allowed_fields = [
            "name",
            "filter_type",
            "filters_disabled",
        ] + view_type.allowed_fields
        view = set_allowed_attrs(view_values, allowed_fields, view)
        view.save()

        view_updated.send(self, view=view, user=user)

        return view

    def order_views(self, user, table, order):
        """
        Updates the order of the views in the given table. The order of the views
        that are not in the `order` parameter set set to `0`.

        :param user: The user on whose behalf the views are ordered.
        :type user: User
        :param table: The table of which the views must be updated.
        :type table: Table
        :param order: A list containing the view ids in the desired order.
        :type order: list
        :raises ViewNotInTable: If one of the view ids in the order does not belong
            to the table.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        queryset = View.objects.filter(table_id=table.id)
        view_ids = queryset.values_list("id", flat=True)

        for view_id in order:
            if view_id not in view_ids:
                raise ViewNotInTable(view_id)

        View.order_objects(queryset, order)
        views_reordered.send(self, table=table, order=order, user=user)

    def delete_view(self, user, view):
        """
        Deletes an existing view instance.

        :param user: The user on whose behalf the view is deleted.
        :type user: User
        :param view: The view instance that needs to be deleted.
        :type view: View
        :raises ViewDoesNotExist: When the view with the provided id does not exist.
        """

        if not isinstance(view, View):
            raise ValueError("The view is not an instance of View")

        group = view.table.database.group
        group.has_user(user, raise_error=True)

        view_id = view.id
        view.delete()

        view_deleted.send(self, view_id=view_id, view=view, user=user)

    def update_field_options(self, user, view, field_options, fields=None):
        """
        Updates the field options with the provided values if the field id exists in
        the table related to the view.

        :param user: The user on whose behalf the request is made.
        :type user: User
        :param view: The view for which the field options need to be updated.
        :type view: View
        :param field_options: A dict with the field ids as the key and a dict
            containing the values that need to be updated as value.
        :type field_options: dict
        :param fields: Optionally a list of fields can be provided so that they don't
            have to be fetched again.
        :type fields: None or list
        :raises UnrelatedFieldError: When the provided field id is not related to the
            provided view.
        """

        view.table.database.group.has_user(user, raise_error=True)

        if not fields:
            fields = Field.objects.filter(table=view.table)

        try:
            model = view._meta.get_field("field_options").remote_field.through
        except FieldDoesNotExist:
            raise ViewDoesNotSupportFieldOptions(
                "This view does not support field options."
            )

        field_name = get_model_reference_field_name(model, View)

        if not field_name:
            raise ValueError(
                "The model doesn't have a relationship with the View model or any "
                "descendants."
            )

        view_type = view_type_registry.get_by_model(view.specific_class)
        field_options = view_type.before_field_options_update(
            view, field_options, fields
        )

        allowed_field_ids = [field.id for field in fields]
        for field_id, options in field_options.items():
            if int(field_id) not in allowed_field_ids:
                raise UnrelatedFieldError(
                    f"The field id {field_id} is not related to the view."
                )
            model.objects.update_or_create(
                field_id=field_id, defaults=options, **{field_name: view}
            )

        view_field_options_updated.send(self, view=view, user=user)

    def field_type_changed(self, field):
        """
        This method is called by the FieldHandler when the field type of a field has
        changed. It could be that the field has filters or sortings that are not
        compatible anymore. If that is the case then those need to be removed.

        :param field: The new field object.
        :type field: Field
        """

        field_type = field_type_registry.get_by_model(field.specific_class)

        # If the new field type does not support sorting then all sortings will be
        # removed.
        if not field_type.check_can_order_by(field):
            field.viewsort_set.all().delete()

        # Check which filters are not compatible anymore and remove those.
        for filter in field.viewfilter_set.all():
            filter_type = view_filter_type_registry.get(filter.type)

            if not filter_type.field_is_compatible(field):
                filter.delete()

    def _get_filter_builder(
        self, view: View, model: GeneratedTableModel
    ) -> FilterBuilder:
        """
        Constructs a FilterBuilder object based on the provided view's filter.

        :param view: The view where to fetch the fields from.
        :param model: The generated model containing all fields.
        :return: FilterBuilder object with the view's filter applied.
        """

        # The table model has to be dynamically generated
        if not hasattr(model, "_field_objects"):
            raise ValueError("A queryset of the table model is required.")

        filter_builder = FilterBuilder(filter_type=view.filter_type)
        for view_filter in view.viewfilter_set.all():
            if view_filter.field_id not in model._field_objects:
                raise ValueError(
                    f"The table model does not contain field "
                    f"{view_filter.field_id}."
                )
            field_object = model._field_objects[view_filter.field_id]
            field_name = field_object["name"]
            model_field = model._meta.get_field(field_name)
            view_filter_type = view_filter_type_registry.get(view_filter.type)
            filter_builder.filter(
                view_filter_type.get_filter(
                    field_name, view_filter.value, model_field, field_object["field"]
                )
            )

        return filter_builder

    def apply_filters(self, view, queryset):
        """
        Applies the view's filter to the given queryset.

        :param view: The view where to fetch the fields from.
        :type view: View
        :param queryset: The queryset where the filters need to be applied to.
        :type queryset: QuerySet
        :raises ValueError: When the queryset's model is not a table model or if the
            table model does not contain the one of the fields.
        :return: The queryset where the filters have been applied to.
        :type: QuerySet
        """

        model = queryset.model

        if view.filters_disabled:
            return queryset

        filter_builder = self._get_filter_builder(view, model)
        return filter_builder.apply_to_queryset(queryset)

    def get_filter(self, user, view_filter_id, base_queryset=None):
        """
        Returns an existing view filter by the given id.

        :param user: The user on whose behalf the view filter is requested.
        :type user: User
        :param view_filter_id: The id of the view filter.
        :type view_filter_id: int
        :param base_queryset: The base queryset from where to select the view filter
            object. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises ViewFilterDoesNotExist: The the requested view does not exists.
        :return: The requested view filter instance.
        :type: ViewFilter
        """

        if base_queryset is None:
            base_queryset = ViewFilter.objects

        try:
            view_filter = base_queryset.select_related(
                "view__table__database__group"
            ).get(pk=view_filter_id)
        except ViewFilter.DoesNotExist:
            raise ViewFilterDoesNotExist(
                f"The view filter with id {view_filter_id} does not exist."
            )

        if TrashHandler.item_has_a_trashed_parent(
            view_filter.view.table, check_item_also=True
        ):
            raise ViewFilterDoesNotExist(
                f"The view filter with id {view_filter_id} does not exist."
            )

        group = view_filter.view.table.database.group
        group.has_user(user, raise_error=True)

        return view_filter

    def create_filter(self, user, view, field, type_name, value):
        """
        Creates a new view filter. The rows that are visible in a view should always
        be filtered by the related view filters.

        :param user: The user on whose behalf the view filter is created.
        :type user: User
        :param view: The view for which the filter needs to be created.
        :type: View
        :param field: The field that the filter should compare the value with.
        :type field: Field
        :param type_name: The filter type, allowed values are the types in the
            view_filter_type_registry `equal`, `not_equal` etc.
        :type type_name: str
        :param value: The value that the filter must apply to.
        :type value: str
        :raises ViewFilterNotSupported: When the provided view does not support
            filtering.
        :raises ViewFilterTypeNotAllowedForField: When the field does not support the
            filter type.
        :raises FieldNotInTable:  When the provided field does not belong to the
            provided view's table.
        :return: The created view filter instance.
        :rtype: ViewFilter
        """

        group = view.table.database.group
        group.has_user(user, raise_error=True)

        # Check if view supports filtering
        view_type = view_type_registry.get_by_model(view.specific_class)
        if not view_type.can_filter:
            raise ViewFilterNotSupported(
                f"Filtering is not supported for {view_type.type} views."
            )

        view_filter_type = view_filter_type_registry.get(type_name)
        field_type = field_type_registry.get_by_model(field.specific_class)

        # Check if the field is allowed for this filter type.
        if not view_filter_type.field_is_compatible(field):
            raise ViewFilterTypeNotAllowedForField(type_name, field_type.type)

        # Check if field belongs to the grid views table
        if not view.table.field_set.filter(id=field.pk).exists():
            raise FieldNotInTable(
                f"The field {field.pk} does not belong to table {view.table.id}."
            )

        view_filter = ViewFilter.objects.create(
            view=view, field=field, type=view_filter_type.type, value=value
        )

        view_filter_created.send(self, view_filter=view_filter, user=user)

        return view_filter

    def update_filter(self, user, view_filter, **kwargs):
        """
        Updates the values of an existing view filter.

        :param user: The user on whose behalf the view filter is updated.
        :type user: User
        :param view_filter: The view filter that needs to be updated.
        :type view_filter: ViewFilter
        :param kwargs: The values that need to be updated, allowed values are
            `field`, `value` and `type_name`.
        :type kwargs: dict
        :raises ViewFilterTypeNotAllowedForField: When the field does not supports the
            filter type.
        :raises FieldNotInTable: When the provided field does not belong to the
            view's table.
        :return: The updated view filter instance.
        :rtype: ViewFilter
        """

        group = view_filter.view.table.database.group
        group.has_user(user, raise_error=True)

        type_name = kwargs.get("type_name", view_filter.type)
        field = kwargs.get("field", view_filter.field)
        value = kwargs.get("value", view_filter.value)
        view_filter_type = view_filter_type_registry.get(type_name)
        field_type = field_type_registry.get_by_model(field.specific_class)

        # Check if the field is allowed for this filter type.
        if not view_filter_type.field_is_compatible(field):
            raise ViewFilterTypeNotAllowedForField(type_name, field_type.type)

        # If the field has changed we need to check if the field belongs to the table.
        if (
            field.id != view_filter.field_id
            and not view_filter.view.table.field_set.filter(id=field.pk).exists()
        ):
            raise FieldNotInTable(
                f"The field {field.pk} does not belong to table "
                f"{view_filter.view.table.id}."
            )

        view_filter.field = field
        view_filter.value = value
        view_filter.type = type_name
        view_filter.save()

        view_filter_updated.send(self, view_filter=view_filter, user=user)

        return view_filter

    def delete_filter(self, user, view_filter):
        """
        Deletes an existing view filter.

        :param user: The user on whose behalf the view filter is deleted.
        :type user: User
        :param view_filter: The view filter instance that needs to be deleted.
        :type view_filter: ViewFilter
        """

        group = view_filter.view.table.database.group
        group.has_user(user, raise_error=True)

        view_filter_id = view_filter.id
        view_filter.delete()

        view_filter_deleted.send(
            self, view_filter_id=view_filter_id, view_filter=view_filter, user=user
        )

    def apply_sorting(self, view, queryset, restrict_to_field_ids=None):
        """
        Applies the view's sorting to the given queryset. The first sort, which for now
        is the first created, will always be applied first. Secondary sortings are
        going to be applied if the values of the first sort rows are the same.

        Example:

        id | field_1 | field_2
        1  | Bram    | 20
        2  | Bram    | 10
        3  | Elon    | 30

        If we are going to sort ascending on field_1 and field_2 the resulting ids are
        going to be 2, 1 and 3 in that order.

        :param view: The view where to fetch the sorting from.
        :type view: View
        :param queryset: The queryset where the sorting need to be applied to.
        :type queryset: QuerySet
        :raises ValueError: When the queryset's model is not a table model or if the
            table model does not contain the one of the fields.
        :param restrict_to_field_ids: Only field ids in this iterable will have their
            view sorts applied in the resulting queryset.
        :type restrict_to_field_ids: Optional[Iterable[int]]
        :return: The queryset where the sorting has been applied to.
        :type: QuerySet
        """

        model = queryset.model

        # If the model does not have the `_field_objects` property then it is not a
        # generated table model which is not supported.
        if not hasattr(model, "_field_objects"):
            raise ValueError("A queryset of the table model is required.")

        order_by = []

        qs = view.viewsort_set
        if restrict_to_field_ids is not None:
            qs = qs.filter(field_id__in=restrict_to_field_ids)
        for view_sort in qs.all():
            # If the to be sort field is not present in the `_field_objects` we
            # cannot filter so we raise a ValueError.
            if view_sort.field_id not in model._field_objects:
                raise ValueError(
                    f"The table model does not contain field {view_sort.field_id}."
                )

            field = model._field_objects[view_sort.field_id]["field"]
            field_name = model._field_objects[view_sort.field_id]["name"]
            field_type = model._field_objects[view_sort.field_id]["type"]

            order = field_type.get_order(field, field_name, view_sort.order)
            annotation = None

            if isinstance(order, AnnotatedOrder):
                annotation = order.annotation
                order = order.order

            if annotation is not None:
                queryset = queryset.annotate(**annotation)

            # If the field type does not have a specific ordering expression we can
            # order the default way.
            if not order:
                order = F(field_name)

                if view_sort.order == "ASC":
                    order = order.asc(nulls_first=True)
                else:
                    order = order.desc(nulls_last=True)

            order_by.append(order)

        order_by.append("order")
        order_by.append("id")
        queryset = queryset.order_by(*order_by)

        return queryset

    def get_sort(self, user, view_sort_id, base_queryset=None):
        """
        Returns an existing view sort with the given id.

        :param user: The user on whose behalf the view sort is requested.
        :type user: User
        :param view_sort_id: The id of the view sort.
        :type view_sort_id: int
        :param base_queryset: The base queryset from where to select the view sort
            object from. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises ViewSortDoesNotExist: The the requested view does not exists.
        :return: The requested view sort instance.
        :type: ViewSort
        """

        if base_queryset is None:
            base_queryset = ViewSort.objects

        try:
            view_sort = base_queryset.select_related(
                "view__table__database__group"
            ).get(pk=view_sort_id)
        except ViewSort.DoesNotExist:
            raise ViewSortDoesNotExist(
                f"The view sort with id {view_sort_id} does not exist."
            )

        if TrashHandler.item_has_a_trashed_parent(
            view_sort.view.table, check_item_also=True
        ):
            raise ViewSortDoesNotExist(
                f"The view sort with id {view_sort_id} does not exist."
            )

        group = view_sort.view.table.database.group
        group.has_user(user, raise_error=True)

        return view_sort

    def create_sort(self, user, view, field, order):
        """
        Creates a new view sort.

        :param user: The user on whose behalf the view sort is created.
        :type user: User
        :param view: The view for which the sort needs to be created.
        :type: View
        :param field: The field that needs to be sorted.
        :type field: Field
        :param order: The desired order, can either be ascending (A to Z) or
            descending (Z to A).
        :type order: str
        :raises ViewSortNotSupported: When the provided view does not support sorting.
        :raises FieldNotInTable:  When the provided field does not belong to the
            provided view's table.
        :return: The created view sort instance.
        :rtype: ViewSort
        """

        group = view.table.database.group
        group.has_user(user, raise_error=True)

        # Check if view supports sorting.
        view_type = view_type_registry.get_by_model(view.specific_class)
        if not view_type.can_sort:
            raise ViewSortNotSupported(
                f"Sorting is not supported for {view_type.type} views."
            )

        # Check if the field supports sorting.
        field_type = field_type_registry.get_by_model(field.specific_class)
        if not field_type.check_can_order_by(field):
            raise ViewSortFieldNotSupported(
                f"The field {field.pk} does not support sorting."
            )

        # Check if field belongs to the grid views table
        if not view.table.field_set.filter(id=field.pk).exists():
            raise FieldNotInTable(
                f"The field {field.pk} does not belong to table {view.table.id}."
            )

        # Check if the field already exists as sort
        if view.viewsort_set.filter(field_id=field.pk).exists():
            raise ViewSortFieldAlreadyExist(
                f"A sort with the field {field.pk} already exists."
            )

        view_sort = ViewSort.objects.create(view=view, field=field, order=order)

        view_sort_created.send(self, view_sort=view_sort, user=user)

        return view_sort

    def update_sort(self, user, view_sort, **kwargs):
        """
        Updates the values of an existing view sort.

        :param user: The user on whose behalf the view sort is updated.
        :type user: User
        :param view_sort: The view sort that needs to be updated.
        :type view_sort: ViewSort
        :param kwargs: The values that need to be updated, allowed values are
            `field` and `order`.
        :type kwargs: dict
        :raises FieldNotInTable: When the field does not support sorting.
        :return: The updated view sort instance.
        :rtype: ViewSort
        """

        group = view_sort.view.table.database.group
        group.has_user(user, raise_error=True)

        field = kwargs.get("field", view_sort.field)
        order = kwargs.get("order", view_sort.order)

        # If the field has changed we need to check if the field belongs to the table.
        if (
            field.id != view_sort.field_id
            and not view_sort.view.table.field_set.filter(id=field.pk).exists()
        ):
            raise FieldNotInTable(
                f"The field {field.pk} does not belong to table "
                f"{view_sort.view.table.id}."
            )

        # If the field has changed we need to check if the new field type supports
        # sorting.
        field_type = field_type_registry.get_by_model(field.specific_class)
        if field.id != view_sort.field_id and not field_type.check_can_order_by(field):
            raise ViewSortFieldNotSupported(
                f"The field {field.pk} does not support sorting."
            )

        # If the field has changed we need to check if the new field doesn't already
        # exist as sort.
        if (
            field.id != view_sort.field_id
            and view_sort.view.viewsort_set.filter(field_id=field.pk).exists()
        ):
            raise ViewSortFieldAlreadyExist(
                f"A sort with the field {field.pk} already exists."
            )

        view_sort.field = field
        view_sort.order = order
        view_sort.save()

        view_sort_updated.send(self, view_sort=view_sort, user=user)

        return view_sort

    def delete_sort(self, user, view_sort):
        """
        Deletes an existing view sort.

        :param user: The user on whose behalf the view sort is deleted.
        :type user: User
        :param view_sort: The view sort instance that needs to be deleted.
        :type view_sort: ViewSort
        """

        group = view_sort.view.table.database.group
        group.has_user(user, raise_error=True)

        view_sort_id = view_sort.id
        view_sort.delete()

        view_sort_deleted.send(
            self, view_sort_id=view_sort_id, view_sort=view_sort, user=user
        )

    def get_queryset(
        self,
        view,
        search=None,
        model=None,
        only_sort_by_field_ids=None,
        only_search_by_field_ids=None,
    ):
        """
        Returns a queryset for the provided view which is appropriately sorted,
        filtered and searched according to the view type and its settings.

        :param search: A search term to apply to the resulting queryset.
        :param model: The model for this views table to generate the queryset from, if
            not specified then the model will be generated automatically.
        :param view: The view to get the export queryset and fields for.
        :type view: View
        :param only_sort_by_field_ids: To only sort the queryset by some fields
            provide those field ids in this optional iterable. Other fields not
            present in the iterable will not have their view sorts applied even if they
            have one.
        :type only_sort_by_field_ids: Optional[Iterable[int]]
        :param only_search_by_field_ids: To only apply the search term to some
            fields provide those field ids in this optional iterable. Other fields
             not present in the iterable will not be searched and filtered down by the
             search term.
        :type only_search_by_field_ids: Optional[Iterable[int]]
        :return: The appropriate queryset for the provided view.
        :rtype: QuerySet
        """

        if model is None:
            model = view.table.get_model()

        queryset = model.objects.all().enhance_by_fields()

        view_type = view_type_registry.get_by_model(view.specific_class)
        if view_type.can_filter:
            queryset = self.apply_filters(view, queryset)
        if view_type.can_sort:
            queryset = self.apply_sorting(view, queryset, only_sort_by_field_ids)
        if search is not None:
            queryset = queryset.search_all_fields(search, only_search_by_field_ids)
        return queryset

    def get_field_aggregations(
        self,
        view: View,
        aggregations: Iterable[Tuple[django_models.Field, str]],
        model: Table = None,
        with_total: bool = False,
    ) -> Dict[str, Any]:
        """
        Returns a dict of aggregation for given (field, aggregation_type) couple.
        Each dict key is the name of the field suffixed with two `_` then the
        aggregation type. ex: "field_42__empty_count" for the empty count
        aggregation of field with id 42.

        :param view: The view to get the field aggregation for.
        :param aggregations: A list of (field_instance, aggregation_type).
        :param model: The model for this view table to generate the aggregation
            query from, if not specified then the model will be generated
            automatically.
        :param with_total: Whether the total row count should be returned in the
             result.
        :raises FieldAggregationNotSupported: When the view type doesn't support
            field aggregation.
        :raises FieldNotInTable: When the field does not belong to the specified
            view.
        :returns: A dict of aggregation value
        """

        if model is None:
            model = view.table.get_model()

        queryset = model.objects.all().enhance_by_fields()

        view_type = view_type_registry.get_by_model(view.specific_class)

        # Check if view supports field aggregation
        if not view_type.can_aggregate_field:
            raise FieldAggregationNotSupported(
                f"Field aggregation is not supported for {view_type.type} views."
            )

        # Apply filters to have accurate aggregation
        if view_type.can_filter:
            queryset = self.apply_filters(view, queryset)

        aggregation_dict = {}
        for (field_instance, aggregation_type_name) in aggregations:

            # Check whether the field belongs to the table.
            if field_instance.table_id != view.table_id:
                raise FieldNotInTable(
                    f"The field {field_instance.pk} does not belong to table "
                    f"{view.table.id}."
                )

            # Prepare data for .get_aggregation call
            field = model._field_objects[field_instance.id]["field"]
            field_name = field_instance.db_column
            model_field = model._meta.get_field(field_name)
            aggregation_type = view_aggregation_type_registry.get(aggregation_type_name)

            # Add the aggregation for the field
            aggregation_dict[
                f"{field_name}__{aggregation_type_name}"
            ] = aggregation_type.get_aggregation(field_name, model_field, field)

        if with_total:
            # Add total to allow further calculation on the client
            aggregation_dict["total"] = Count("id")

        queryset = queryset.aggregate(**aggregation_dict)

        return queryset

    def rotate_view_slug(self, user, view):
        """
        Rotates the slug of the provided view.

        :param user: The user on whose behalf the view is updated.
        :type user: User
        :param view: The form view instance that needs to be updated.
        :type view: View
        :return: The updated view instance.
        :rtype: View
        :raises CannotShareViewTypeError: Raised if called for a view which does not
            support sharing.
        """

        view_type = view_type_registry.get_by_model(view.specific_class)
        if not view_type.can_share:
            raise CannotShareViewTypeError()

        group = view.table.database.group
        group.has_user(user, raise_error=True)

        view.rotate_slug()
        view.save()

        view_updated.send(self, view=view, user=user)

        return view

    def get_public_view_by_slug(self, user, slug, view_model=None):
        """
        Returns the view with the provided slug if it is public or if the user has
        access to the views group.

        :param user: The user on whose behalf the view is requested.
        :type user: User
        :param slug: The slug of the view.
        :type slug: str
        :param view_model: If provided that models objects are used to select the
            view. This can for example be useful when you want to select a GridView or
            other child of the View model.
        :type view_model: Type[View]
        :return: The requested view with matching slug.
        :rtype: View
        """

        if not view_model:
            view_model = View

        try:
            view = view_model.objects.select_related("table__database__group").get(
                slug=slug
            )
        except (view_model.DoesNotExist, ValidationError):
            raise ViewDoesNotExist("The view does not exist.")

        if TrashHandler.item_has_a_trashed_parent(view.table, check_item_also=True):
            raise ViewDoesNotExist("The view does not exist.")

        if not view.public and (
            not user or not view.table.database.group.has_user(user)
        ):
            raise ViewDoesNotExist("The view does not exist.")

        return view

    def submit_form_view(self, form, values, model=None, enabled_field_options=None):
        """
        Handles when a form is submitted. It will validate the data by checking if
        the required fields are provided and not empty and it will create a new row
        based on those values.

        :param form: The form view that is submitted.
        :type form: FormView
        :param values: The submitted values that need to be used when creating the row.
        :type values: dict
        :param model: If the model is already generated, it can be provided here.
        :type model: Model | None
        :param enabled_field_options: If the enabled field options have already been
            fetched, they can be provided here.
        :type enabled_field_options: QuerySet | list | None
        :return: The newly created row.
        :rtype: Model
        """

        table = form.table

        if not model:
            model = table.get_model()

        if not enabled_field_options:
            enabled_field_options = form.active_field_options

        allowed_field_names = []
        field_errors = {}

        # Loop over all field options, find the name in the model and check if the
        # required values are provided. If not, a validation error is raised.
        for field in enabled_field_options:
            field_name = model._field_objects[field.field_id]["name"]
            allowed_field_names.append(field_name)

            if field.required and (
                field_name not in values or values[field_name] in EMPTY_VALUES
            ):
                field_errors[field_name] = ["This field is required."]

        if len(field_errors) > 0:
            raise ValidationError(field_errors)

        allowed_values = extract_allowed(values, allowed_field_names)
        instance = RowHandler().force_create_row(table, allowed_values, model)

        row_created.send(
            self, row=instance, before=None, user=None, table=table, model=model
        )

        return instance

    def get_public_views_row_checker(
        self,
        table,
        model,
        only_include_views_which_want_realtime_events,
        updated_field_ids=None,
    ):
        """
        Returns a CachingPublicViewRowChecker object which will have precalculated
        information about the public views in the provided table to aid with quickly
        checking which views a row in that table is visible in. If you will be updating
        the row and reusing the checker you must provide an iterable of the field ids
        that you will be updating in the row, otherwise the checker will cache the
        first check per view/row.

        :param table: The table the row is in.
        :param model: The model of the table including all fields.
        :param only_include_views_which_want_realtime_events: If True will only look
            for public views where
            ViewType.when_shared_publicly_requires_realtime_events is True.
        :param updated_field_ids: An optional iterable of field ids which will be
            updated on rows passed to the checker. If the checker is used on the same
            row multiple times and that row has been updated it will return invalid
            results unless you have correctly populated this argument.
        :return: A list of non-specific public view instances.
        """

        return CachingPublicViewRowChecker(
            table,
            model,
            only_include_views_which_want_realtime_events,
            updated_field_ids,
        )

    def restrict_row_for_view(
        self, view: View, serialized_row: Dict[str, Any]
    ) -> Dict[Any, Any]:
        """
        Removes any fields which are hidden in the view from the provided serialized
        row ensuring no data is leaked according to the views field options.

        :param view: The view to restrict the row by.
        :param serialized_row: A python dictionary which is the result of serializing
            the row containing `field_XXX` keys per field value. It must not be a
            serialized using user_field_names=True.
        :return: A copy of the serialized_row with all hidden fields removed.
        """
        return self.restrict_rows_for_view(view, [serialized_row])[0]

    def restrict_rows_for_view(
        self, view: View, serialized_rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Removes any fields which are hidden in the view from the provided serialized
        row ensuring no data is leaked according to the views field options.

        :param view: The view to restrict the row by.
        :param serialized_rows: A list of python dictionaries which are the result of
            serializing the rows containing `field_XXX` keys per field value. They
            must not be serialized using user_field_names=True.
        :return: A copy of the serialized_row with all hidden fields removed.
        """

        view_type = view_type_registry.get_by_model(view.specific_class)
        hidden_field_options = view_type.get_hidden_field_options(view)
        restricted_rows = []
        for serialized_row in serialized_rows:
            row_copy = deepcopy(serialized_row)
            for hidden_field_option in hidden_field_options:
                row_copy.pop(f"field_{hidden_field_option.field_id}", None)
            restricted_rows.append(row_copy)
        return restricted_rows


class CachingPublicViewRowChecker:
    """
    A helper class to check which public views a row is visible in. Will pre-calculate
    upfront for a specific table which public views are always visible, which public
    views can have row check results cached for and finally will pre-construct and
    reuse querysets for performance reasons.
    """

    def __init__(
        self,
        table: Table,
        model: GeneratedTableModel,
        only_include_views_which_want_realtime_events: bool,
        updated_field_ids: Optional[Iterable[int]] = None,
    ):
        self._public_views = (
            table.view_set.filter(public=True).prefetch_related("viewfilter_set").all()
        )
        self._updated_field_ids = updated_field_ids
        self._views_with_filters = []
        self._always_visible_views = []
        self._view_row_check_cache = defaultdict(dict)
        handler = ViewHandler()
        for view in self._public_views:
            if only_include_views_which_want_realtime_events:
                view_type = view_type_registry.get_by_model(view.specific_class)
                if not view_type.when_shared_publicly_requires_realtime_events:
                    continue

            if len(view.viewfilter_set.all()) == 0:
                # If there are no view filters for this view then any row must always
                # be visible in this view
                self._always_visible_views.append(view)
            else:
                filter_qs = handler.apply_filters(view, model.objects)
                self._views_with_filters.append(
                    (
                        view,
                        filter_qs,
                        self._view_row_checks_can_be_cached(view),
                    )
                )

    def get_public_views_where_row_is_visible(self, row):
        """
        WARNING: If you are reusing the same checker and calling this method with the
        same row multiple times you must have correctly set which fields in the row
        might be updated in the checkers initials `updated_field_ids` attribute. This
        is because for a given view, if we know none of the fields it filters on
        will be updated we can cache the first check of if that row exists as any
        further changes to the row wont be affecting filtered fields. Hence
        `updated_field_ids` needs to be set if you are ever changing the row and
        reusing the same CachingPublicViewRowChecker instance.

        :param row: A row in the checkers table.
        :return: A list of views where the row is visible for this checkers table.
        """
        views = []
        for view, filter_qs, can_use_cache in self._views_with_filters:
            if can_use_cache:
                if row.id not in self._view_row_check_cache[view.id]:
                    self._view_row_check_cache[view.id][
                        row.id
                    ] = self._check_row_visible(filter_qs, row)
                if self._view_row_check_cache[view.id][row.id]:
                    views.append(view)
            elif self._check_row_visible(filter_qs, row):
                views.append(view)

        return views + self._always_visible_views

    # noinspection PyMethodMayBeStatic
    def _check_row_visible(self, filter_qs, row):
        return filter_qs.filter(id=row.id).exists()

    def _view_row_checks_can_be_cached(self, view):
        if self._updated_field_ids is None:
            return True
        for view_filter in view.viewfilter_set.all():
            if view_filter.field_id in self._updated_field_ids:
                # We found a view filter for a field which will be updated hence we
                # need to check both before and after a row update occurs
                return False
        # Every single updated field does not have a filter on it, hence
        # we only need to check if a given row is visible in the view once
        # as any changes to the fields in said row wont be for fields with
        # filters and so the result of the first check will be still
        # valid for any subsequent checks.
        return True
