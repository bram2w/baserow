import abc
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union
from xmlrpc.client import Boolean
from zipfile import ZipFile

from django.core.files.storage import Storage
from django.db.models import QuerySet
from django.db.transaction import Atomic

from baserow.contrib.database.constants import IMPORT_SERIALIZED_IMPORTING
from baserow.core.utils import ChildProgressBuilder

from .exceptions import (
    ApplicationTypeAlreadyRegistered,
    ApplicationTypeDoesNotExist,
    AuthenticationProviderTypeAlreadyRegistered,
    AuthenticationProviderTypeDoesNotExist,
    ObjectScopeTypeAlreadyRegistered,
    ObjectScopeTypeDoesNotExist,
    OperationTypeAlreadyRegistered,
    OperationTypeDoesNotExist,
    PermissionDenied,
    PermissionManagerTypeAlreadyRegistered,
    PermissionManagerTypeDoesNotExist,
)
from .export_serialized import CoreExportSerializedStructure
from .registry import (
    APIUrlsInstanceMixin,
    APIUrlsRegistryMixin,
    ImportExportMixin,
    Instance,
    MapAPIExceptionsInstanceMixin,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)
from .types import ContextObject, ScopeObject

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from .models import Application, Group


class Plugin(APIUrlsInstanceMixin, Instance):
    """
    This abstract class represents a custom plugin that can be added to the plugin
    registry. It must be extended so customisation can be done. Each plugin can register
    urls to the root and to the api.

    The added API urls will be available under the namespace 'api'. So if a url
    with name 'example' is returned by the method it will available under
    reverse('api:example').

    Example:
        from django.http import HttpResponse
        from baserow.core.registries import Plugin, plugin_registry

        def page_1(request):
            return HttpResponse('Page 2')

        class ExamplePlugin(Plugin):
            type = 'a-unique-type-name'

            # Will be added to the root.
            def get_urls(self):
                return [
                    url(r'^page-1$', page_1, name='page_1')
                ]

            # Will be added to the API.
            def get_api_urls(self):
                return [
                    path('application-type/', include(api_urls, namespace=self.type)),
                ]

        plugin_registry.register(ExamplePlugin())
    """

    def get_urls(self):
        """
        If needed root urls related to the plugin can be added here.

        Example:

            def get_urls(self):
                from . import api_urls

                return [
                    path('some-url/', include(api_urls, namespace=self.type)),
                ]

            # api_urls.py
            from django.urls import re_path

            urlpatterns = [
                url(r'some-view^$', SomeView.as_view(), name='some_view'),
            ]

        :return: A list containing the urls.
        :rtype: list
        """

        return []

    def user_created(self, user, group, group_invitation, template):
        """
        A hook that is called after a new user has been created. This is the place to
        create some data the user can start with. A group has already been created
        for the user to that one is passed as a parameter.

        :param user: The newly created user.
        :type user: User
        :param group: The newly created group for the user.
        :type group: Group
        :param group_invitation: Is provided if the user has signed up using a valid
            group invitation token.
        :type group_invitation: GroupInvitation
        :param template: The template that is installed right after creating the
            account. Is `None` if the template was not created.
        :type template: Template or None
        """

    def user_signed_in(self, user):
        """
        A hook that is called after an existing user has signed in.

        :param user: The user that just signed in.
        :type user: User
        """


class PluginRegistry(APIUrlsRegistryMixin, Registry):
    """
    With the plugin registry it is possible to register new plugins. A plugin is an
    abstraction made specifically for Baserow. It allows a plugin developer to
    register extra api and root urls.
    """

    name = "plugin"

    @property
    def urls(self):
        """
        Returns a list of all the urls that are in the registered instances. They
        are going to be added to the root url config.

        :return: The urls of the registered instances.
        :rtype: list
        """

        urls = []
        for types in self.registry.values():
            urls += types.get_urls()
        return urls


