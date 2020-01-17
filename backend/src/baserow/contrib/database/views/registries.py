from baserow.core.registry import (
    Instance, Registry, ModelInstanceMixin, ModelRegistryMixin,
    CustomFieldsInstanceMixin, CustomFieldsRegistryMixin
)
from .exceptions import ViewTypeAlreadyRegistered, ViewTypeDoesNotExist


class ViewType(CustomFieldsInstanceMixin, ModelInstanceMixin, Instance):
    """
    This abstract class represents a custom view type that can be added to the
    view type registry. It must be extended so customisation can be done. Each view type
    will have his own model that must extend the View model, this is needed so that the
    user can set custom settings per view instance he has created.

    Example:
        from baserow.contrib.database.views.models import View
        from baserow.contrib.database.views.registry import ViewType, view_type_registry

        class ExampleViewModel(ViewType):
            pass

        class ExampleViewType(ViewType):
            type = 'a-unique-view-type-name'
            model_class = ExampleViewModel
            allowed_fields = ['example_ordering']
            serializer_field_names = ['example_ordering']
            serializer_field_overrides = {
                'example_ordering': serializers.CharField()
            }

        view_type_registry.register(ExampleViewType())
    """


class ViewTypeRegistry(CustomFieldsRegistryMixin, ModelRegistryMixin, Registry):
    """
    With the view type registry it is possible to register new view types.  A view type
    is an abstraction made specifically for Baserow. If added to the registry a user can
    create new views based on this type.
    """

    name = 'view'
    does_not_exist_exception_class = ViewTypeDoesNotExist
    already_registered_exception_class = ViewTypeAlreadyRegistered


# A default view type registry is created here, this is the one that is used
# throughout the whole Baserow application to add a new view type.
view_type_registry = ViewTypeRegistry()
