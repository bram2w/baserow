import contextlib
import typing
from functools import lru_cache
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    ValuesView,
)

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from rest_framework import serializers

from baserow.api.utils import ExceptionMappingType, get_serializer_class, map_exceptions

from .exceptions import InstanceTypeAlreadyRegistered, InstanceTypeDoesNotExist

if typing.TYPE_CHECKING:
    from django.contrib.contenttypes.models import ContentType


T = TypeVar("T")


class Instance(object):
    """
    This abstract class represents a custom instance that can be added to the registry.
    It must be extended so properties and methods can be added.
    """

    type: str
    """A unique string that identifies the instance."""

    def __init__(self):
        if not self.type:
            raise ImproperlyConfigured("The type of an instance must be set.")


class ModelInstanceMixin(Generic[T]):
    """
    This mixin introduces a model_class that will be related to the instance. It is to
    be used in combination with a registry that extends the ModelRegistryMixin.
    """

    model_class: Type[T]

    def __init__(self):
        if not self.model_class:
            raise ImproperlyConfigured("The model_class of an instance must be set.")

    def get_content_type(self) -> "ContentType":
        """
        Returns the content_type related to the model_class.
        """

        from django.contrib.contenttypes.models import ContentType

        return ContentType.objects.get_for_model(self.model_class)

    def get_object_for_this_type(self, **kwargs) -> T:
        """
        Returns the object given the filters in parameter.
        """

        return self.get_content_type().get_object_for_this_type(**kwargs)

    def get_all_objects_for_this_type(self, **kwargs) -> models.QuerySet:
        """
        Returns a queryset to get the objects given the filters in parameter.
        """

        return self.get_content_type().get_all_objects_for_this_type(**kwargs)


class CustomFieldsInstanceMixin:
    """
    If an instance can have custom fields per type, they can be defined here.
    """

    allowed_fields = []
    """The field names that are allowed to set when creating and updating"""

    serializer_field_names = []
    """The field names that must be added to the serializer."""

    request_serializer_field_names = None
    """
    The field names that must be added to the request serializer if different from
    the `serializer_field_names`.
    """

    serializer_field_overrides = {}
    """The fields that must be added to the serializer."""

    request_serializer_field_overrides = None
    """
    The fields that must be added to the request serializer if different from the
    `serializer_field_overrides` property.
    """

    serializer_mixins = []
    """
    The serializer mixins that must be added to the serializer. This property is
    useful if you want to add some custom SerializerMethodField for example.
    """

    serializer_extra_kwargs = None
    """
    The extra kwargs that must be added to the serializer fields. This property is
    useful if you want to add some custom `write_only` field for example.
    """

    def __init__(self):
        """
        :raises ValueError: If the object does not have a `model_class` attribute.
        """

        model_class = getattr(self, "model_class")
        if not model_class:
            raise ValueError(
                "Attribute model_class must be set, maybe you forgot to "
                "extend the ModelInstanceMixin?"
            )

    def get_serializer_class(
        self, *args, request_serializer: bool = False, **kwargs
    ) -> serializers.ModelSerializer:
        """
        Returns a model serializer class based on this type field names and overrides.

        :raises ValueError: If the object does not have a `model_class` attribute.
        :return: The generated model serializer class.
        """

        if request_serializer and self.request_serializer_field_overrides is not None:
            field_overrides = self.request_serializer_field_overrides
        else:
            field_overrides = self.serializer_field_overrides

        if request_serializer and self.request_serializer_field_names is not None:
            field_names = self.request_serializer_field_names
        else:
            field_names = self.serializer_field_names

        mixins = [] if request_serializer else self.serializer_mixins

        return get_serializer_class(
            self.model_class,
            field_names,
            field_overrides=field_overrides,
            base_mixins=mixins,
            meta_extra_kwargs=self.serializer_extra_kwargs,
            *args,
            **kwargs,
        )

    def get_serializer(
        self,
        model_instance: models.Model,
        base_class: Optional[serializers.ModelSerializer] = None,
        context: Optional[Dict[str, Any]] = None,
        request: bool = False,
        **kwargs: Dict[str, Any],
    ) -> serializers.ModelSerializer:
        """
        Returns an instantiated model serializer based on this type field names and
        overrides. The provided model instance will be used instantiate the serializer.

        :param model_instance: The instance for which the serializer must be generated.
        :param base_class: The base serializer class that must be extended. For example
            common fields could be stored here.
        :param context: Extra context arguments to pass to the serializers context.
        :param request: True if you want the request serializer.
        :param kwargs: The kwargs are used to initialize the serializer class.
        :return: The instantiated generated model serializer.
        """

        if context is None:
            context = {}

        model_instance = model_instance.specific

        serializer_class = self.get_serializer_class(
            base_class=base_class, request_serializer=request
        )

        return serializer_class(model_instance, context=context, **kwargs)


