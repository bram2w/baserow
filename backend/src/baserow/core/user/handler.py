from urllib.parse import urlparse, urljoin
from itsdangerous import URLSafeTimedSerializer

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.utils import translation
from django.utils.translation import gettext as _

from baserow.core.handler import CoreHandler
from baserow.core.registries import plugin_registry
from baserow.core.exceptions import BaseURLHostnameNotAllowed
from baserow.core.exceptions import GroupInvitationEmailMismatch
from baserow.core.models import UserProfile

from .exceptions import (
    UserAlreadyExist,
    UserNotFound,
    PasswordDoesNotMatchValidation,
    InvalidPassword,
    DisabledSignupError,
)
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
        :raises ValueError: When neither a `user_id` or `email` has been provided.
        :raises UserNotFound: When the user with the provided parameters has not been
            found.
        :return: The requested user.
        :rtype: User
        """

        if not user_id and not email:
            raise ValueError("Either a user id or email must be provided.")

        query = User.objects.all()

        if user_id:
            query = query.filter(id=user_id)

        if email:
            email = normalize_email_address(email)
            query = query.filter(username=email)

        try:
            return query.get()
        except User.DoesNotExist:
            raise UserNotFound("The user with the provided parameters is not found.")

    def create_user(
        self,
        name,
        email,
        password,
        language=settings.LANGUAGE_CODE,
        group_invitation_token=None,
        template=None,
    ):
        """
        Creates a new user with the provided information and creates a new group and
        application for him. If the optional group invitation is provided then the user
        joins that group without creating a new one.

        :param name: The name of the new user.
        :type name: str
        :param email: The e-mail address of the user, this is also the username.
        :type email: str
        :param password: The password of the user.
        :type password: str
        :param language: The language selected by the user.
        :type language: str
        :param group_invitation_token: If provided and valid, the invitation will be
            accepted and and initial group will not be created.
        :type group_invitation_token: str
        :param template: If provided, that template will be installed into the newly
            created group.
        :type template: Template
        :raises: UserAlreadyExist: When a user with the provided username (email)
            already exists.
        :raises GroupInvitationEmailMismatch: If the group invitation email does not
            match the one of the user.
        :raises SignupDisabledError: If signing up is disabled.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The user object.
        :rtype: User
        """

        core_handler = CoreHandler()

        if not core_handler.get_settings().allow_new_signups:
            raise DisabledSignupError("Sign up is disabled.")

        email = normalize_email_address(email)

        if User.objects.filter(Q(email=email) | Q(username=email)).exists():
            raise UserAlreadyExist(f"A user with username {email} already exists.")

        group_invitation = None
        group_user = None

        if group_invitation_token:
            group_invitation = core_handler.get_group_invitation_by_token(
                group_invitation_token
            )

            if email != group_invitation.email:
                raise GroupInvitationEmailMismatch(
                    "The email address of the invitation does not match the one of the "
                    "user."
                )

        user = User(first_name=name, email=email, username=email)

        try:
            validate_password(password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(password)

        if not User.objects.exists():
            # This is the first ever user created in this baserow instance and
            # therefore the administrator user, lets give them staff rights so they
            # can set baserow wide settings.
            user.is_staff = True

        user.save()

        # Since there is a one-to-one relationship between the user and their
        # profile, we create and populate it here because this way
        # you can assume safely that, everywhere else in the code, it exists.
        UserProfile.objects.create(user=user, language=language)

        if group_invitation_token:
            group_user = core_handler.accept_group_invitation(user, group_invitation)

        if not group_user:
            with translation.override(language):
                group_user = core_handler.create_group(
                    user=user, name=_("%(name)s's group") % {"name": name}
                )

        if not group_invitation_token and template:
            core_handler.install_template(user, group_user.group, template)

        # Call the user_created method for each plugin that is un the registry.
        for plugin in plugin_registry.registry.values():
            plugin.user_created(user, group_user.group, group_invitation, template)

        return user

    def update_user(self, user, first_name=None, language=None):
        """
        Update user modifiable properties

        :param user: The user instance to update.
        :type user: User
        :param language: The language selected by the user.
        :type language: str
        :return: The user object.
        :rtype: User
        """

        if first_name is not None:
            user.first_name = first_name
            user.save()

        if language is not None:
            user.profile.language = language
            user.profile.save()

        return user

    def get_reset_password_signer(self):
        """
        Instantiates the password reset serializer that can dump and load values.

        :return: The itsdangerous serializer.
        :rtype: URLSafeTimedSerializer
        """

        return URLSafeTimedSerializer(settings.SECRET_KEY, "user-reset-password")

    def send_reset_password_email(self, user, base_url):
        """
        Sends an email containing a password reset url to the user.

        :param user: The user instance.
        :type user: User
        :param base_url: The base url of the frontend, where the user can reset his
            password. The reset token is appended to the URL (base_url + '/TOKEN').
            Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :type base_url: str
        """

        parsed_base_url = urlparse(base_url)
        if parsed_base_url.hostname != settings.PUBLIC_WEB_FRONTEND_HOSTNAME:
            raise BaseURLHostnameNotAllowed(
                f"The hostname {parsed_base_url.netloc} is not allowed."
            )

        signer = self.get_reset_password_signer()
        signed_user_id = signer.dumps(user.id)

        if not base_url.endswith("/"):
            base_url += "/"

        reset_url = urljoin(base_url, signed_user_id)

        with translation.override(user.profile.language):
            email = ResetPasswordEmail(user, reset_url, to=[user.email])
            email.send()

    def reset_password(self, token, password):
        """
        Changes the password of a user if the provided token is valid.

        :param token: The signed token that was send to the user.
        :type token: str
        :param password: The new password of the user.
        :type password: str
        :raises BadSignature: When the provided token has a bad signature.
        :raises SignatureExpired: When the provided token's signature has expired.
        :raises UserNotFound: When a user related to the provided token has not been
            found.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The updated user instance.
        :rtype: User
        """

        signer = self.get_reset_password_signer()
        user_id = signer.loads(token, max_age=settings.RESET_PASSWORD_TOKEN_MAX_AGE)

        user = self.get_user(user_id=user_id)

        try:
            validate_password(password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(password)
        user.save()

        return user

    def change_password(self, user, old_password, new_password):
        """
        Changes the password of the provided user if the old password matches the
        existing one.

        :param user: The user for which the password needs to be changed.
        :type user: User
        :param old_password: The old password of the user. This must match with the
            existing password else the InvalidPassword exception is raised.
        :type old_password: str
        :param new_password: The new password of the user. After changing the user
            can only authenticate with this password.
        :type new_password: str
        :raises InvalidPassword: When the provided old password is incorrect.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The changed user instance.
        :rtype: User
        """

        if not user.check_password(old_password):
            raise InvalidPassword("The provided old password is incorrect.")

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(new_password)
        user.save()

        return user
