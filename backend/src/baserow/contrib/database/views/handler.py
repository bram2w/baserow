from baserow.core.exceptions import UserNotInGroupError
from baserow.core.utils import extract_allowed, set_allowed_attrs

from .registries import view_type_registry
from .models import View


class ViewHandler:
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
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # Figure out which model to use for the given view type.
        view_type = view_type_registry.get(type_name)
        model_class = view_type.model_class
        allowed_fields = ['name'] + view_type.allowed_fields
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
        :return: The updated view instance.
        :rtype: View
        """

        if not isinstance(view, View):
            raise ValueError('The view is not an instance of View.')

        group = view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        view_type = view_type_registry.get_by_model(view)
        allowed_fields = ['name'] + view_type.allowed_fields
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
        """

        if not isinstance(view, View):
            raise ValueError('The view is not an instance of View')

        group = view.table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        view.delete()
