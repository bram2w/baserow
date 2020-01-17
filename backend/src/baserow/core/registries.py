from .registry import Instance, Registry, ModelInstanceMixin, ModelRegistryMixin
from .exceptions import ApplicationTypeAlreadyRegistered, ApplicationTypeDoesNotExist


class ApplicationType(ModelInstanceMixin, Instance):
    """
    This abstract class represents a custom application that can be added to the
    application registry. It must be extended so customisation can be done. Each
    application will have his own model that must extend the Application model, this is
    needed so that the user can set custom settings per application instance he has
    created.

    Example:
        from baserow.core.models import Application
        from baserow.core.applications import ApplicationType, application_type_registry

        class ExampleApplicationModel(Application):
            pass

        class ExampleApplication(ApplicationType):
            type = 'a-unique-type-name'
            model_class = ExampleApplicationModel

        application_type_registry.register(ExampleApplication())

    """

    instance_serializer_class = None
    """This serializer that is used to serialize the instance model."""

    def get_api_v0_urls(self):
        """
        If needed custom api related urls to the application can be added here.

        Example:

            def get_api_urls(self):
                from . import api_urls

                return [
                    path('some-application/', include(api_urls, namespace=self.type)),
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


class ApplicationTypeRegistry(ModelRegistryMixin, Registry):
    """
    With the application registry it is possible to register new applications. An
    application is an abstraction made specifically for Baserow. If added to the
    registry a user can create new instances of that application via the app and
    register api related urls.
    """

    name = 'application'
    does_not_exist_exception_class = ApplicationTypeDoesNotExist
    already_registered_exception_class = ApplicationTypeAlreadyRegistered

    @property
    def api_urls(self):
        """
        Returns a list of all the api urls that are in the registered applications.

        :return: The api urls of the registered applications.
        :rtype: list
        """

        api_urls = []
        for application in self.registry.values():
            api_urls += application.get_api_v0_urls()
        return api_urls


# A default application registry is created here, this is the one that is used
# throughout the whole Baserow application. To add a new application use this registry.
application_type_registry = ApplicationTypeRegistry()
