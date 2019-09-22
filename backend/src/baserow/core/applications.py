from django.core.exceptions import ImproperlyConfigured

from .exceptions import ApplicationAlreadyRegistered, ApplicationTypeDoesNotExist


class Application(object):
    """
    This abstract class represents a custom application that can be added to the
    application registry. It must be extended so customisation can be done. Each
    application will have his own model that must extend the Application model, this is
    needed so that the user can set custom settings per application instance he has
    created.

    Example:
        from baserow.core.models import Application as ApplicationModel
        from baserow.core.applications import Application, registry

        class ExampleApplicationModel(ApplicationModel):
            pass

        class ExampleApplication(Application):
            type = 'a-unique-type-name'
            instance_model = ExampleApplicationModel

        registry.register(ExampleApplication())

    """

    type = None
    instance_model = None

    def __init__(self):
        if not self.type:
            raise ImproperlyConfigured('The type of an application must be set.')

        if not self.instance_model:
            raise ImproperlyConfigured('The instance model of an application must be '
                                       'set.')

    def get_api_urls(self):
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


class ApplicationRegistry(object):
    """
    With the application registry it is possible to register new applications.  An
    application is an abstraction made specifically for Baserow. If added to the
    registry a user can create new instances of that application via the ap and register
    api related urls.
    """

    def __init__(self):
        self.registry = {}

    def get(self, type):
        """
        Returns a registered application their type name.

        :param type: The type name of the registered application.
        :param type: str
        :return: The requested application.
        :rtype: Application
        """

        if type not in self.registry:
            raise ApplicationTypeDoesNotExist(f'The application type {type} does not '
                                              f'exist.')

        return self.registry[type]

    def get_by_model(self, instance):
        """Returns the application instance of a model or model instance.

        :param instance: The modal that must be the applications model_instance.
        :type instance: Model or an instance of model.
        :return: The registered application instance.
        :rtype: Application
        """

        for value in self.registry.values():
            if value.instance_model == instance \
               or isinstance(instance, value.instance_model):
                return value

        raise ApplicationTypeDoesNotExist(f'The application with model instance '
                                          f'{instance} does not exist. ')

    def get_types(self):
        """
        Returns a list of available type names.

        :return: A list of available types.
        :rtype: List
        """

        return list(self.registry.keys())

    def register(self, application):
        """
        Registers a new application in the registry.

        :param application: The application that needs to be registered.
        :type application:
        """

        if not isinstance(application, Application):
            raise ValueError('The application must be an instance of Application.')

        if application.type in self.registry:
            raise ApplicationAlreadyRegistered(
                f'The application with type {application.type} is already registered.')

        self.registry[application.type] = application

    def unregister(self, value):
        """
        Removes a registered application from the registry. An application instance or
        type name can be provided as value.

        :param value: The application instance or type name.
        :type value: Application or str
        """

        if isinstance(value, Application):
            for type, application in self.registry.items():
                if application == value:
                    value = type

        if isinstance(value, str):
            del self.registry[value]
        else:
            raise ValueError('The value must either be an application instance or type '
                             'name')

    @property
    def api_urls(self):
        """
        Returns a list of all the api urls that are in the registered applications.

        :return: The api urls of the registered applications.
        :rtype: list
        """

        api_urls = []
        for application in self.registry.values():
            api_urls += application.get_api_urls()
        return api_urls


# A default application is created here, this is the one that is used throughout the
# whole Baserow application. To add a new application use this registry.
registry = ApplicationRegistry()
