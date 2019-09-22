import pytest

from baserow.core.applications import Application, ApplicationRegistry
from baserow.core.exceptions import (
    ApplicationAlreadyRegistered, ApplicationTypeDoesNotExist
)


class FakeModel(object):
    pass


class FakeModel2(object):
    pass


class TemporaryApplication1(Application):
    type = 'temporary_1'
    instance_model = FakeModel

    def get_api_urls(self):
        return ['url_1', 'url_2']


class TemporaryApplication2(Application):
    type = 'temporary_2'
    instance_model = FakeModel2

    def get_api_urls(self):
        return ['url_3']


def test_application_registry_register():
    temporary_1 = TemporaryApplication1()
    temporary_2 = TemporaryApplication2()

    registry = ApplicationRegistry()
    registry.register(temporary_1)
    registry.register(temporary_2)

    with pytest.raises(ValueError):
        registry.register('NOT AN APPLICATION')

    with pytest.raises(ApplicationAlreadyRegistered):
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


def test_application_registry_get():
    temporary_1 = TemporaryApplication1()
    registry = ApplicationRegistry()
    registry.register(temporary_1)

    assert registry.get('temporary_1') == temporary_1
    with pytest.raises(ApplicationTypeDoesNotExist):
        registry.get('something')

    assert registry.get_by_model(FakeModel) == temporary_1
    assert registry.get_by_model(FakeModel()) == temporary_1
    with pytest.raises(ApplicationTypeDoesNotExist):
        registry.get_by_model(FakeModel2)
    with pytest.raises(ApplicationTypeDoesNotExist):
        registry.get_by_model(FakeModel2())


def test_application_get_api_urls():
    temporary_1 = TemporaryApplication1()
    temporary_2 = TemporaryApplication2()

    registry = ApplicationRegistry()
    registry.register(temporary_1)
    registry.register(temporary_2)

    assert registry.api_urls == ['url_1', 'url_2', 'url_3']
