import datetime
from datetime import timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.db.utils import IntegrityError
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from itsdangerous import URLSafeTimedSerializer
from opentelemetry import trace

from baserow.core.auth_provider.handler import PasswordProviderHandler
from baserow.core.auth_provider.models import AuthProviderModel
from baserow.core.exceptions import (
    BaseURLHostnameNotAllowed,
    WorkspaceInvitationEmailMismatch,
)
from baserow.core.handler import CoreHandler
from baserow.core.models import (
    BlacklistedToken,
    Template,
    UserLogEntry,
    UserProfile,
    Workspace,
    WorkspaceUser,
)
from baserow.core.registries import plugin_registry
from baserow.core.signals import (
    before_user_deleted,
    user_deleted,
    user_permanently_deleted,
    user_restored,
    user_updated,
)
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import generate_hash

from ..telemetry.utils import baserow_trace_methods
from .emails import (
    AccountDeleted,
    AccountDeletionCanceled,
    AccountDeletionScheduled,
    ResetPasswordEmail,
)
from .exceptions import (
    DeactivatedUserException,
    DisabledSignupError,
    InvalidPassword,
    PasswordDoesNotMatchValidation,
    RefreshTokenAlreadyBlacklisted,
    ResetPasswordDisabledError,
    UserAlreadyExist,
    UserIsLastAdmin,
    UserNotFound,
)
from .signals import user_password_changed
from .utils import normalize_email_address

User = get_user_model()

tracer = trace.get_tracer(__name__)


