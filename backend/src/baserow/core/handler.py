import os
import json
import hashlib
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, urljoin
from itsdangerous import URLSafeSerializer
from zipfile import ZipFile, ZIP_DEFLATED

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.core.files.storage import default_storage

from baserow.core.user.utils import normalize_email_address

from .models import (
    Settings,
    Group,
    GroupUser,
    GroupInvitation,
    Application,
    Template,
    TemplateCategory,
    GROUP_USER_PERMISSION_CHOICES,
    GROUP_USER_PERMISSION_ADMIN,
)
from .exceptions import (
    UserNotInGroup,
    GroupDoesNotExist,
    ApplicationDoesNotExist,
    ApplicationNotInGroup,
    BaseURLHostnameNotAllowed,
    GroupInvitationEmailMismatch,
    GroupInvitationDoesNotExist,
    GroupUserDoesNotExist,
    GroupUserAlreadyExists,
    GroupUserIsLastAdmin,
    IsNotAdminError,
    TemplateFileDoesNotExist,
    TemplateDoesNotExist,
)
from .trash.handler import TrashHandler
from .utils import extract_allowed, set_allowed_attrs
from .registries import application_type_registry
from .signals import (
    application_created,
    application_updated,
    application_deleted,
    applications_reordered,
    group_created,
    group_updated,
    group_deleted,
    group_user_updated,
    group_user_deleted,
)
from .emails import GroupInvitationEmail


User = get_user_model()


