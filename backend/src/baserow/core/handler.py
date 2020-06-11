from .models import Group, GroupUser, Application
from .exceptions import UserNotInGroupError
from .utils import extract_allowed, set_allowed_attrs
from .registries import application_type_registry


class CoreHandler:
    def create_group(self, user, **kwargs):
        """
        Creates a new group for an existing user.

        :param user: The user that must be in the group.
        :type user: User
        :return: The newly created GroupUser object
        :rtype: GroupUser
        """

        group_values = extract_allowed(kwargs, ['name'])
        group = Group.objects.create(**group_values)
        last_order = GroupUser.get_last_order(user)
        group_user = GroupUser.objects.create(group=group, user=user, order=last_order)

        return group_user

    def update_group(self, user, group, **kwargs):
        """
        Updates the values of a group.

        :param user: The user on whose behalf the change is made.
        :type user: User
        :param group: The group instance that must be updated.
        :type group: Group
        :return: The updated group
        :rtype: Group
        """

        if not isinstance(group, Group):
            raise ValueError('The group is not an instance of Group.')

        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        group = set_allowed_attrs(kwargs, ['name'], group)
        group.save()

        return group

    def delete_group(self, user, group):
        """
        Deletes an existing group and related application the proper way.

        :param user: The user on whose behalf the delete is done.
        :type: user: User
        :param group: The group instance that must be deleted.
        :type: group: Group
        """

        if not isinstance(group, Group):
            raise ValueError('The group is not an instance of Group.')

        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # Select all the applications so we can delete them via the handler which is
        # needed in order to call the pre_delete method for each application.
        applications = group.application_set.all().select_related('group')
        for application in applications:
            self.delete_application(user, application)

        group.delete()

    def order_groups(self, user, group_ids):
        """
        Changes the order of groups for a user.

        :param user: The user on whose behalf the ordering is done.
        :type: user: User
        :param group_ids: A list of group ids ordered the way they need to be ordered.
        :type group_ids: List[int]
        """

        for index, group_id in enumerate(group_ids):
            GroupUser.objects.filter(
                user=user,
                group_id=group_id
            ).update(order=index + 1)

    def create_application(self, user, group, type_name, **kwargs):
        """
        Creates a new application based on the provided type.

        :param user: The user on whose behalf the application is created.
        :type user: User
        :param group: The group that the application instance belongs to.
        :type group: Group
        :param type_name: The type name of the application. ApplicationType can be
            registered via the ApplicationTypeRegistry.
        :type type_name: str
        :param kwargs: The fields that need to be set upon creation.
        :type kwargs: object
        :return: The created application instance.
        :rtype: Application
        """

        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # Figure out which model is used for the given application type.
        application_type = application_type_registry.get(type_name)
        model = application_type.model_class
        application_values = extract_allowed(kwargs, ['name'])
        last_order = model.get_last_order(group)

        instance = model.objects.create(group=group, order=last_order,
                                        **application_values)

        return instance

    def update_application(self, user, application, **kwargs):
        """
        Updates an existing application instance.

        :param user: The user on whose behalf the application is updated.
        :type user: User
        :param application: The application instance that needs to be updated.
        :type application: Application
        :param kwargs: The fields that need to be updated.
        :type kwargs: object
        :return: The updated application instance.
        :rtype: Application
        """

        if not isinstance(application, Application):
            raise ValueError('The application is not an instance of Application.')

        if not application.group.has_user(user):
            raise UserNotInGroupError(user, application.group)

        application = set_allowed_attrs(kwargs, ['name'], application)
        application.save()

        return application

    def delete_application(self, user, application):
        """
        Deletes an existing application instance.

        :param user: The user on whose behalf the application is deleted.
        :type user: User
        :param application: The application instance that needs to be deleted.
        :type application: Application
        """

        if not isinstance(application, Application):
            raise ValueError('The application is not an instance of Application')

        if not application.group.has_user(user):
            raise UserNotInGroupError(user, application.group)

        application = application.specific
        application_type = application_type_registry.get_by_model(application)
        application_type.pre_delete(user, application)

        application.delete()
