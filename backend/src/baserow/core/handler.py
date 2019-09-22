from .models import Group, GroupUser, Application
from .exceptions import UserNotIngroupError
from .utils import extract_allowed, set_allowed_attrs
from .applications import registry


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
            raise UserNotIngroupError(f'The user {user} does not belong to the group '
                                      f'{group}.')

        group = set_allowed_attrs(kwargs, ['name'], group)
        group.save()

        return group

    def delete_group(self, user, group):
        """
        Deletes an existing group.

        :param user: The user on whose behalf the delete is done.
        :type: user: User
        :param group: The group instance that must be deleted.
        :type: group: Group
        """

        if not isinstance(group, Group):
            raise ValueError('The group is not an instance of Group.')

        if not group.has_user(user):
            raise UserNotIngroupError(f'The user {user} does not belong to the group '
                                      f'{group}.')

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

    def create_application(self, user, group, type, **kwargs):
        """
        Creates a new application based on the provided type.

        :param user: The user on whose behalf the application is created.
        :type user: User
        :param group: The group that the application instance belongs to.
        :type group: Group
        :param type: The type name of the application. Application can be registered via
                     the ApplicationRegistry.
        :type type: str
        :param kwargs: The fields that need to be set upon creation.
        :type kwargs: object
        :return: The created application instance.
        :rtype: Application
        """

        if not group.has_user(user):
            raise UserNotIngroupError(f'The user {user} does not belong to the group '
                                      f'{group}.')

        # Figure out which model is used for the given application type.
        application = registry.get(type)
        model = application.instance_model
        application_values = extract_allowed(kwargs, ['name'])

        if 'order' not in application_values:
            application_values['order'] = model.get_last_order(group)

        instance = model.objects.create(group=group, **application_values)

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
            raise ValueError('The application is not an instance of Application')

        if not application.group.has_user(user):
            raise UserNotIngroupError(f'The user {user} does not belong to the group '
                                      f'{application.group}.')

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
            raise UserNotIngroupError(f'The user {user} does not belong to the group '
                                      f'{application.group}.')

        application.delete()
