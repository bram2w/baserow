from baserow.core.handler import CoreHandler
from baserow.core.signals import group_deleted
from baserow.core.exceptions import IsNotAdminError
from baserow_premium.admin.groups.exceptions import CannotDeleteATemplateGroupError


class GroupsAdminHandler:
    def delete_group(self, user, group):
        """
        Deletes an existing group and related applications if the user is staff.

        :param user: The user on whose behalf the group is deleted
        :type: user: User
        :param group: The group instance that must be deleted.
        :type: group: Group
        :raises IsNotAdminError: If the user is not admin or staff.
        """

        if not user.is_staff:
            raise IsNotAdminError()

        if group.has_template():
            raise CannotDeleteATemplateGroupError()

        # Load the group users before the group is deleted so that we can pass those
        # along with the signal.
        group_id = group.id
        group_users = list(group.users.all())

        CoreHandler()._delete_group(group)

        group_deleted.send(
            self, group_id=group_id, group=group, group_users=group_users
        )
