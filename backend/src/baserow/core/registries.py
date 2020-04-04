from .registry import (
    Instance, Registry, ModelInstanceMixin, ModelRegistryMixin, APIUrlsRegistryMixin,
    APIUrlsInstanceMixin
)
from .exceptions import ApplicationTypeAlreadyRegistered, ApplicationTypeDoesNotExist


class ApplicationType(APIUrlsInstanceMixin, ModelInstanceMixin, Instance):
    """
    This abstract class represents a custom application that can be added to the
    application registry. It must be extended so customisation can be done. Each
    application will have his own model that must extend the Application model, this is
    needed so that the user can set custom settings per application instance he has
    created.

    The added API urls will be available under the namespace 'api_v0'. So if a url
    with name 'example' is returned by the method it will available under
    reverse('api_v0:example').

    Example:
        from baserow.core.models import Application
        from baserow.core.applications import ApplicationType, application_type_registry

        class ExampleApplicationModel(Application):
            pass

        class ExampleApplication(ApplicationType):
            type = 'a-unique-type-name'
            model_class = ExampleApplicationModel

            def get_api_v0_urls(self):
                return [
                    path('application-type/', include(api_urls, namespace=self.type)),
                ]

        application_type_registry.register(ExampleApplication())

    """

    instance_serializer_class = None
    """This serializer that is used to serialize the instance model."""

    def user_created(self, user, group):
        """
        A hook that is called after a new user has been created. This is the place to
        create some data the user can start with. A group has already been created
        for the user to that one is passed as a parameter.

        :param user: The newly created user.
        :param group: The newly created group for the user.
        """

    def pre_delete(self, application):
        """
        A hook that is called before the application instance is deleted.

        :param application: The application model instance that needs to be deleted.
        :type application: Application
        """


class ApplicationTypeRegistry(APIUrlsRegistryMixin, ModelRegistryMixin, Registry):
    """
    With the application registry it is possible to register new applications. An
    application is an abstraction made specifically for Baserow. If added to the
    registry a user can create new instances of that application via the app and
    register api related urls.
    """

    name = 'application'
    does_not_exist_exception_class = ApplicationTypeDoesNotExist
    already_registered_exception_class = ApplicationTypeAlreadyRegistered


# A default application registry is created here, this is the one that is used
# throughout the whole Baserow application. To add a new application use this registry.
application_type_registry = ApplicationTypeRegistry()
