from django.db.models import Q

from baserow.core.exceptions import UserNotInGroupError
from baserow.core.utils import extract_allowed, set_allowed_attrs
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.exceptions import FieldNotInTable

from .exceptions import (
    ViewDoesNotExist, UnrelatedFieldError, ViewFilterDoesNotExist,
    ViewFilterNotSupported, ViewFilterTypeNotAllowedForField
)
from .registries import view_type_registry, view_filter_type_registry
from .models import (
    View, GridViewFieldOptions, ViewFilter, FILTER_TYPE_AND, FILTER_TYPE_OR
)


class ViewHandler:
    def get_view(self, user, view_id, view_model=None, base_queryset=None):
        """
        Selects a view and checks if the user has access to that view. If everything
        is fine the view is returned.

        :param user: The user on whose behalf the view is requested.
        :type user: User
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
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :type view_model: View
        :return:
        """

        if not view_model:
            view_model = View

        if not base_queryset:
            base_queryset = view_model.objects

        try:
            view = base_queryset.select_related('table__database__group').get(
                pk=view_id
            )
        except View.DoesNotExist:
            raise ViewDoesNotExist(f'The view with id {view_id} does not exist.')

        group = view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

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
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :return: The created view instance.
        :rtype: View
        """

        group = table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # Figure out which model to use for the given view type.
        view_type = view_type_registry.get(type_name)
        model_class = view_type.model_class
        allowed_fields = ['name', 'filter_type'] + view_type.allowed_fields
        view_values = extract_allowed(kwargs, allowed_fields)
        last_order = model_class.get_last_order(table)

        instance = model_class.objects.create(table=table, order=last_order,
                                              **view_values)

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
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :return: The updated view instance.
        :rtype: View
        """

        if not isinstance(view, View):
            raise ValueError('The view is not an instance of View.')

        group = view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        view_type = view_type_registry.get_by_model(view)
        allowed_fields = ['name', 'filter_type'] + view_type.allowed_fields
        view = set_allowed_attrs(kwargs, allowed_fields, view)
        view.save()

        return view

    def delete_view(self, user, view):
        """
        Deletes an existing view instance.

        :param user: The user on whose behalf the view is deleted.
        :type user: User
        :param view: The view instance that needs to be deleted.
        :type view: View
        :raises ViewDoesNotExist: When the view with the provided id does not exist.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        """

        if not isinstance(view, View):
            raise ValueError('The view is not an instance of View')

        group = view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        view.delete()

    def update_grid_view_field_options(self, grid_view, field_options, fields=None):
        """
        Updates the field options with the provided values if the field id exists in
        the table related to the grid view.

        :param grid_view: The grid view for which the field options need to be updated.
        :type grid_view: Model
        :param field_options: A dict with the field ids as the key and a dict
            containing the values that need to be updated as value.
        :type field_options: dict
        :param fields: Optionally a list of fields can be provided so that they don't
            have to be fetched again.
        :type fields: None or list
        :raises UnrelatedFieldError: When the provided field id is not related to the
            provided view.
        """

        if not fields:
            fields = Field.objects.filter(table=grid_view.table)

        allowed_field_ids = [field.id for field in fields]
        for field_id, options in field_options.items():
            if int(field_id) not in allowed_field_ids:
                raise UnrelatedFieldError(f'The field id {field_id} is not related to '
                                          f'the grid view.')
            GridViewFieldOptions.objects.update_or_create(
                grid_view=grid_view, field_id=field_id, defaults=options
            )

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
        if not hasattr(model, '_field_objects'):
            raise ValueError('A queryset of the a table model is required.')

        q_filters = Q()

        for view_filter in view.viewfilter_set.all():
            # If the to be filtered field is not present in the `_field_objects` we
            # cannot filter so we raise a ValueError.
            if view_filter.field_id not in model._field_objects:
                raise ValueError(f'The table model does not contain field '
                                 f'{view_filter.field_id}.')

            field_name = model._field_objects[view_filter.field_id]['name']
            model_field = model._meta.get_field(field_name)
            view_filter_type = view_filter_type_registry.get(view_filter.type)
            q_filter = view_filter_type.get_filter(
                field_name,
                view_filter.value,
                model_field
            )

            # Depending on filter type we are going to combine the Q either as AND or
            # as OR.
            if view.filter_type == FILTER_TYPE_AND:
                q_filters &= q_filter
            elif view.filter_type == FILTER_TYPE_OR:
                q_filters |= q_filter

        queryset = queryset.filter(q_filters)

        return queryset

    def get_filter(self, user, view_filter_id):
        """
        Returns an existing view filter by the given id.

        :param user: The user on whose behalf the view filter is requested.
        :type user: User
        :param view_filter_id: The id of the view filter.
        :type view_filter_id: int
        :raises ViewFilterDoesNotExist: The the requested view does not exists.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :return: The requested view filter instance.
        :type: ViewFilter
        """

        try:
            view_filter = ViewFilter.objects.select_related(
                'view__table__database__group'
            ).get(
                pk=view_filter_id
            )
        except ViewFilter.DoesNotExist:
            raise ViewFilterDoesNotExist(
                f'The view filter with id {view_filter_id} does not exist.'
            )

        group = view_filter.view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

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
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :raises ViewFilterNotSupported: When the provided view does not support filters.
        :raises ViewFilterTypeNotAllowedForField: When the field does not support the
            filter type.
        :raises FieldNotInTable:  When the provided field does not belong to the
            provided view's table.
        :return: The created view filter instance.
        :rtype: ViewFilter
        """

        group = view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # Check if view supports filtering
        view_type = view_type_registry.get_by_model(view.specific_class)
        if not view_type.can_filter:
            raise ViewFilterNotSupported(
                f'Filtering is not supported for {view_type.type} views.'
            )

        view_filter_type = view_filter_type_registry.get(type_name)
        field_type = field_type_registry.get_by_model(field.specific_class)

        # Check if the field is allowed for this filter type.
        if field_type.type not in view_filter_type.compatible_field_types:
            raise ViewFilterTypeNotAllowedForField(
                f'The view filter type {type_name} is not supported for field type '
                f'{field_type.type}.'
            )

        # Check if field belongs to the grid views table
        if not view.table.field_set.filter(id=field.pk).exists():
            raise FieldNotInTable(f'The field {field.pk} does not belong to table '
                                  f'{view.table.id}.')

        return ViewFilter.objects.create(
            view=view,
            field=field,
            type=view_filter_type.type,
            value=value
        )

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
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :raises ViewFilterTypeNotAllowedForField: When the field does not supports the
            filter type.
        :raises FieldNotInTable: When the does not support the filter type.
        :return: The updated view filter instance.
        :rtype: ViewFilter
        """

        group = view_filter.view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        type_name = kwargs.get('type_name', view_filter.type)
        field = kwargs.get('field', view_filter.field)
        value = kwargs.get('value', view_filter.value)
        view_filter_type = view_filter_type_registry.get(type_name)
        field_type = field_type_registry.get_by_model(field.specific_class)

        # Check if the field is allowed for this filter type.
        if field_type.type not in view_filter_type.compatible_field_types:
            raise ViewFilterTypeNotAllowedForField(
                f'The view filter type {type_name} is not supported for field type '
                f'{field_type.type}.'
            )

        # If the field has changed we need to check if the field belongs to the table.
        if (
            field.id != view_filter.field_id and
            not view_filter.view.table.field_set.filter(id=field.pk).exists()
        ):
            raise FieldNotInTable(f'The field {field.pk} does not belong to table '
                                  f'{view_filter.view.table.id}.')

        view_filter.field = field
        view_filter.value = value
        view_filter.type = type_name
        view_filter.save()

        return view_filter

    def delete_filter(self, user, view_filter):
        """
        Deletes an existing view filter.

        :param user: The user on whose behalf the view filter is deleted.
        :type user: User
        :param view_filter: The view filter instance that needs to be deleted.
        :type view_filter: ViewFilter
        :raises UserNotInGroupError: When the user does not belong to the related group.
        """

        group = view_filter.view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        view_filter.delete()
