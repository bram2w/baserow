from baserow.core.mixins import HierarchicalModelMixin
from baserow.core.registries import object_scope_type_registry


def test_all_scope_types_with_model_classes_are_hierarchical():
    for t in object_scope_type_registry.get_all():
        if not issubclass(t.model_class, type(None)):
            assert issubclass(t.model_class, HierarchicalModelMixin), (
                "All ObjectScopeType.model_class classes must implement the "
                "HierarchicalModelMixin"
            )
