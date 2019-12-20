from baserow.core.registry import (
    Instance, Registry, ModelInstanceMixin, ModelRegistryMixin
)
from .exceptions import ViewTypeAlreadyRegistered, ViewTypeDoesNotExist


class ViewType(ModelInstanceMixin, Instance):
    """
    This abstract class represents a custom view type that can be added to the
    view type registry. It must be extended so customisation can be done. Each view type
    will have his own model that must extend the View model, this is needed so that the
    user can set custom settings per view instance he has created.

    Example:
        from baserow.contrib.views.models import View
        from baserow.contrib.database.views.registry import ViewType, registry

        class ExampleViewModel(ViewType):
            pass

        class ExampleViewType(ViewType):
            type = 'a-unique-view-type-name'
            model_class = ExampleViewModel

        registry.register(ExampleViewType())

    """

    instance_serializer_class = None
    """This serializer that is used to serialize the instance model."""


class ViewTypeRegistry(ModelRegistryMixin, Registry):
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
