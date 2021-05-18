from django.db.models import F

from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.core.utils import extract_allowed, set_allowed_attrs
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
)
from .models import View, GridViewFieldOptions, ViewFilter, ViewSort
from .registries import view_type_registry, view_filter_type_registry
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
    grid_view_field_options_updated,
)
from baserow.contrib.database.fields.field_filters import FilterBuilder


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
        :type view_model: View
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

        if not base_queryset:
            base_queryset = view_model.objects

        try:
            view = base_queryset.select_related("table__database__group").get(
                pk=view_id
            )
        except View.DoesNotExist:
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
        allowed_fields = [
            "name",
            "filter_type",
            "filters_disabled",
        ] + view_type.allowed_fields
        view_values = extract_allowed(kwargs, allowed_fields)
        last_order = model_class.get_last_order(table)

        instance = model_class.objects.create(
            table=table, order=last_order, **view_values
        )

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
        allowed_fields = [
            "name",
            "filter_type",
            "filters_disabled",
        ] + view_type.allowed_fields
        view = set_allowed_attrs(kwargs, allowed_fields, view)
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

    def update_grid_view_field_options(
        self, user, grid_view, field_options, fields=None
    ):
        """
        Updates the field options with the provided values if the field id exists in
        the table related to the grid view.

        :param user: The user on whose behalf the request is made.
        :type user: User
        :param grid_view: The grid view for which the field options need to be updated.
        :type grid_view: GridView
        :param field_options: A dict with the field ids as the key and a dict
            containing the values that need to be updated as value.
        :type field_options: dict
        :param fields: Optionally a list of fields can be provided so that they don't
            have to be fetched again.
        :type fields: None or list
        :raises UnrelatedFieldError: When the provided field id is not related to the
            provided view.
        """

        grid_view.table.database.group.has_user(user, raise_error=True)

        if not fields:
            fields = Field.objects.filter(table=grid_view.table)

        allowed_field_ids = [field.id for field in fields]
        for field_id, options in field_options.items():
            if int(field_id) not in allowed_field_ids:
                raise UnrelatedFieldError(
                    f"The field id {field_id} is not related to " f"the grid view."
                )
            GridViewFieldOptions.objects.update_or_create(
                grid_view=grid_view, field_id=field_id, defaults=options
            )

        grid_view_field_options_updated.send(self, grid_view=grid_view, user=user)

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
        if not field_type.can_order_by:
            field.viewsort_set.all().delete()

        # Check which filters are not compatible anymore and remove those.
        for filter in field.viewfilter_set.all():
            filter_type = view_filter_type_registry.get(filter.type)

            if field_type.type not in filter_type.compatible_field_types:
                filter.delete()

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

        # If the model does not have the `_field_objects` property then it is not a
        # generated table model which is not supported.
        if not hasattr(model, "_field_objects"):
            raise ValueError("A queryset of the table model is required.")

        # If the filter are disabled we don't have to do anything with the queryset.
        if view.filters_disabled:
            return queryset

        filter_builder = FilterBuilder(filter_type=view.filter_type)

        for view_filter in view.viewfilter_set.all():
            # If the to be filtered field is not present in the `_field_objects` we
            # cannot filter so we raise a ValueError.
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

        if not base_queryset:
            base_queryset = ViewFilter.objects

        try:
            view_filter = base_queryset.select_related(
                "view__table__database__group"
            ).get(pk=view_filter_id)
        except ViewFilter.DoesNotExist:
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
        if field_type.type not in view_filter_type.compatible_field_types:
            raise ViewFilterTypeNotAllowedForField(type_name, field_type.type)

        # Check if field belongs to the grid views table
        if not view.table.field_set.filter(id=field.pk).exists():
            raise FieldNotInTable(
                f"The field {field.pk} does not belong to table " f"{view.table.id}."
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
        if field_type.type not in view_filter_type.compatible_field_types:
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

    def apply_sorting(self, view, queryset):
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
        :return: The queryset where the sorting has been applied to.
        :type: QuerySet
        """

        model = queryset.model

        # If the model does not have the `_field_objects` property then it is not a
        # generated table model which is not supported.
        if not hasattr(model, "_field_objects"):
            raise ValueError("A queryset of the table model is required.")

        order_by = []

        for view_sort in view.viewsort_set.all():
            # If the to be sort field is not present in the `_field_objects` we
            # cannot filter so we raise a ValueError.
            if view_sort.field_id not in model._field_objects:
                raise ValueError(
                    f"The table model does not contain field " f"{view_sort.field_id}."
                )

            field = model._field_objects[view_sort.field_id]["field"]
            field_name = model._field_objects[view_sort.field_id]["name"]
            field_type = model._field_objects[view_sort.field_id]["type"]

            order = field_type.get_order(field, field_name, view_sort)

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

        if not base_queryset:
            base_queryset = ViewSort.objects

        try:
            view_sort = base_queryset.select_related(
                "view__table__database__group"
            ).get(pk=view_sort_id)
        except ViewSort.DoesNotExist:
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
        if not field_type.can_order_by:
            raise ViewSortFieldNotSupported(
                f"The field {field.pk} does not support " f"sorting."
            )

        # Check if field belongs to the grid views table
        if not view.table.field_set.filter(id=field.pk).exists():
            raise FieldNotInTable(
                f"The field {field.pk} does not belong to table " f"{view.table.id}."
            )

        # Check if the field already exists as sort
        if view.viewsort_set.filter(field_id=field.pk).exists():
            raise ViewSortFieldAlreadyExist(
                f"A sort with the field {field.pk} " f"already exists."
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
        if field.id != view_sort.field_id and not field_type.can_order_by:
            raise ViewSortFieldNotSupported(
                f"The field {field.pk} does not support " f"sorting."
            )

        # If the field has changed we need to check if the new field doesn't already
        # exist as sort.
        if (
            field.id != view_sort.field_id
            and view_sort.view.viewsort_set.filter(field_id=field.pk).exists()
        ):
            raise ViewSortFieldAlreadyExist(
                f"A sort with the field {field.pk} " f"already exists."
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
