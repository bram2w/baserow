from typing import Optional

from django.contrib.auth import get_user_model

from baserow.core.exceptions import IsNotAdminError
from baserow_premium.admin.users.exceptions import (
    CannotDeactivateYourselfException,
    CannotDeleteYourselfException,
    UserDoesNotExistException,
)

User = get_user_model()


class UserAdminHandler:
    def update_user(
        self,
        requesting_user: User,
        user_id: int,
        username: Optional[str] = None,
        name: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_staff: Optional[bool] = None,
    ):
        """
        Updates a specified user with new attribute values. Will raise an exception
        if a user attempts to de-activate or un-staff themselves.

        :param requesting_user: The user who is making the request to update a user, the
            user must be a staff member or else an exception will
            be raised.
        :param user_id: The id of the user to update, if they do not exist raises a
            UserDoesNotExistException.
        :param is_staff: Optional value used to set if the user is an admin or not.
        :param is_active: Optional value to disable or enable login for the user.
        :param password: Optional new password to securely set for the user.
        :param name: Optional new name to set on the user.
        :param username: Optional new username/email to set for the user.
        """

        self._raise_if_not_permitted(requesting_user)
        self._raise_if_locking_self_out_of_admin(
            is_active, is_staff, requesting_user, user_id
        )

        try:
            user = User.objects.select_for_update().get(id=user_id)
        except User.DoesNotExist:
            raise UserDoesNotExistException()

        if is_staff is not None:
            user.is_staff = is_staff
        if is_active is not None:
            user.is_active = is_active
        if password is not None:
            user.set_password(password)
        if name is not None:
            user.first_name = name
        if username is not None:
            user.email = username
            user.username = username

        user.save()
        return user

    @staticmethod
    def _raise_if_locking_self_out_of_admin(
        is_active, is_staff, requesting_user, user_id
    ):
        """
        Raises an exception if the requesting_user is about to lock themselves out of
        the admin area of Baserow by either turning off their staff status or disabling
        their account.
        """

        is_setting_staff_to_false = is_staff is not None and not is_staff
        is_setting_active_to_false = is_active is not None and not is_active
        if user_id == requesting_user.id and (
            is_setting_staff_to_false or is_setting_active_to_false
        ):
            raise CannotDeactivateYourselfException()

    def delete_user(self, requesting_user: User, user_id: int):
        """
        Deletes a specified user, raises an exception if you attempt to delete yourself.

        :param requesting_user: The user who is making the delete request , the
            user must be a staff member or else an exception will
            be raised.
        :param user_id: The id of the user to update, if they do not exist raises a
            UnknownUserException.
        """

        self._raise_if_not_permitted(requesting_user)

        if requesting_user.id == user_id:
            raise CannotDeleteYourselfException()

        try:
            user = User.objects.get(id=user_id)
            user.delete()
        except User.DoesNotExist:
            raise UserDoesNotExistException()

    @staticmethod
    def _raise_if_not_permitted(requesting_user):
        if not requesting_user.is_staff:
            raise IsNotAdminError()