class CoreHandler:
    def get_settings(self):
        """
        Returns a settings model instance containing all the admin configured settings.

        :return: The settings instance.
        :rtype: Settings
        """

        try:
            return Settings.objects.all()[:1].get()
        except Settings.DoesNotExist:
            return Settings.objects.create()

    def update_settings(self, user, settings_instance=None, **kwargs):
        """
        Updates one or more setting values if the user has staff permissions.

        :param user: The user on whose behalf the settings are updated.
        :type user: User
        :param settings_instance: If already fetched, the settings instance can be
            provided to avoid fetching the values for a second time.
        :type settings_instance: Settings
        :param kwargs: An dict containing the settings that need to be updated.
        :type kwargs: dict
        :return: The update settings instance.
        :rtype: Settings
        """

        if not user.is_staff:
            raise IsNotAdminError(user)

        if not settings_instance:
            settings_instance = self.get_settings()

        settings_instance = set_allowed_attrs(
            kwargs, ["allow_new_signups"], settings_instance
        )

        settings_instance.save()
        return settings_instance

    def get_group(self, group_id, base_queryset=None):
        """
        Selects a group with a given id from the database.

        :param group_id: The identifier of the group that must be returned.
        :type group_id: int
        :param base_queryset: The base queryset from where to select the group
            object. This can for example be used to do a `prefetch_related`.
        :type base_queryset: Queryset
        :raises GroupDoesNotExist: When the group with the provided id does not exist.
        :return: The requested group instance of the provided id.
        :rtype: Group
        """

        if base_queryset is None:
            base_queryset = Group.objects

        try:
            group = base_queryset.get(id=group_id)
        except Group.DoesNotExist:
            raise GroupDoesNotExist(f"The group with id {group_id} does not exist.")

        return group

    def create_group(self, user, **kwargs):
        """
        Creates a new group for an existing user.

        :param user: The user that must be in the group.
        :type user: User
        :return: The newly created GroupUser object
        :rtype: GroupUser
        """

        group_values = extract_allowed(kwargs, ["name"])
        group = Group.objects.create(**group_values)
        last_order = GroupUser.get_last_order(user)
        group_user = GroupUser.objects.create(
            group=group,
            user=user,
            order=last_order,
            permissions=GROUP_USER_PERMISSION_ADMIN,
        )

        group_created.send(self, group=group, user=user)

        return group_user

    def update_group(self, user, group, **kwargs):
        """
        Updates the values of a group if the user on whose behalf the request is made
        has admin permissions to the group.

        :param user: The user on whose behalf the change is made.
        :type user: User
        :param group: The group instance that must be updated.
        :type group: Group
        :raises ValueError: If one of the provided parameters is invalid.
        :return: The updated group
        :rtype: Group
        """

        if not isinstance(group, Group):
            raise ValueError("The group is not an instance of Group.")

        group.has_user(user, "ADMIN", raise_error=True)
        group = set_allowed_attrs(kwargs, ["name"], group)
        group.save()

        group_updated.send(self, group=group, user=user)

        return group

    def leave_group(self, user, group):
        """
        Called when a user of group wants to leave a group.

        :param user: The user that wants to leave the group.
        :type user: User
        :param group: The group that the user wants to leave.
        :type group: Group
        """

        if not isinstance(group, Group):
            raise ValueError("The group is not an instance of Group.")

        try:
            group_user = GroupUser.objects.get(user=user, group=group)
        except GroupUser.DoesNotExist:
            raise UserNotInGroup(user, self)

        # If the current user is an admin and he is the last admin left, he is not
        # allowed to leave the group otherwise no one will have control over it. He
        # needs to give someone else admin permissions first or he must leave the group.
        if (
            group_user.permissions == GROUP_USER_PERMISSION_ADMIN
            and GroupUser.objects.filter(
                group=group, permissions=GROUP_USER_PERMISSION_ADMIN
            ).count()
            == 1
        ):
            raise GroupUserIsLastAdmin(
                "The user is the last admin left in the group and can therefore not "
                "leave it."
            )

        # If the user is not the last admin, we can safely delete the user from the
        # group.
        group_user_id = group_user.id
        group_user.delete()
        group_user_deleted.send(
            self, group_user_id=group_user_id, group_user=group_user, user=user
        )

    def delete_group(self, user, group):
        """
        Deletes an existing group and related applications if the user has admin
        permissions for the group. The group can be restored after deletion using the
        trash handler.

        :param user: The user on whose behalf the delete is done.
        :type: user: User
        :param group: The group instance that must be deleted.
        :type: group: Group
        :raises ValueError: If one of the provided parameters is invalid.
        """

        if not isinstance(group, Group):
            raise ValueError("The group is not an instance of Group.")

        group.has_user(user, "ADMIN", raise_error=True)

        # Load the group users before the group is deleted so that we can pass those
        # along with the signal.
        group_id = group.id
        group_users = list(group.users.all())

        TrashHandler.trash(user, group, None, group)

        group_deleted.send(
            self, group_id=group_id, group=group, group_users=group_users, user=user
        )

    def order_groups(self, user, group_ids):
        """
        Changes the order of groups for a user.

        :param user: The user on whose behalf the ordering is done.
        :type: user: User
        :param group_ids: A list of group ids ordered the way they need to be ordered.
        :type group_ids: List[int]
        """

        for index, group_id in enumerate(group_ids):
            GroupUser.objects.filter(user=user, group_id=group_id).update(
                order=index + 1
            )

    def get_group_user(self, group_user_id, base_queryset=None):
        """
        Fetches a group user object related to the provided id from the database.

        :param group_user_id: The identifier of the group user that must be returned.
        :type group_user_id: int
        :param base_queryset: The base queryset from where to select the group user
            object. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises GroupDoesNotExist: When the group with the provided id does not exist.
        :return: The requested group user instance of the provided group_id.
        :rtype: GroupUser
        """

        if base_queryset is None:
            base_queryset = GroupUser.objects

        try:
            group_user = base_queryset.select_related("group").get(id=group_user_id)
        except GroupUser.DoesNotExist:
            raise GroupUserDoesNotExist(
                f"The group user with id {group_user_id} does " f"not exist."
            )

        return group_user

    def update_group_user(self, user, group_user, **kwargs):
        """
        Updates the values of an existing group user.

        :param user: The user on whose behalf the group user is deleted.
        :type user: User
        :param group_user: The group user that must be updated.
        :type group_user: GroupUser
        :return: The updated group user instance.
        :rtype: GroupUser
        """

        if not isinstance(group_user, GroupUser):
            raise ValueError("The group user is not an instance of GroupUser.")

        group_user.group.has_user(user, "ADMIN", raise_error=True)
        group_user = set_allowed_attrs(kwargs, ["permissions"], group_user)
        group_user.save()

        group_user_updated.send(self, group_user=group_user, user=user)

        return group_user

    def delete_group_user(self, user, group_user):
        """
        Deletes the provided group user.

        :param user: The user on whose behalf the group user is deleted.
        :type user: User
        :param group_user: The group user that must be deleted.
        :type group_user: GroupUser
        """

        if not isinstance(group_user, GroupUser):
            raise ValueError("The group user is not an instance of GroupUser.")

        group_user.group.has_user(user, "ADMIN", raise_error=True)
        group_user_id = group_user.id
        group_user.delete()

        group_user_deleted.send(
            self, group_user_id=group_user_id, group_user=group_user, user=user
        )

    def get_group_invitation_signer(self):
        """
        Returns the group invitation signer. This is for example used to create a url
        safe signed version of the invitation id which is used when sending a public
        accept link to the user.

        :return: The itsdangerous serializer.
        :rtype: URLSafeSerializer
        """

        return URLSafeSerializer(settings.SECRET_KEY, "group-invite")

    def send_group_invitation_email(self, invitation, base_url):
        """
        Sends out a group invitation email to the user based on the provided
        invitation instance.

        :param invitation: The invitation instance for which the email must be send.
        :type invitation: GroupInvitation
        :param base_url: The base url of the frontend, where the user can accept his
            invitation. The signed invitation id is appended to the URL (base_url +
            '/TOKEN'). Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :type base_url: str
        :raises BaseURLHostnameNotAllowed: When the host name of the base_url is not
            allowed.
        """

        parsed_base_url = urlparse(base_url)
        if parsed_base_url.hostname != settings.PUBLIC_WEB_FRONTEND_HOSTNAME:
            raise BaseURLHostnameNotAllowed(
                f"The hostname {parsed_base_url.netloc} is not allowed."
            )

        signer = self.get_group_invitation_signer()
        signed_invitation_id = signer.dumps(invitation.id)

        if not base_url.endswith("/"):
            base_url += "/"

        public_accept_url = urljoin(base_url, signed_invitation_id)

        email = GroupInvitationEmail(
            invitation, public_accept_url, to=[invitation.email]
        )
        email.send()

    def get_group_invitation_by_token(self, token, base_queryset=None):
        """
        Returns the group invitation instance if a valid signed token of the id is
        provided. It can be signed using the signer returned by the
        `get_group_invitation_signer` method.

        :param token: The signed invitation id of related to the group invitation
            that must be fetched. Must be signed using the signer returned by the
            `get_group_invitation_signer`.
        :type token: str
        :param base_queryset: The base queryset from where to select the invitation.
            This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises BadSignature: When the provided token has a bad signature.
        :raises GroupInvitationDoesNotExist: If the invitation does not exist.
        :return: The requested group invitation instance related to the provided token.
        :rtype: GroupInvitation
        """

        signer = self.get_group_invitation_signer()
        group_invitation_id = signer.loads(token)

        if base_queryset is None:
            base_queryset = GroupInvitation.objects

        try:
            group_invitation = base_queryset.select_related("group", "invited_by").get(
                id=group_invitation_id
            )
        except GroupInvitation.DoesNotExist:
            raise GroupInvitationDoesNotExist(
                f"The group invitation with id {group_invitation_id} does not exist."
            )

        return group_invitation

    def get_group_invitation(self, group_invitation_id, base_queryset=None):
        """
        Selects a group invitation with a given id from the database.

        :param group_invitation_id: The identifier of the invitation that must be
            returned.
        :type group_invitation_id: int
        :param base_queryset: The base queryset from where to select the invitation.
            This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises GroupInvitationDoesNotExist: If the invitation does not exist.
        :return: The requested field instance of the provided id.
        :rtype: GroupInvitation
        """

        if base_queryset is None:
            base_queryset = GroupInvitation.objects

        try:
            group_invitation = base_queryset.select_related("group", "invited_by").get(
                id=group_invitation_id
            )
        except GroupInvitation.DoesNotExist:
            raise GroupInvitationDoesNotExist(
                f"The group invitation with id {group_invitation_id} does not exist."
            )

        return group_invitation

    def create_group_invitation(
        self, user, group, email, permissions, base_url, message=""
    ):
        """
        Creates a new group invitation for the given email address and sends out an
        email containing the invitation.

        :param user: The user on whose behalf the invitation is created.
        :type user: User
        :param group: The group for which the user is invited.
        :type group: Group
        :param email: The email address of the person that is invited to the group.
            Can be an existing or not existing user.
        :type email: str
        :param permissions: The group permissions that the user will get once he has
            accepted the invitation.
        :type permissions: str
        :param base_url: The base url of the frontend, where the user can accept his
            invitation. The signed invitation id is appended to the URL (base_url +
            '/TOKEN'). Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :type base_url: str
        :param message: A custom message that will be included in the invitation email.
        :type message: Optional[str]
        :raises ValueError: If the provided permissions are not allowed.
        :raises UserInvalidGroupPermissionsError: If the user does not belong to the
            group or doesn't have right permissions in the group.
        :return: The created group invitation.
        :rtype: GroupInvitation
        """

        group.has_user(user, "ADMIN", raise_error=True)

        if permissions not in dict(GROUP_USER_PERMISSION_CHOICES):
            raise ValueError("Incorrect permissions provided.")

        email = normalize_email_address(email)

        if GroupUser.objects.filter(group=group, user__email=email).exists():
            raise GroupUserAlreadyExists(
                f"The user {email} is already part of the " f"group."
            )

        invitation, created = GroupInvitation.objects.update_or_create(
            group=group,
            email=email,
            defaults={
                "message": message,
                "permissions": permissions,
                "invited_by": user,
            },
        )

        self.send_group_invitation_email(invitation, base_url)

        return invitation

    def update_group_invitation(self, user, invitation, permissions):
        """
        Updates the permissions of an existing invitation if the user has ADMIN
        permissions to the related group.

        :param user: The user on whose behalf the invitation is updated.
        :type user: User
        :param invitation: The invitation that must be updated.
        :type invitation: GroupInvitation
        :param permissions: The new permissions of the invitation that the user must
            has after accepting.
        :type permissions: str
        :raises ValueError: If the provided permissions is not allowed.
        :raises UserInvalidGroupPermissionsError: If the user does not belong to the
            group or doesn't have right permissions in the group.
        :return: The updated group permissions instance.
        :rtype: GroupInvitation
        """

        invitation.group.has_user(user, "ADMIN", raise_error=True)

        if permissions not in dict(GROUP_USER_PERMISSION_CHOICES):
            raise ValueError("Incorrect permissions provided.")

        invitation.permissions = permissions
        invitation.save()

        return invitation

    def delete_group_invitation(self, user, invitation):
        """
        Deletes an existing group invitation if the user has ADMIN permissions to the
        related group.

        :param user: The user on whose behalf the invitation is deleted.
        :type user: User
        :param invitation: The invitation that must be deleted.
        :type invitation: GroupInvitation
        :raises UserInvalidGroupPermissionsError: If the user does not belong to the
            group or doesn't have right permissions in the group.
        """

        invitation.group.has_user(user, "ADMIN", raise_error=True)
        invitation.delete()

    def reject_group_invitation(self, user, invitation):
        """
        Rejects a group invitation by deleting the invitation so that can't be reused
        again. It can only be rejected if the invitation was addressed to the email
        address of the user.

        :param user: The user who wants to reject the invitation.
        :type user: User
        :param invitation: The invitation that must be rejected.
        :type invitation: GroupInvitation
        :raises GroupInvitationEmailMismatch: If the invitation email does not match
            the one of the user.
        """

        if user.username != invitation.email:
            raise GroupInvitationEmailMismatch(
                "The email address of the invitation does not match the one of the "
                "user."
            )

        invitation.delete()

    def accept_group_invitation(self, user, invitation):
        """
        Accepts a group invitation by adding the user to the correct group with the
        right permissions. It can only be accepted if the invitation was addressed to
        the email address of the user. Because the invitation has been accepted it
        can then be deleted. If the user is already a member of the group then the
        permissions are updated.

        :param user: The user who has accepted the invitation.
        :type: user: User
        :param invitation: The invitation that must be accepted.
        :type invitation: GroupInvitation
        :raises GroupInvitationEmailMismatch: If the invitation email does not match
            the one of the user.
        :return: The group user relationship related to the invite.
        :rtype: GroupUser
        """

        if user.username != invitation.email:
            raise GroupInvitationEmailMismatch(
                "The email address of the invitation does not match the one of the "
                "user."
            )

        group_user, created = GroupUser.objects.update_or_create(
            user=user,
            group=invitation.group,
            defaults={
                "order": GroupUser.get_last_order(user),
                "permissions": invitation.permissions,
            },
        )
        invitation.delete()

        return group_user

    def get_application(self, application_id, base_queryset=None):
        """
        Selects an application with a given id from the database.

        :param user: The user on whose behalf the application is requested.
        :type user: User
        :param application_id: The identifier of the application that must be returned.
        :type application_id: int
        :param base_queryset: The base queryset from where to select the application
            object. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises ApplicationDoesNotExist: When the application with the provided id
            does not exist.
        :return: The requested application instance of the provided id.
        :rtype: Application
        """

        if base_queryset is None:
            base_queryset = Application.objects

        try:
            application = base_queryset.select_related("group", "content_type").get(
                id=application_id
            )
        except Application.DoesNotExist:
            raise ApplicationDoesNotExist(
                f"The application with id {application_id} does not exist."
            )

        if TrashHandler.item_has_a_trashed_parent(application):
            raise ApplicationDoesNotExist(
                f"The application with id {application_id} does not exist."
            )

        return application

    def create_application(self, user, group, type_name, **kwargs):
        """
        Creates a new application based on the provided type.

        :param user: The user on whose behalf the application is created.
        :type user: User
        :param group: The group that the application instance belongs to.
        :type group: Group
        :param type_name: The type name of the application. ApplicationType can be
            registered via the ApplicationTypeRegistry.
        :type type_name: str
        :param kwargs: The fields that need to be set upon creation.
        :type kwargs: object
        :return: The created application instance.
        :rtype: Application
        """

        group.has_user(user, raise_error=True)

        # Figure out which model is used for the given application type.
        application_type = application_type_registry.get(type_name)
        model = application_type.model_class
        application_values = extract_allowed(kwargs, ["name"])
        last_order = model.get_last_order(group)

        instance = model.objects.create(
            group=group, order=last_order, **application_values
        )

        application_created.send(self, application=instance, user=user)

        return instance

    def update_application(self, user, application, **kwargs):
        """
        Updates an existing application instance.

        :param user: The user on whose behalf the application is updated.
        :type user: User
        :param application: The application instance that needs to be updated.
        :type application: Application
        :param kwargs: The fields that need to be updated.
        :type kwargs: object
        :raises ValueError: If one of the provided parameters is invalid.
        :return: The updated application instance.
        :rtype: Application
        """

        if not isinstance(application, Application):
            raise ValueError("The application is not an instance of Application.")

        application.group.has_user(user, raise_error=True)

        application = set_allowed_attrs(kwargs, ["name"], application)
        application.save()

        application_updated.send(self, application=application, user=user)

        return application

    def order_applications(self, user, group, order):
        """
        Updates the order of the applications in the given group. The order of the
        applications that are not in the `order` parameter set set to `0`.

        :param user: The user on whose behalf the tables are ordered.
        :type user: User
        :param group: The group of which the applications must be updated.
        :type group: Group
        :param order: A list containing the application ids in the desired order.
        :type order: list
        :raises ApplicationNotInGroup: If one of the applications ids in the order does
            not belong to the database.
        """

        group.has_user(user, raise_error=True)

        queryset = Application.objects.filter(group_id=group.id)
        application_ids = queryset.values_list("id", flat=True)

        for application_id in order:
            if application_id not in application_ids:
                raise ApplicationNotInGroup(application_id)

        Application.order_objects(queryset, order)
        applications_reordered.send(self, group=group, order=order, user=user)

    def delete_application(self, user, application):
        """
        Deletes an existing application instance if the user has access to the
        related group. The `application_deleted` signal is also called.

        :param user: The user on whose behalf the application is deleted.
        :type user: User
        :param application: The application instance that needs to be deleted.
        :type application: Application
        :raises ValueError: If one of the provided parameters is invalid.
        """

        if not isinstance(application, Application):
            raise ValueError("The application is not an instance of Application")

        application.group.has_user(user, raise_error=True)

        application_id = application.id
        TrashHandler.trash(user, application.group, application, application)

        application_deleted.send(
            self, application_id=application_id, application=application, user=user
        )

    def export_group_applications(self, group, files_buffer, storage=None):
        """
        Exports the applications of a group to a list. They can later be imported via
        the `import_applications_to_group` method. The result can be serialized to JSON.

        @TODO look into speed optimizations by streaming to a JSON file instead of
            generating the entire file in memory.

        :param group: The group of which the applications must be exported.
        :type group: Group
        :param files_buffer: A file buffer where the files must be written to in ZIP
            format.
        :type files_buffer: IOBase
        :param storage: The storage where the files can be loaded from.
        :type storage: Storage or None
        :return: A list containing the exported applications.
        :rtype: list
        """

        if not storage:
            storage = default_storage

        with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
            exported_applications = []
            applications = group.application_set.all()
            for a in applications:
                application = a.specific
                application_type = application_type_registry.get_by_model(application)
                exported_application = application_type.export_serialized(
                    application, files_zip, storage
                )
                exported_applications.append(exported_application)

        return exported_applications

    def import_applications_to_group(
        self, group, exported_applications, files_buffer, storage=None
    ):
        """
        Imports multiple exported applications into the given group. It is compatible
        with an export of the `export_group_applications` method.

        @TODO look into speed optimizations by streaming from a JSON file instead of
            loading the entire file into memory.

        :param group: The group that the applications must be imported to.
        :type group: Group
        :param exported_applications: A list containing the applications generated by
            the `export_group_applications` method.
        :type exported_applications: list
        :param files_buffer: A file buffer containing the exported files in ZIP format.
        :type files_buffer: IOBase
        :param storage: The storage where the files can be copied to.
        :type storage: Storage or None
        :return: The newly created applications based on the import and a dict
            containing a mapping of old ids to new ids.
        :rtype: list, dict
        """

        if not storage:
            storage = default_storage

        with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
            id_mapping = {}
            imported_applications = []
            for application in exported_applications:
                application_type = application_type_registry.get(application["type"])
                imported_application = application_type.import_serialized(
                    group, application, id_mapping, files_zip, storage
                )
                imported_applications.append(imported_application)

        return imported_applications, id_mapping

    def get_template(self, template_id, base_queryset=None):
        """
        Selects a template with the given id from the database.

        :param template_id: The identifier of the template that must be returned.
        :type template_id: int
        :param base_queryset: The base queryset from where to select the group
            object. This can for example be used to do a `prefetch_related`.
        :type base_queryset: Queryset
        :raises TemplateDoesNotExist: When the group with the provided id does not
            exist.
        :return: The requested template instance related to the provided id.
        :rtype: Template
        """

        if base_queryset is None:
            base_queryset = Template.objects

        try:
            template = base_queryset.get(id=template_id)
        except Template.DoesNotExist:
            raise TemplateDoesNotExist(
                f"The template with id {template_id} does not " f"exist."
            )

        return template

    def sync_templates(self, storage=None):
        """
        Synchronizes the JSON template files with the templates stored in the database.
        We need to have a copy in the database so that the user can live preview a
        template before installing. It will also make sure that the right categories
        exist and that old ones are deleted.

        If the template doesn't exist, a group can be created and we can import the
        export in that group. If the template already exists we check if the
        `export_hash` has changed, if so it means the export has changed. Because we
        don't have updating capability, we delete the old group and create a new one
        where we can import the export into.

        :param storage:
        :type storage:
        """

        installed_templates = (
            Template.objects.all()
            .prefetch_related("categories")
            .select_related("group")
        )
        installed_categories = list(TemplateCategory.objects.all())

        # Loop over the JSON template files in the directory to see which database
        # templates need to be created or updated.
        templates = list(Path(settings.APPLICATION_TEMPLATES_DIR).glob("*.json"))
        for template_file_path in templates:
            content = Path(template_file_path).read_text()
            parsed_json = json.loads(content)

            if "baserow_template_version" not in parsed_json:
                continue

            slug = ".".join(template_file_path.name.split(".")[:-1])
            installed_template = next(
                (t for t in installed_templates if t.slug == slug), None
            )
            hash_json = json.dumps(parsed_json["export"])
            export_hash = hashlib.sha256(hash_json.encode("utf-8")).hexdigest()
            keywords = (
                ",".join(parsed_json["keywords"]) if "keywords" in parsed_json else ""
            )

            # If the installed template and group exist, and if there is a hash
            # mismatch, we need to delete the old group and all the related
            # applications in it. This is because a new group will be created.
            if (
                installed_template
                and installed_template.group
                and installed_template.export_hash != export_hash
            ):
                TrashHandler.permanently_delete(installed_template.group)

            # If the installed template does not yet exist or if there is a export
            # hash mismatch, which means the group has already been deleted, we can
            # create a new group and import the exported applications into that group.
            if not installed_template or installed_template.export_hash != export_hash:
                # It is optionally possible for a template to have additional files.
                # They are stored in a ZIP file and are generated when the template
                # is exported. They for example contain file field files.
                try:
                    files_file_path = f"{os.path.splitext(template_file_path)[0]}.zip"
                    files_buffer = open(files_file_path, "rb")
                except FileNotFoundError:
                    # If the file is not found, we provide a BytesIO buffer to
                    # maintain backward compatibility and to not brake anything.
                    files_buffer = BytesIO()

                group = Group.objects.create(name=parsed_json["name"])
                self.import_applications_to_group(
                    group,
                    parsed_json["export"],
                    files_buffer=files_buffer,
                    storage=storage,
                )

                if files_buffer:
                    files_buffer.close()
            else:
                group = installed_template.group
                group.name = parsed_json["name"]
                group.save()

            kwargs = {
                "name": parsed_json["name"],
                "icon": parsed_json["icon"],
                "export_hash": export_hash,
                "keywords": keywords,
                "group": group,
            }

            if not installed_template:
                installed_template = Template.objects.create(slug=slug, **kwargs)
            else:
                # If the installed template already exists, we only need to update the
                # values to the latest version according to the JSON template.
                for key, value in kwargs.items():
                    setattr(installed_template, key, value)
                installed_template.save()

            # Loop over the categories related to the template and check which ones
            # already exist and which need to be created. Based on that we can create
            # a list of category ids that we can set for the template.
            template_category_ids = []
            for category_name in parsed_json["categories"]:
                installed_category = next(
                    (c for c in installed_categories if c.name == category_name), None
                )
                if not installed_category:
                    installed_category = TemplateCategory.objects.create(
                        name=category_name
                    )
                    installed_categories.append(installed_category)
                template_category_ids.append(installed_category.id)

            installed_template.categories.set(template_category_ids)

        # Delete all the installed templates that were installed, but don't exist in
        # the template directory anymore.
        slugs = [
            ".".join(template_file_path.name.split(".")[:-1])
            for template_file_path in templates
        ]
        for template in Template.objects.filter(~Q(slug__in=slugs)):
            TrashHandler.permanently_delete(template.group)
            template.delete()

        # Delete all the categories that don't have any templates anymore.
        TemplateCategory.objects.annotate(num_templates=Count("templates")).filter(
            num_templates=0
        ).delete()

    def install_template(self, user, group, template, storage=None):
        """
        Installs the exported applications of a template into the given group if the
        provided user has access to that group.

        :param user: The user on whose behalf the template installed.
        :type user: User
        :param group: The group where the template applications must be imported into.
        :type group: Group
        :param template: The template that must be installed.
        :type template: Template
        :param storage: The storage where the files can be copied to.
        :type storage: Storage or None
        :return: The imported applications.
        :rtype: list
        """

        group.has_user(user, raise_error=True)

        file_name = f"{template.slug}.json"
        template_path = Path(
            os.path.join(settings.APPLICATION_TEMPLATES_DIR, file_name)
        )

        if not template_path.exists():
            raise TemplateFileDoesNotExist(
                f"The template with file name {file_name} does not exist. You might "
                f"need to run the `sync_templates` management command."
            )

        content = template_path.read_text()
        parsed_json = json.loads(content)

        # It is optionally possible for a template to have additional files. They are
        # stored in a ZIP file and are generated when the template is exported. They
        # for example contain file field files.
        try:
            files_path = f"{os.path.splitext(template_path)[0]}.zip"
            files_buffer = open(files_path, "rb")
        except FileNotFoundError:
            # If the file is not found, we provide a BytesIO buffer to
            # maintain backward compatibility and to not brake anything.
            files_buffer = BytesIO()

        applications, id_mapping = self.import_applications_to_group(
            group, parsed_json["export"], files_buffer=files_buffer, storage=storage
        )

        if files_buffer:
            files_buffer.close()

        # Because a user has initiated the creation of applications, we need to
        # call the `application_created` signal for each created application.
        for application in applications:
            application_type = application_type_registry.get_by_model(application)
            application_created.send(
                self,
                application=application,
                user=user,
                type_name=application_type.type,
            )

        return applications, id_mapping
