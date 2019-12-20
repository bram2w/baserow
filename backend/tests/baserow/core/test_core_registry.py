import pytest

from django.core.exceptions import ImproperlyConfigured

from baserow.core.registry import (
    Instance, ModelInstanceMixin, Registry, ModelRegistryMixin
)
from baserow.core.exceptions import (
    InstanceTypeAlreadyRegistered, InstanceTypeDoesNotExist
)


class FakeModel(object):
    pass


class FakeModel2(object):
    pass


class TemporaryApplication1(ModelInstanceMixin, Instance):
    type = 'temporary_1'
    model_class = FakeModel


class TemporaryApplication2(ModelInstanceMixin, Instance):
    type = 'temporary_2'
    model_class = FakeModel2


class TemporaryRegistry(ModelRegistryMixin, Registry):
    name = 'temporary'


def test_registry():
    with pytest.raises(ImproperlyConfigured):
        Registry()


def test_registry_register():
    temporary_1 = TemporaryApplication1()
    temporary_2 = TemporaryApplication2()

    registry = TemporaryRegistry()
    registry.register(temporary_1)
    registry.register(temporary_2)

    with pytest.raises(ValueError):
        registry.register('NOT AN APPLICATION')

    with pytest.raises(InstanceTypeAlreadyRegistered):
        registry.register(temporary_1)

    assert len(registry.registry.items()) == 2
    assert registry.registry['temporary_1'] == temporary_1
    assert registry.registry['temporary_2'] == temporary_2

    registry.unregister(temporary_1)

    assert len(registry.registry.items()) == 1

    registry.unregister('temporary_2')

    assert len(registry.registry.items()) == 0

    with pytest.raises(ValueError):
        registry.unregister(000)


def test_registry_get():
    temporary_1 = TemporaryApplication1()
    registry = TemporaryRegistry()
    registry.register(temporary_1)

    assert registry.get('temporary_1') == temporary_1
    with pytest.raises(InstanceTypeDoesNotExist):
        registry.get('something')

    assert registry.get_by_model(FakeModel) == temporary_1
    assert registry.get_by_model(FakeModel()) == temporary_1
    with pytest.raises(InstanceTypeDoesNotExist):
        registry.get_by_model(FakeModel2)
    with pytest.raises(InstanceTypeDoesNotExist):
        registry.get_by_model(FakeModel2())

    assert registry.get_types() == ['temporary_1']