class APIUrlsInstanceMixin:
    def get_api_urls(self):
        """
        If needed custom api related urls to the instance can be added here.

        Example:

            def get_api_urls(self):
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


class MapAPIExceptionsInstanceMixin:
    """
    Example:
        class ExampleInstance(MapAPIExceptionsInstanceMixin, Instance):
            type = 'example'
            api_exceptions_map = {
                SomeSpecificException: 'API_ERROR'
            }

        # If the exception is raised while inside the with map_api_exceptions() the
        # following HTTP response can be expected.

        instance = ExampleInstance()
        with instance.map_api_exceptions():
            raise SomeSpecificException('Reason')

        HTTP/1.1 400
        {
            "error": "API_ERROR",
            "detail": ""
        }
    """

    api_exceptions_map: ExceptionMappingType = {}

    @contextlib.contextmanager
    def map_api_exceptions(self):
        """
        The map_api_exceptions method can be used to map uncaught exceptions to
        certain api error responses. These API exceptions should be defined in the
        api_exceptions_map.
        """

        with map_exceptions(self.api_exceptions_map):
            yield


class ImportExportMixin:
    def export_serialized(self, instance):
        """
        Should return with a serialized version of the provided instance. It must be
        JSON serializable and it must be possible to the import via the
        `import_serialized` method.

        :param instance: The instance that must be serialized and exported. Could be
            any object type because it depends on the type instance that uses this
            mixin.
        :type instance: Object
        :return: Serialized version of the instance.
        :rtype: dict
        """

        raise NotImplementedError("The export_serialized method must be implemented.")

    def import_serialized(self, parent, serialized_values, id_mapping):
        """
        Should import and create the correct instances in the database based on the
        serialized values exported by the `export_serialized` method. It should create
        a copy. An entry to the mapping could be made if a new instance is created.

        :param parent: Optionally a parent instance can be provided here.
        :type parent: Object
        :param serialized_values: The values that must be inserted.
        :type serialized_values: dict
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :type id_mapping: dict
        :return: The newly created instance.
        :rtype: Object
        """

        raise NotImplementedError("The import_serialized method must be implemented.")


T = TypeVar("T", bound=Instance)
K = TypeVar("K")


class Registry(Generic[T]):
    name: str
    """The unique name that is used when raising exceptions."""

    does_not_exist_exception_class = InstanceTypeDoesNotExist
    """The exception that is raised when an instance doesn't exist."""

    already_registered_exception_class = InstanceTypeAlreadyRegistered
    """The exception that is raised when an instance is already registered."""

    def __init__(self):
        if not getattr(self, "name", None):
            raise ImproperlyConfigured(
                "The name must be set on an "
                "InstanceModelRegistry to raise proper errors."
            )

        self.registry: Dict[str, T] = {}

    def get(self, type_name: str) -> T:
        """
        Returns a registered instance of the given type name.

        :param type_name: The unique name of the registered instance.
        :type type_name: str
        :raises InstanceTypeDoesNotExist: If the instance with the provided `type_name`
            does not exist in the registry.
        :return: The requested instance.
        :rtype: InstanceModelInstance
        """

        if type_name not in self.registry:
            raise self.does_not_exist_exception_class(
                type_name, f"The {self.name} type {type_name} does not exist."
            )

        return self.registry[type_name]

    def get_by_type(self, instance_type: Type[K]) -> K:
        return self.get(instance_type.type)

    def get_all(self) -> ValuesView[T]:
        """
        Returns all registered instances

        :return: A list of the registered instances.
        :rtype: List[InstanceModelInstance]
        """

        return self.registry.values()

    def get_types(self) -> List[str]:
        """
        Returns a list of available type names.

        :return: The list of available types.
        :rtype: List
        """

        return list(self.registry.keys())

    def get_types_as_tuples(self) -> List[Tuple[str, str]]:
        """
        Returns a list of available type names.

        :return: The list of available types.
        :rtype: List[Tuple[str,str]]
        """

        return [(k, k) for k in self.registry.keys()]

    def register(self, instance: T):
        """
        Registers a new instance in the registry.

        :param instance: The instance that needs to be registered.
        :type instance: Instance
        :raises ValueError: When the provided instance is not an instance of Instance.
        :raises InstanceTypeAlreadyRegistered: When the instance's type has already
            been registered.
        """

        if not isinstance(instance, Instance):
            raise ValueError(f"The {self.name} must be an instance of " f"Instance.")

        if instance.type in self.registry:
            raise self.already_registered_exception_class(
                f"The {self.name} with type {instance.type} is already registered."
            )

        self.registry[instance.type] = instance

    def unregister(self, value: T):
        """
        Removes a registered instance from the registry. An instance or type name can be
        provided as value.

        :param value: The instance or type name.
        :type value: Instance or str
        :raises ValueError: If the provided value is not an instance of Instance or
            string containing the type name.
        """

        if isinstance(value, Instance):
            for type_name, instance in self.registry.items():
                if instance == value:
                    value = type_name

        if isinstance(value, str):
            del self.registry[value]
        else:
            raise ValueError(
                f"The value must either be an {self.name} instance or " f"type name"
            )


