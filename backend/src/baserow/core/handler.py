from .models import Group, GroupUser, Application
from .exceptions import UserNotInGroupError
from .utils import extract_allowed, set_allowed_attrs
from .registries import application_type_registry
from .exceptions import GroupDoesNotExist, ApplicationDoesNotExist
from .signals import (
    application_created, application_updated, application_deleted, group_created,
    group_updated, group_deleted
)


class CoreHandler:
    def get_group(self, user, group_id, base_queryset=None):
        """
        Selects a group with a given id from the database.

        :param user: The user on whose behalf the group is requested.
        :type user: User
        :param group_id: The identifier of the group that must be returned.
        :type group_id: int
        :param base_queryset: The base queryset from where to select the group
            object. This can for example be used to do a `prefetch_related`.
        :type base_queryset: Queryset
        :raises GroupDoesNotExist: When the group with the provided id does not exist.
        :raises UserNotInGroupError: When the user does not belong to the group.
        :return: The requested group instance of the provided id.
        :rtype: Group
        """

        if not base_queryset:
            base_queryset = Group.objects

        try:
            group = base_queryset.get(id=group_id)
        except Group.DoesNotExist:
            raise GroupDoesNotExist(f'The group with id {group_id} does not exist.')

        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        return group

    def get_group_user(self, user, group_id, base_queryset=None):
        """
        Selects a group user object for the given user and group_id from the database.

        :param user: The user on whose behalf the group is requested.
        :type user: User
        :param group_id: The identifier of the group that must be returned.
        :type group_id: int
        :param base_queryset: The base queryset from where to select the group user
            object. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises GroupDoesNotExist: When the group with the provided id does not exist.
        :raises UserNotInGroupError: When the user does not belong to the group.
        :return: The requested group user instance of the provided group_id.
        :rtype: GroupUser
        """

        if not base_queryset:
            base_queryset = GroupUser.objects

        try:
            group_user = base_queryset.select_related('group').get(
                user=user, group_id=group_id
            )
        except GroupUser.DoesNotExist:
            if Group.objects.filter(pk=group_id).exists():
                raise UserNotInGroupError(user)
            else:
                raise GroupDoesNotExist(f'The group with id {group_id} does not exist.')

        return group_user

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

        group_created.send(self, group=group, user=user)

        return group_user

    def update_group(self, user, group, **kwargs):
        """
        Updates the values of a group.

        :param user: The user on whose behalf the change is made.
        :type user: User
        :param group: The group instance that must be updated.
        :type group: Group
        :raises ValueError: If one of the provided parameters is invalid.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :return: The updated group
        :rtype: Group
        """

        if not isinstance(group, Group):
            raise ValueError('The group is not an instance of Group.')

        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        group = set_allowed_attrs(kwargs, ['name'], group)
        group.save()

        group_updated.send(self, group=group, user=user)

        return group

    def delete_group(self, user, group):
        """
        Deletes an existing group and related application the proper way.

        :param user: The user on whose behalf the delete is done.
        :type: user: User
        :param group: The group instance that must be deleted.
        :type: group: Group
        :raises ValueError: If one of the provided parameters is invalid.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        """

        if not isinstance(group, Group):
            raise ValueError('The group is not an instance of Group.')

        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        # Load the group users before the group is deleted so that we can pass those
        # along with the signal.
        group_id = group.id
        group_users = list(group.users.all())

        # Select all the applications so we can delete them via the handler which is
        # needed in order to call the pre_delete method for each application.
        applications = group.application_set.all().select_related('group')
        for application in applications:
            self.delete_application(user, application)

        group.delete()

        group_deleted.send(self, group_id=group_id, group=group,
                           group_users=group_users, user=user)

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

    def get_application(self, user, application_id, base_queryset=None):
        """
        Selects an application with a given id from the database.

        :param user: The user on whose behalf the application is requested.
        :type user: User
        :param application_id: The identifier of the application that must be returned.
        :type application_id: int
        :param base_queryset: The base queryset from where to select the application
            object. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises ApplicationDoesNotExist: When the application with the provided id
            does not exist.
        :raises UserNotInGroupError: When the user does not belong to the group.
        :return: The requested application instance of the provided id.
        :rtype: Application
        """

        if not base_queryset:
            base_queryset = Application.objects

        try:
            application = base_queryset.select_related(
                'group', 'content_type'
            ).get(id=application_id)
        except Application.DoesNotExist:
            raise ApplicationDoesNotExist(
                f'The application with id {application_id} does not exist.'
            )

        if not application.group.has_user(user):
            raise UserNotInGroupError(user, application.group)

        return application

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
        :raises UserNotInGroupError: When the user does not belong to the related group.
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

        application_created.send(self, application=instance, user=user,
                                 type_name=type_name)

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
        :raises ValueError: If one of the provided parameters is invalid.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        :return: The updated application instance.
        :rtype: Application
        """

        if not isinstance(application, Application):
            raise ValueError('The application is not an instance of Application.')

        if not application.group.has_user(user):
            raise UserNotInGroupError(user, application.group)

        application = set_allowed_attrs(kwargs, ['name'], application)
        application.save()

        application_updated.send(self, application=application, user=user)

        return application

    def delete_application(self, user, application):
        """
        Deletes an existing application instance.

        :param user: The user on whose behalf the application is deleted.
        :type user: User
        :param application: The application instance that needs to be deleted.
        :type application: Application
        :raises ValueError: If one of the provided parameters is invalid.
        :raises UserNotInGroupError: When the user does not belong to the related group.
        """

        if not isinstance(application, Application):
            raise ValueError('The application is not an instance of Application')

        if not application.group.has_user(user):
            raise UserNotInGroupError(user, application.group)

        application_id = application.id
        application = application.specific
        application_type = application_type_registry.get_by_model(application)
        application_type.pre_delete(user, application)

        application.delete()

        application_deleted.send(self, application_id=application_id,
                                 application=application, user=user)
