from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .exceptions import UserAlreadyExist


User = get_user_model()


class UserHandler:
    def create_user(self, name, email, password):
        """Create a new user with the provided information.

        :param name: The name of the new user.
        :param email: The e-mail address of the user, this is also the username.
        :param password: The password of the user.
        :return: The user object.
        :rtype: User
        """

        try:
            user = User(first_name=name, email=email, username=email)
            user.set_password(password)
            user.save()
        except IntegrityError:
            raise UserAlreadyExist(f'A user with username {email} already exists.')

        return user