P = TypeVar("P")


class ModelRegistryMixin(Generic[P, T]):
    def get_by_model(self, model_instance: Union[P, type]) -> T:
        """
        Returns a registered instance of the given model class.

        :param model_instance: The value that must be a Model class or
            an instance of any model_class.
        :raises InstanceTypeDoesNotExist: When the provided model instance is not
            found in the registry.
        :return: The registered instance.
        """

        if isinstance(model_instance, type):
            clazz = model_instance
        else:
            clazz = type(model_instance)

        return self.get_for_class(clazz)

    @lru_cache
    def get_for_class(self, clazz: type) -> T:
        """
        Returns a registered instance of the given model class.

        :param model_instance: The value that must be a Model class.
        :raises InstanceTypeDoesNotExist: When the provided model instance is not
            found in the registry.
        :return: The registered instance.
        """

        most_specific_value = None
        for value in self.registry.values():
            value_model_class = value.model_class
            if value_model_class == clazz or issubclass(clazz, value_model_class):
                if most_specific_value is None:
                    most_specific_value = value
                else:
                    # There might be values where one is a sub type of another. The
                    # one with the longer mro is the more specific type (it inherits
                    # from more base classes)
                    most_specific_num_base_classes = len(
                        most_specific_value.model_class.mro()
                    )
                    value_num_base_classes = len(value_model_class.mro())
                    if value_num_base_classes > most_specific_num_base_classes:
                        most_specific_value = value

        if most_specific_value is not None:
            return most_specific_value

        raise self.does_not_exist_exception_class(
            f"The {self.name} model {clazz} does not exist."
        )

    def get_all_by_model_isinstance(self, model_instance: P) -> List[T]:
        """
        Returns all registered types which are an instance of the provided
        model_instance.
        """

        all_matching_non_abstract_types = []
        for value in self.registry.values():
            value_model_class = value.model_class
            if value_model_class == model_instance or isinstance(
                model_instance, value_model_class
            ):
                all_matching_non_abstract_types.append(value)

        return all_matching_non_abstract_types


class CustomFieldsRegistryMixin:
    def get_serializer(self, model_instance, base_class=None, context=None, **kwargs):
        """
        Based on the provided model_instance and base_class a unique serializer
        containing the correct field type is generated.

        :param model_instance: The instance for which the serializer must be generated.
        :type model_instance: Model
        :param base_class: The base serializer class that must be extended. For example
            common fields could be stored here.
        :type base_class: ModelSerializer
        :param context: Extra context arguments to pass to the serializers context.
        :type kwargs: dict
        :param kwargs: The kwargs are used to initialize the serializer class.
        :type kwargs: dict
        :raises ValueError: When the `get_by_model` method was not found, which could
            indicate the `ModelRegistryMixin` has not been mixed in.
        :return: The instantiated generated model serializer.
        :rtype: ModelSerializer
        """

        get_by_model = getattr(self, "get_by_model")
        if not get_by_model:
            raise ValueError(
                "The method get_by_model must exist on the registry in "
                "order to generate the serializer, maybe you forgot to "
                "extend the ModelRegistryMixin?"
            )

        instance_type = self.get_by_model(model_instance.specific_class)
        return instance_type.get_serializer(
            model_instance, base_class=base_class, context=context, **kwargs
        )


class APIUrlsRegistryMixin:
    @property
    def api_urls(self):
        """
        Returns a list of all the api urls that are in the registered instances.

        :return: The api urls of the registered instances.
        :rtype: list
        """

        api_urls = []
        for types in self.registry.values():
            api_urls += types.get_api_urls()
        return api_urls