class UserHandler(metaclass=baserow_trace_methods(tracer)):
    def get_active_user(
        self,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        exclude_users_scheduled_to_be_deleted: bool = False,
    ) -> AbstractUser:
        """
        Finds and returns a single active user instance based on the provided
        parameters.

        :param user_id: The user id of the user.
        :param email: The username, which is their email address, of the user.
        :param exclude_users_scheduled_to_be_deleted: If set to True, the user will
            not be returned if it is scheduled to be deleted.
        :raises ValueError: When neither a `user_id` or `email` has been
            provided.
        :raises UserNotFound: When the user with the provided parameters has not
            been found.
        :return: The requested user.
        """

        if not user_id and not email:
            raise ValueError("Either a user id or email must be provided.")

        query = User.objects.filter(is_active=True).select_related("profile")
        if exclude_users_scheduled_to_be_deleted:
            query = query.filter(profile__to_be_deleted=False)

        if user_id:
            query = query.filter(id=user_id)

        if email:
            email = normalize_email_address(email)
            query = query.filter(username=email)

        try:
            return query.get()
        except User.DoesNotExist:
            raise UserNotFound("The user with the provided parameters is not found.")

    def force_create_user(self, email, name, password, **kwargs):
        """
        Creates a new user and their profile.

        :param email: The username/email of the new user.
        :param name: The full name of the new user.
        :param password: The password of the new user.
        :param kwargs: Additional kwargs that must be added when creating the User
            object.
        :raises UserAlreadyExist: When the user with the provided email already exists.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :raises DeactivatedUserException: When a user with the provided email exists but
            has been deactivated.
        :return: The newly created user object.
        """

        language = settings.LANGUAGE_CODE
        if "language" in kwargs:
            language = kwargs.pop("language") or settings.LANGUAGE_CODE

        email = normalize_email_address(email)
        user_query = User.objects.filter(Q(email=email) | Q(username=email))
        if user_query.exists():
            user = user_query.first()
            if user.is_active:
                raise UserAlreadyExist(f"A user with email {email} already exists.")
            else:
                raise DeactivatedUserException(
                    f"User with email {email} has been deactivated."
                )

        user = User(first_name=name, email=email, username=email, **kwargs)

        if password is not None:
            try:
                validate_password(password, user)
            except ValidationError as e:
                raise PasswordDoesNotMatchValidation(e.messages)
            user.set_password(password)

        user.save()

        # Immediately create the one-to-one relationship with the user profile
        # so we can safely use it everywhere else in the code.
        UserProfile.objects.create(user=user, language=language)

        return user

    def create_user(
        self,
        name: str,
        email: str,
        password: str,
        language: Optional[str] = None,
        workspace_invitation_token: Optional[str] = None,
        template: Template = None,
        auth_provider: Optional[AuthProviderModel] = None,
    ) -> AbstractUser:
        """
        Creates a new user with the provided information and creates a new workspace and
        application for him. If the optional workspace invitation is provided then the
        user joins that workspace without creating a new one.

        :param name: The name of the new user.
        :param email: The e-mail address of the user, this is also the username.
        :param password: The password of the user.
        :param language: The language selected by the user.
        :param workspace_invitation_token: If provided and valid, the invitation will be
            accepted and initial workspace will not be created.
        :param template: If provided, that template will be installed into the newly
            created workspace.
        :param auth_provider: If provided, a reference to the authentication
            provider will be stored in order to be able to provide different options
            for the user to login.
        :raises: UserAlreadyExist: When a user with the provided username (email)
            already exists.
        :raises WorkspaceInvitationEmailMismatch: If the workspace invitation email
            does not match the one of the user.
        :raises SignupDisabledError: If signing up is disabled.
        :return: The user object.
        """

        core_handler = CoreHandler()

        workspace_invitation = None
        workspace_user = None

        if workspace_invitation_token:
            workspace_invitation = core_handler.get_workspace_invitation_by_token(
                workspace_invitation_token
            )

            if email != workspace_invitation.email:
                raise WorkspaceInvitationEmailMismatch(
                    "The email address of the invitation does not match the one of the "
                    "user."
                )

        instance_settings = core_handler.get_settings()
        allow_new_signups = instance_settings.allow_new_signups
        allow_signup_for_invited_user = (
            instance_settings.allow_signups_via_workspace_invitations
            and workspace_invitation is not None
        )
        if not (allow_new_signups or allow_signup_for_invited_user):
            raise DisabledSignupError("Sign up is disabled.")

        user = self.force_create_user(
            email=email,
            name=name,
            password=password,
            # This is the first ever user created in this baserow instance and
            # therefore the administrator user, lets give them staff rights so they
            # can set baserow wide settings.
            is_staff=not User.objects.exists(),
            language=language,
        )

        if instance_settings.show_admin_signup_page:
            instance_settings.show_admin_signup_page = False
            instance_settings.save()

        # If we have an invitation to a workspace, then accept it.
        if workspace_invitation_token:
            workspace_user = core_handler.accept_workspace_invitation(
                user, workspace_invitation
            )

        # If we still don't have a `WorkspaceUser`, which will be because we weren't
        # invited to a workspace, and `allow_global_workspace_creation` is enabled,
        # we'll create a workspace for this new user.
        if not workspace_user and instance_settings.allow_global_workspace_creation:
            with translation.override(language):
                workspace_user = core_handler.create_workspace(
                    user=user, name=_("%(name)s's workspace") % {"name": name}
                )

        # If we've created a `WorkspaceUser` at some point, pluck out the `Workspace`.
        workspace = getattr(workspace_user, "workspace", None)
        user.default_workspace = workspace

        if not workspace_invitation_token and template and workspace:
            core_handler.install_template(user, workspace, template)

        # Call the user_created method for each plugin that is in the registry.
        for plugin in plugin_registry.registry.values():
            plugin.user_created(user, workspace, workspace_invitation, template)

        # register the authentication provider used to create the user
        if auth_provider is None:
            auth_provider = PasswordProviderHandler.get()
        auth_provider.user_signed_in(user)

        return user

    def update_user(
        self,
        user: AbstractUser,
        first_name: Optional[str] = None,
        language: Optional[str] = None,
        email_notification_frequency: Optional[str] = None,
    ) -> AbstractUser:
        """
        Updates the user's account editable properties. Handles the scenario
        when a user edits his own account.

        :param user: The user instance to update.
        :param first_name: The new user first name.
        :param language: The language selected by the user.
        :param email_notification_frequency: The frequency chosen by the user to
            receive email notifications.
        :return: The updated user object.
        """

        if first_name is not None and first_name != user.first_name:
            user.first_name = first_name
            user.save()

        profile_fields_to_update = []

        if language is not None:
            user.profile.language = language
            profile_fields_to_update.append("language")

        if email_notification_frequency is not None:
            user.profile.email_notification_frequency = email_notification_frequency
            profile_fields_to_update.append("email_notification_frequency")

        if profile_fields_to_update:
            user.profile.save(update_fields=profile_fields_to_update)

        user_updated.send(self, performed_by=user, user=user)

        return user

    def get_reset_password_signer(self) -> URLSafeTimedSerializer:
        """
        Instantiates the password reset serializer that can dump and load values.

        :return: The itsdangerous serializer.
        :rtype: URLSafeTimedSerializer
        """

        return URLSafeTimedSerializer(settings.SECRET_KEY, "user-reset-password")

    def send_reset_password_email(self, user: AbstractUser, base_url: str):
        """
        Sends an email containing a password reset url to the user.

        :param user: The user instance.
        :param base_url: The base url of the frontend, where the user can reset his
            password. The reset token is appended to the URL (base_url + '/TOKEN').
            Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :raises: ResetPasswordDisabledError: If the reset password is disabled.
        """

        if not CoreHandler().get_settings().allow_reset_password:
            raise ResetPasswordDisabledError("Reset password is disabled")

        parsed_base_url = urlparse(base_url)
        if parsed_base_url.hostname not in (
            settings.PUBLIC_WEB_FRONTEND_HOSTNAME,
            settings.BASEROW_EMBEDDED_SHARE_HOSTNAME,
        ):
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

    def reset_password(self, token: str, password: str) -> AbstractUser:
        """
        Changes the password of a user if the provided token is valid.

        :param token: The signed token that was send to the user.
        :param password: The new password of the user.
        :raises SignatureExpired: When the provided token's signature has expired.
        :raises UserNotFound: When a user related to the provided token has not been
            found.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The updated user instance.
        """

        if not CoreHandler().get_settings().allow_reset_password:
            raise ResetPasswordDisabledError("Reset password is disabled.")

        signer = self.get_reset_password_signer()
        user_id = signer.loads(token, max_age=settings.RESET_PASSWORD_TOKEN_MAX_AGE)

        user = self.get_active_user(user_id=user_id)

        try:
            validate_password(password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(password)
        user.save()

        # Update the last password change timestamp to invalidate old authentication
        # tokens.
        user.profile.last_password_change = timezone.now()
        user.profile.save()

        user_password_changed.send(
            self, user=user, ignore_web_socket_id=getattr(user, "web_socket_id", None)
        )

        return user

    def change_password(
        self, user: AbstractUser, old_password: str, new_password: str
    ) -> AbstractUser:
        """
        Changes the password of the provided user if the old password matches the
        existing one.

        :param user: The user for which the password needs to be changed.
        :param old_password: The old password of the user. This must match with the
            existing password else the InvalidPassword exception is raised.
        :param new_password: The new password of the user. After changing the user
            can only authenticate with this password.
        :raises InvalidPassword: When the provided old password is incorrect.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The changed user instance.
        """

        if not user.check_password(old_password):
            raise InvalidPassword("The provided old password is incorrect.")

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(new_password)
        user.save()

        # Update the last password change timestamp to invalidate old authentication
        # tokens.
        user.profile.last_password_change = timezone.now()
        user.profile.save()

        user_password_changed.send(
            self, user=user, ignore_web_socket_id=getattr(user, "web_socket_id", None)
        )

        return user

    def user_signed_in_via_provider(
        self, user: AbstractUser, authentication_provider: AuthProviderModel
    ):
        """
        Registers the authentication provider used to authenticate the user.

        :param user: The user instance.
        :param authentication_provider: The authentication provider instance.
        """

        authentication_provider.user_signed_in(user)
        self.user_signed_in(user)

    def user_signed_in(self, user: AbstractUser):
        """
        Executes tasks and informs plugins when a user signs in.

        :param user: The user that has just signed in.
        """

        if user.profile.to_be_deleted:
            self.cancel_user_deletion(user)

        update_last_login(None, user)
        UserLogEntry.objects.create(actor=user, action="SIGNED_IN")

        # Call the user_signed_in method for each plugin that is in the registry to
        # notify all plugins that a user has signed in.
        from baserow.core.registries import plugin_registry

        for plugin in plugin_registry.registry.values():
            plugin.user_signed_in(user)

    def delete_user_log_entries_older_than(self, cutoff: datetime):
        """
        Deletes all UserLogEntry entries that are older than the given cutoff date.

        :param cutoff: The date and time before which all entries will be deleted.
        """

        delete_qs = UserLogEntry.objects.filter(timestamp__lt=cutoff)
        delete_qs._raw_delete(delete_qs.db)

    def schedule_user_deletion(self, user: AbstractUser):
        """
        Schedules the user account deletion. The user is flagged as `to_be_deleted` and
        will be deleted after a predefined grace delay unless the user
        cancel his account deletion by log in again.
        This action sends an email to the user to explain the process.

        :param user: The user to flag as `to_be_deleted`.
        :raises UserIsLastAdmin: When the user cannot be deleted as they are the last
            admin.
        """

        if (
            user.is_staff
            and not User.objects.filter(is_staff=True).exclude(pk=user.pk).exists()
        ):
            raise UserIsLastAdmin("You are the last admin of the instance.")

        before_user_deleted.send(self, user=user)

        user.profile.to_be_deleted = True
        user.profile.save()

        # update last login to be more accurate
        update_last_login(None, user)

        core_settings = CoreHandler().get_settings()

        days_left = getattr(
            settings,
            "FORCE_ACCOUNT_DELETION_GRACE_DELAY",
            timedelta(days=core_settings.account_deletion_grace_delay),
        ).days

        with translation.override(user.profile.language):
            email = AccountDeletionScheduled(user, days_left, to=[user.email])
            email.send()

        user_deleted.send(self, performed_by=user, user=user)

    def cancel_user_deletion(self, user: AbstractUser):
        """
        Cancels a previously scheduled user account deletion. This action send an email
        to the user to confirm the cancelation.

        :param user: The user currently in pending deletion.
        """

        user.profile.to_be_deleted = False
        user.profile.save()

        with translation.override(user.profile.language):
            email = AccountDeletionCanceled(user, to=[user.email])
            email.send()

        user_restored.send(self, performed_by=user, user=user)

    def delete_expired_users_and_related_workspaces_if_last_admin(
        self, grace_delay: Optional[timedelta] = None
    ):
        """
        Executes all previously scheduled user account deletions for which
        the `last_login` date is earlier than the defined grace delay. If the users
        are the last admin of some workspaces, these workspaces are also deleted. An
        email is sent to confirm the user account deletion. This task is periodically
        executed.

        :param grace_delay: A timedelta that indicate the delay before permanently
          delete a user account. If this parameter is not given, the delay is defined
          in the core Baserow settings.
        """

        if not isinstance(grace_delay, timedelta):
            core_settings = CoreHandler().get_settings()
            grace_delay = getattr(
                settings,
                "FORCE_ACCOUNT_DELETION_GRACE_DELAY",
                timedelta(days=core_settings.account_deletion_grace_delay),
            )

        limit_date = timezone.now() - grace_delay

        users_to_delete = User.objects.filter(
            profile__to_be_deleted=True, last_login__lt=limit_date
        )

        workspace_users = WorkspaceUser.objects.filter(user__in=users_to_delete)

        deleted_user_info = []
        for u in users_to_delete.all():
            workspace_ids = [
                gu.workspace_id for gu in workspace_users if gu.user_id == u.id
            ]
            deleted_user_info.append(
                (u.id, u.username, u.email, u.profile.language, workspace_ids)
            )

        # A workspace need to be deleted if there was an admin before and there is no
        # *active* admin after the users deletion.
        workspaces_to_be_deleted = Workspace.objects.annotate(
            admin_count_after=Count(
                "workspaceuser",
                filter=(
                    Q(workspaceuser__permissions="ADMIN")
                    & ~Q(workspaceuser__user__in=users_to_delete)
                ),
            ),
        ).filter(template=None, admin_count_after=0)

        with transaction.atomic():
            for workspace in workspaces_to_be_deleted:
                # Here we use the trash handler to be sure that we delete every thing
                # related the workspaces like
                TrashHandler.permanently_delete(workspace)
            users_to_delete.delete()

        for id, username, email, language, workspace_ids in deleted_user_info:
            with translation.override(language):
                email = AccountDeleted(username, to=[email])
                email.send()
            user_permanently_deleted.send(self, user_id=id, workspace_ids=workspace_ids)

    def get_all_active_users_qs(self) -> QuerySet:
        """
        Returns a queryset of all users which are considered active and usable in a
        Baserow instance. Will filter out users who have be "banned/deactivated" by an
        admin or users who have scheduled their account for a deletion.
        """

        return User.objects.filter(
            profile__to_be_deleted=False,
            is_active=True,
        )

    def blacklist_refresh_token(
        self, refresh_token: str, expires_at: datetime.datetime
    ):
        """
        Blacklists the provided refresh token. This results in not being able to
        generate access tokens anymore. The access does remain working until it expires.

        :param user: The user that owns the refresh token.
        :param refresh_token: The raw refresh token that must be blacklisted.
        :param expires_at: Date when the token expires, this will be used when
            cleaning up.
        """

        hashed_token = generate_hash(refresh_token)

        try:
            BlacklistedToken.objects.create(
                hashed_token=hashed_token,
                expires_at=expires_at,
            )
        except IntegrityError:
            raise RefreshTokenAlreadyBlacklisted

    def refresh_token_is_blacklisted(self, refresh_token: str) -> bool:
        """
        Checks if the provided refresh token is blacklisted.

        :param refresh_token: The refresh token that must be checked.
        :return: Whether the token is blacklisted.
        """

        hashed_token = generate_hash(refresh_token)
        return BlacklistedToken.objects.filter(hashed_token=hashed_token).exists()
