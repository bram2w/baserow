from django.contrib.auth import get_user_model

from rest_framework_jwt.settings import api_settings

from baserow.core.models import UserProfile


User = get_user_model()
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class UserFixtures:
    def generate_token(self, user):
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return token

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

        profile_data["language"] = kwargs.pop("language", "en")

        user = User(**kwargs)
        user.set_password(kwargs["password"])
        user.save()

        # Profile creation
        profile_data["user"] = user
        UserProfile.objects.create(**profile_data)

        return user

    def create_user_and_token(self, **kwargs):
        user = self.create_user(**kwargs)
        token = self.generate_token(user)
        return user, token
