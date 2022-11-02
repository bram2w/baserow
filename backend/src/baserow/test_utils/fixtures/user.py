from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from baserow.api.sessions import (
    set_client_undo_redo_action_group_id,
    set_untrusted_client_session_id,
)
from baserow.core.models import GROUP_USER_PERMISSION_ADMIN, GroupUser, UserProfile

User = get_user_model()


class UserFixtures:
    def generate_token(self, user):
        return str(AccessToken.for_user(user))

    def generate_refresh_token(self, user):
        return str(RefreshToken.for_user(user))

    def create_user(self, **kwargs):
        profile_data = {}

        if "email" not in kwargs:
            kwargs["email"] = self.fake.email()

        if "username" not in kwargs:
            kwargs["username"] = kwargs["email"]

        if "first_name" not in kwargs:
            kwargs["first_name"] = self.fake.name()

        if "password" not in kwargs:
            kwargs["password"] = "password"

        session_id = kwargs.pop("session_id", "default-test-user-session-id")
        action_group = kwargs.pop("action_group", None)

        profile_data["language"] = kwargs.pop("language", "en")
        profile_data["to_be_deleted"] = kwargs.pop("to_be_deleted", False)

        user = User(**kwargs)
        user.set_password(kwargs["password"])
        user.save()

        # Profile creation
        profile_data["user"] = user
        UserProfile.objects.create(**profile_data)

        set_untrusted_client_session_id(user, session_id)
        set_client_undo_redo_action_group_id(user, action_group)

        # add it to a specific group if it is given
        if "group" in kwargs:
            GroupUser.objects.create(
                group=kwargs["group"],
                user=user,
                order=0,
                permissions=GROUP_USER_PERMISSION_ADMIN,
            )

        return user

    def create_user_and_token(self, **kwargs):
        user = self.create_user(**kwargs)
        token = self.generate_token(user)
        return user, token
