from itsdangerous import URLSafeTimedSerializer

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from baserow.core.handler import CoreHandler
from baserow.core.registries import plugin_registry

from .exceptions import UserAlreadyExist, UserNotFound
from .emails import ResetPasswordEmail
from .utils import normalize_email_address


User = get_user_model()


class UserHandler:
    def get_user(self, user_id=None, email=None):
        """
        Finds and returns a single user instance based on the provided parameters.

        :param user_id: The user id of the user.
        :type user_id: int
        :param email: The username, which is their email address, of the user.
        :type email: str
        :return: The requested user.
        :rtype: User
        """

        if not user_id and not email:
            raise ValueError('Either a user id or email must be provided.')

        query = User.objects.all()

        if user_id:
            query = query.filter(id=user_id)

        if email:
            email = normalize_email_address(email)
            query = query.filter(username=email)

        try:
            return query.get()
        except User.DoesNotExist:
            raise UserNotFound('The user with the provided parameters is not found.')

    def create_user(self, name, email, password):
        """
        Creates a new user with the provided information and creates a new group and
        application for him.

        :param name: The name of the new user.
        :param email: The e-mail address of the user, this is also the username.
        :param password: The password of the user.
        :return: The user object.
        :rtype: User
        """

        try:
            email = normalize_email_address(email)
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

    def get_reset_password_signer(self):
        """
        Instantiates the password reset serializer that can dump and load values.

        :return: The itsdangerous serializer.
        :rtype: URLSafeTimedSerializer
        """

        return URLSafeTimedSerializer(settings.SECRET_KEY, 'user-reset-password')

    def send_reset_password_email(self, user, base_url):
        """
        Sends an email containing a password reset url to the user.

        :param user: The user instance.
        :type user: User
        :param base_url: The base url of the frontend, where the user can reset his
            password. The reset token is appended to the URL (base_url + '/TOKEN').
        :type base_url: str
        """

        signer = self.get_reset_password_signer()
        signed_user_id = signer.dumps(user.id)
        reset_url = f'{base_url}/{signed_user_id}'

        email = ResetPasswordEmail(user, reset_url, to=[user.email])
        email.send()

    def reset_password(self, token, password):
        """
        Changes the password of a user if the provided token is valid.

        :param token: The signed token that was send to the user.
        :type token: str
        :param password: The new password of the user.
        :type password: str
        :return: The updated user instance.
        :rtype: User
        """

        signer = self.get_reset_password_signer()
        user_id = signer.loads(token, max_age=settings.RESET_PASSWORD_TOKEN_MAX_AGE)

        user = self.get_user(user_id=user_id)
        user.set_password(password)
        user.save()

        return user
