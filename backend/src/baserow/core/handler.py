from .models import Group, GroupUser
from .exceptions import UserNotIngroupError


class CoreHandler:
    def create_group(self, user, **kwargs):
        """Creates a new group for an existing user.

        :param user: The user that must be in the group.
        :type user: User
        :return: The newly created GroupUser object
        :rtype: GroupUser
        """

        allowed_fields = ['name']

        group_values = {}
        for field in allowed_fields:
            if field in allowed_fields:
                group_values[field] = kwargs[field]

        group = Group.objects.create(**group_values)
        last_order = GroupUser.get_last_order(user)
        group_user = GroupUser.objects.create(group=group, user=user, order=last_order)

        return group_user

    def update_group(self, user, group, **kwargs):
        """Updates fields of a group.

        :param user:
        :param group:
        :return:
        """

        if not group.has_user(user):
            raise UserNotIngroupError(f'The user {user} does not belong to the group '
                                      f'{group}.')

        allowed_fields = ['name']

        for field in allowed_fields:
            if field in kwargs:
                setattr(group, field, kwargs[field])

        group.save()

        return group

    def delete_group(self, user, group):
        """Deletes an existing group.

        :param user:
        :type: user: User
        :param group:
        :type: group: Group
        :return:
        """

        if not group.has_user(user):
            raise UserNotIngroupError(f'The user {user} does not belong to the group '
                                      f'{group}.')

        group.delete()

    def order_groups(self, user, group_ids):
        """Changes the order of groups for a user.

        :param user:
        :type: user: User
        :param group_ids: A list of group ids ordered the way they need to be ordered.
        :type group_ids: List[int]
        """

        for index, group_id in enumerate(group_ids):
            GroupUser.objects.filter(
                user=user,
                group_id=group_id
            ).update(order=index + 1)
