from typing import Optional

from django.contrib.auth import get_user_model

from baserow.core.exceptions import IsNotAdminError
from baserow_premium.user_admin.exceptions import (
    CannotDeactivateYourselfException,
    CannotDeleteYourselfException,
    UserDoesNotExistException,
    InvalidSortDirectionException,
    InvalidSortAttributeException,
)

User = get_user_model()


def sort_field_names_to_user_attributes():
    return {
        "id": "id",
        "is_active": "is_active",
        "name": "first_name",
        "username": "username",
        "date_joined": "date_joined",
        "last_login": "last_login",
    }


def allowed_user_admin_sort_field_names():
    return sort_field_names_to_user_attributes().keys()


class UserAdminHandler:
    def get_users(
        self,
        requesting_user: User,
        username_search: Optional[str] = None,
        sorts: Optional[str] = None,
    ):
        """
        Looks up all users, performs an optional username search and then sorts the
        resulting user queryset and returns it. By default if no sorts are provided
        sorts by user id ascending.

        :param requesting_user: The user who is making the request to get_users, the
            user must be a staff member or else an exception will
            be raised.
        :param username_search: An optional icontains username search to filter the
            returned users by.
        :param sorts: A comma separated string like `+username,-id` to be applied as
            an ordering order over the returned users. Prefix the attribute with +
            for an ascending sort, - for descending.
            See `allowed_user_admin_sort_field_names` for the allowed attributes to
            sort by.
            Raises InvalidSortAttributeException or InvalidSortAttributeException if
            an invalid sort string is provided.
        :return: A queryset of users in Baserow, optionally sorted and ordered by the
            specified parameters.
        """

        self._raise_if_not_permitted(requesting_user)

        users = User.objects.prefetch_related(
            "groupuser_set", "groupuser_set__group"
        ).all()
        if username_search is not None:
            users = users.filter(username__icontains=username_search)

        users = self._apply_sorts_or_default_sort(sorts, users)

        return users

    @staticmethod
    def _apply_sorts_or_default_sort(sorts: str, queryset):
        """
        Takes a comma separated string in the form of +attribute,-attribute2 and
        applies them to a django queryset in order.
        Defaults to sorting by id if no sorts are provided.
        Raises an InvalidSortDirectionException if an attribute does not begin with `+`
        or `-`.
        Raises an InvalidSortAttributeException if an unknown attribute is supplied to
        sort by or multiple of the same attribute are provided.

        :param sorts: The list of sorts to apply to the queryset.
        :param queryset: The queryset to sort.
        :return: The sorted queryset.
        """

        if sorts is None:
            return queryset.order_by("id")

        parsed_django_order_bys = []
        already_seen_sorts = set()
        for s in sorts.split(","):
            if len(s) <= 2:
                raise InvalidSortAttributeException()

            sort_direction_prefix = s[0]
            sort_field_name = s[1:]

            try:
                sort_direction_to_django_prefix = {"+": "", "-": "-"}
                direction = sort_direction_to_django_prefix[sort_direction_prefix]
            except KeyError:
                raise InvalidSortDirectionException()

            try:
                attribute = sort_field_names_to_user_attributes()[sort_field_name]
            except KeyError:
                raise InvalidSortAttributeException()

            if attribute in already_seen_sorts:
                raise InvalidSortAttributeException()
            else:
                already_seen_sorts.add(attribute)

            parsed_django_order_bys.append(f"{direction}{attribute}")

        return queryset.order_by(*parsed_django_order_bys)

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
