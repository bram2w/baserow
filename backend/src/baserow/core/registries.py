from .registry import (
    Instance,
    Registry,
    ModelInstanceMixin,
    ModelRegistryMixin,
    APIUrlsRegistryMixin,
    APIUrlsInstanceMixin,
    ImportExportMixin,
)
from .exceptions import ApplicationTypeAlreadyRegistered, ApplicationTypeDoesNotExist


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
            from django.conf.urls import url

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

    def pre_delete(self, application):
        """
        A hook that is called before the application instance is deleted.

        :param application: The application model instance that needs to be deleted.
        :type application: Application
        """

    def export_serialized(self, application):
        """
        Exports the application to a serialized dict that can be imported by the
        `import_serialized` method. The dict is JSON serializable.

        :param application: The application that must be exported.
        :type application: Application
        :return: The exported and serialized application.
        :rtype: dict
        """

        return {
            "id": application.id,
            "name": application.name,
            "order": application.order,
            "type": self.type,
        }

    def import_serialized(self, group, serialized_values, id_mapping):
        """
        Imports the exported serialized application by the `export_serialized` as a new
        application to a group.

        :param group: The group that the application must be added to.
        :type group: Group
        :param serialized_values: The exported serialized values by the
            `export_serialized` method.
        :type serialized_values: dict`
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :type id_mapping: dict
        :return: The newly created application.
        :rtype: Application
        """

        if "applications" not in id_mapping:
            id_mapping["applications"] = {}

        serialized_copy = serialized_values.copy()
        application_id = serialized_copy.pop("id")
        serialized_copy.pop("type")
        application = self.model_class.objects.create(group=group, **serialized_copy)
        id_mapping["applications"][application_id] = application.id

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


# A default plugin and application registry is created here, this is the one that is
# used throughout the whole Baserow application. To add a new plugin or application use
# these registries.
plugin_registry = PluginRegistry()
application_type_registry = ApplicationTypeRegistry()
