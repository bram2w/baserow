from django.contrib.auth import get_user_model
from django.db import IntegrityError

from baserow.core.handler import CoreHandler
from baserow.core.registries import plugin_registry

from .exceptions import UserAlreadyExist


User = get_user_model()


class UserHandler:
    def create_user(self, name, email, password):
        """
        Create a new user with the provided information and create a new group and
        application for him.

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

        # Insert some initial data for the newly created user.
        core_handler = CoreHandler()
        group_user = core_handler.create_group(user=user, name=f"{name}'s group")

        # Call the user_created method for each plugin that is un the registry.
        for plugin in plugin_registry.registry.values():
            plugin.user_created(user, group_user.group)

        return user