class ApplicationType(
    APIUrlsInstanceMixin, ModelInstanceMixin, ImportExportMixin, Instance
):
    """
    This abstract class represents a custom application that can be added to the
    application registry. It must be extended so customisation can be done. Each
    application will have his own model that must extend the Application model, this is
    needed so that the user can set custom settings per application instance he has
    created.

    The added API urls will be available under the namespace 'api'. So if a url
    with name 'example' is returned by the method it will available under
    reverse('api:example').

    Example:
        from baserow.core.models import Application
        from baserow.core.registries import ApplicationType, application_type_registry

        class ExampleApplicationModel(Application):
            pass

        class ExampleApplication(ApplicationType):
            type = 'a-unique-type-name'
            model_class = ExampleApplicationModel

            def get_api_urls(self):
                return [
                    path('application-type/', include(api_urls, namespace=self.type)),
                ]

        application_type_registry.register(ExampleApplication())

    """

    instance_serializer_class = None
    """This serializer that is used to serialize the instance model."""

    supports_snapshots = True

    def pre_delete(self, application):
        """
        A hook that is called before the application instance is deleted.

        :param application: The application model instance that needs to be deleted.
        :type application: Application
        """

    def export_safe_transaction_context(self, application: "Application") -> Atomic:
        """
        Should return an Atomic context (such as transaction.atomic or
        baserow.contrib.database.db.atomic.read_repeatable_single_database_atomic_transaction)
        which can be used to safely run a database transaction to export an application
        of this type.

        :param application: The application that we are about to export.
        :return: An Atomic context object that will be used to open a transaction safely
            to export an application of this type.
        """

        raise NotImplementedError(
            "Must be implemented by the specific application type"
        )

    def export_serialized(
        self,
        application: "Application",
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ):
        """
        Exports the application to a serialized dict that can be imported by the
        `import_serialized` method. The dict is JSON serializable.

        :param application: The application that must be exported.
        :type application: Application
        :param files_zip: A zip file buffer where the files related to the template
            must be copied into.
        :type files_zip: ZipFile
        :param storage: The storage where the files can be loaded from.
        :type storage: Storage or None
        :return: The exported and serialized application.
        :rtype: dict
        """

        return CoreExportSerializedStructure.application(
            id=application.id,
            name=application.name,
            order=application.order,
            type=self.type,
        )

    def import_serialized(
        self,
        group: "Group",
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> "Application":
        """
        Imports the exported serialized application by the `export_serialized` as a new
        application to a group.

        :param group: The group that the application must be added to.
        :param serialized_values: The exported serialized values by the
            `export_serialized` method.
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :param files_zip: A zip file buffer where files related to the template can
            be extracted from.
        :param storage: The storage where the files can be copied to.
        :param progress_builder: If provided will be used to build a child progress bar
            and report on this methods progress to the parent of the progress_builder.
        :return: The newly created application.
        """

        if "import_group_id" not in id_mapping and group is not None:
            id_mapping["import_group_id"] = group.id

        if "applications" not in id_mapping:
            id_mapping["applications"] = {}

        serialized_copy = serialized_values.copy()
        application_id = serialized_copy.pop("id")
        serialized_copy.pop("type")
        application = self.model_class.objects.create(group=group, **serialized_copy)
        id_mapping["applications"][application_id] = application.id

        progress = ChildProgressBuilder.build(progress_builder, child_total=1)
        progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        return application


class ApplicationTypeRegistry(APIUrlsRegistryMixin, ModelRegistryMixin, Registry):
    """
    With the application registry it is possible to register new applications. An
    application is an abstraction made specifically for Baserow. If added to the
    registry a user can create new instances of that application via the app and
    register api related urls.
    """

    name = "application"
    does_not_exist_exception_class = ApplicationTypeDoesNotExist
    already_registered_exception_class = ApplicationTypeAlreadyRegistered


class AuthenticationProviderTypeRegistry(
    MapAPIExceptionsInstanceMixin, APIUrlsRegistryMixin, ModelRegistryMixin, Registry
):
    """
    With the authentication provider registry it is possible to register new
    authentication providers. An authentication provider is an abstraction made
    specifically for Baserow. If added to the registry a user can use that
    authentication provider to login.
    """

    name = "authentication_provider"
    does_not_exist_exception_class = AuthenticationProviderTypeDoesNotExist
    already_registered_exception_class = AuthenticationProviderTypeAlreadyRegistered

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default = None

    def register_default(self, instance):
        super().register(instance)
        self._default = instance

    def get_default_provider(self):
        provider, _ = self._default.model_class.objects.get_or_create()
        return provider

    def get_default(self):
        return self._default

    def get_all_available_login_options(self):
        login_options = {}
        for provider in self.get_all():
            provider_login_options = provider.get_login_options()
            if provider_login_options:
                login_options[provider.type] = provider_login_options
        return login_options


class PermissionManagerType(Instance):
    """
    A permission manager is responsible to permit or disallow a specific operation
    according to the given context.

    A permission manager is also responsible to generate the data sent to the
    frontend to make it check the permission.

    And finally, a permission manager can filter the list querysets
    to remove disallowed objects from this list.

    See each PermissionManager method and `CoreHandler` methods for more details.
    """

    def check_permissions(
        self,
        actor: "AbstractUser",
        operation_name: str,
        group: Optional["Group"] = None,
        context: Optional[Any] = None,
        include_trash: Boolean = False,
    ) -> Optional[Boolean]:
        """
        This method is called each time a permission on an operation is checked by the
        `CoreHandler().check_permissions()` method if the current permission manager is
        listed in the `settings.PERMISSION_MANAGERS` list.

        It should:
            - return `True` if the operation is permitted given the other parameters
            - raise a `PermissionDenied` exception if the operation is disallowed
            - return `None` if the condition required by the permission manager are not
              met.

        By default, this method raises a PermissionDenied exception.

        :param actor: The actor who wants to execute the operation. Generally a `User`,
            but can be a `Token`.
        :param operation_name: The operation name the actor wants to execute.
        :param group: The optional group in which  the operation takes place.
        :param context: The optional object affected by the operation. For instance
            if you are updating a `Table` object, the context is this `Table` object.
        :param include_trash: If true then also checks if the given group has been
            trashed instead of raising a DoesNotExist exception.
        :raise PermissionDenied: If the operation is disallowed a PermissionDenied is
            raised.
        :return: `True` if the operation is permitted, None if the permission manager
            can't decide.
        """

        raise PermissionDenied()

    def get_permissions_object(
        self, actor: "AbstractUser", group: Optional["Group"] = None
    ) -> Any:
        """
        This method should return the data necessary to easily check a permission from
        a client. This object can be used for instance from the frontend to hide or
        show UI element accordingly to the user permissions.
        The data set returned must contain all the necessary information to prevent and
        the client shouldn't have to get more data to decide.

        This method is called when the `CoreHandler().get_permissions()` is called,
        if the permission manager is listed in the `settings.PERMISSION_MANAGERS`.
        It can return `None` if this permission manager is not relevant for the given
        actor/group for some reason.

        By default this method returns None.

        :param actor: The actor whom we want to compute the permission object for.
        :param group: The optional group into which we want to compute the permission
            object.
        :return: The permission object or None.
        """

        return None

    def filter_queryset(
        self,
        actor: "AbstractUser",
        operation_name: str,
        queryset: QuerySet,
        group: Optional["Group"] = None,
        context: Optional[Any] = None,
    ) -> QuerySet:
        """
        This method allows a permission manager to filter a given queryset accordingly
        to the actor permissions in the specified context. The
        `CoreHandler().filter_queryset()` method calls each permission manager listed in
        `settings.PERMISSION_MANAGERS` to successively filter the given queryset.

        :param actor: The actor whom we want to filter the queryset for.
            Generally a `User` but can be a Token.
        :param operation: The operation name for which we want to filter the queryset
            for.
        :param group: An optional group into which the operation takes place.
        :param context: An optional context object related to the current operation.
        :return: The queryset potentially filtered.
        """

        return queryset

    def get_roles(self) -> List:
        """
        Get all the roles available for your permissions system
        """

        return []


class PermissionManagerTypeRegistry(Registry[PermissionManagerType]):
    """
    This registry contains all the permission manager used to handle permissions in
    Baserow. A permission manager must then be listed in the
    `settings.PERMISSION_MANAGERS` variable to be used by the `CoreHandler` methods.
    """

    name = "permission_manager"

    does_not_exist_exception_class = PermissionManagerTypeDoesNotExist
    already_registered_exception_class = PermissionManagerTypeAlreadyRegistered


class ObjectScopeType(Instance, ModelInstanceMixin):
    """
    This type describe an object scope in Baserow. This is useful if you need to know
    the object hierarchy. This hierarchy is used by the permission system, for example,
    to determine if a context object is included by a given scope.
    It can also be used to list all context object of a scope included by another scope.

    An `ObjectScopeType` must be registered for each object that can be a scope or a
    context.
    """

    def get_parent_scope(self) -> Optional["ObjectScopeType"]:
        """
        Returns the parent scope of the current scope.

        :return: the parent `ObjectScopeType` or `None` if it's a root scope.
        """

        return None

    def get_parent(self, context: ContextObject) -> Optional[ContextObject]:
        """
        Returns the parent object of the given context which belongs to the current
        scope.

        :param context: The context object which we want the parent for. This object
            must belong to the current scope.
        :return: the parent object or `None` if it's a root object.
        """

        return None

    def get_all_context_objects_in_scope(self, scope: ScopeObject) -> Iterable:
        """
        Returns the list of context object belonging to the current scope that are
        included in the scope object given in parameter.

        :param scope: The scope into which we want the context objects for.
        :return: An iterable containing the context objects for the given scope.
        """

        raise NotImplementedError(
            f"Must be implemented by the specific type <{self.type}>"
        )


class ObjectScopeTypeRegistry(Registry[ObjectScopeType], ModelRegistryMixin):
    """
    This registry contains all `ObjectScopeType`. It also proposes a set of methods
    useful to go through the full object/scope hierarchy.
    """

    name = "object_scope"

    def scope_includes_context(
        self,
        scope: ScopeObject,
        context: ContextObject,
        scope_type: Optional[ObjectScopeType] = None,
    ) -> Boolean:
        """
        Checks whether a scope object includes the given context.

        :param scope: The scope object.
        :param context: A context object.
        :scope_type: An optional `ObjectScopeType` that is used mainly for performance
            reason.
        :return: True if the context is included in the given scope object.
        """

        if context is None:
            return False

        scope_type = scope_type or self.get_by_model(scope)

        context_scope_type = self.get_by_model(context)

        if scope_type == context_scope_type:
            return scope.id == context.id
        else:
            return self.scope_includes_context(
                scope, context_scope_type.get_parent(context), scope_type=scope_type
            )

    def scope_includes_scope(
        self,
        parent_scope: Union[ScopeObject, ObjectScopeType],
        child_scope: Union[ScopeObject, ObjectScopeType],
    ) -> Boolean:
        """
        Checks whether the parent_scope includes the child_scope.

        :param parent_scope: The scope object or type that should includes the other
            scope.
        :param child_scope: The scope object or type that should be included by the
            other scope.
        :return: True if the parent_scope includes the children scope. False otherwise.
        """

        if child_scope is None:
            return False

        parent_scope_type = (
            object_scope_type_registry.get_by_model(parent_scope)
            if not isinstance(parent_scope, ObjectScopeType)
            else parent_scope
        )
        child_scope_type = (
            object_scope_type_registry.get_by_model(child_scope)
            if not isinstance(child_scope, ObjectScopeType)
            else child_scope
        )

        if parent_scope_type == child_scope_type:
            return True
        else:
            return self.scope_includes_scope(
                parent_scope_type,
                child_scope_type.get_parent_scope(),
            )

    # TODO change
    does_not_exist_exception_class = ObjectScopeTypeDoesNotExist
    already_registered_exception_class = ObjectScopeTypeAlreadyRegistered


class OperationType(abc.ABC, Instance):
    """
    An `OperationType` represent an `Operation` an actor can do on a `ContextObject`.

    An OperationType must define a context_scope_name which is the name of the
    `ObjectScopeType` matching the context scope type related to the `ContextObject`

    Optionally an object_scope_name can be define to for list operations to express
    the scope of listed objects sometimes necessary for queryset filtering by the
    permission manager.
    """

    @classmethod
    @property
    @abc.abstractmethod
    def type(cls) -> str:
        """
        Should be a unique lowercase string used to identify this type.
        """

        pass

    @classmethod
    @property
    @abc.abstractmethod
    def context_scope_name(cls) -> str:
        """
        An operation is executed on a context in Baserow. For example the list_fields
        operation is executed on a table as it's context. Provide the context_scope_name
        here which matches a ObjectScopeType in the object_scope_type_registry.
        """

        pass

    object_scope_name: Optional[str] = None

    @cached_property
    def context_scope(self) -> ObjectScopeType:
        """
        Returns the `ObjectScopeType` related to the context_scope_name.
        """

        return object_scope_type_registry.get(self.context_scope_name)

    @cached_property
    def object_scope(self):
        """
        Returns the `ObjectScopeType` related to the object_scope_name. If the
        object_scope_name is not defined, then the object_scope is the same as the
        context_scope.
        """

        if self.object_scope_name:
            return object_scope_type_registry.get(self.object_scope_name)
        else:
            return self.context_scope


class OperationTypeRegistry(Registry[OperationType]):
    """
    Contains all the registered operation. For each registered operation, an Operation
    object is created in the database.
    """

    name = "operation"

    # TODO change
    does_not_exist_exception_class = OperationTypeDoesNotExist
    already_registered_exception_class = OperationTypeAlreadyRegistered


# A default plugin and application registry is created here, this is the one that is
# used throughout the whole Baserow application. To add a new plugin or application use
# these registries.
plugin_registry = PluginRegistry()
application_type_registry = ApplicationTypeRegistry()
auth_provider_type_registry = AuthenticationProviderTypeRegistry()

permission_manager_type_registry: PermissionManagerTypeRegistry = (
    PermissionManagerTypeRegistry()
)
object_scope_type_registry: ObjectScopeTypeRegistry = ObjectScopeTypeRegistry()
operation_type_registry: OperationTypeRegistry = OperationTypeRegistry()
