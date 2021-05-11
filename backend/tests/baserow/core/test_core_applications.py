import pytest

from baserow.core.registries import ApplicationType, ApplicationTypeRegistry
from baserow.core.exceptions import (
    ApplicationTypeAlreadyRegistered,
    ApplicationTypeDoesNotExist,
)


class FakeModel(object):
    pass


class FakeModel2(object):
    pass


class TemporaryApplicationType1(ApplicationType):
    type = "temporary_1"
    model_class = FakeModel

    def get_api_urls(self):
        return ["url_1", "url_2"]


class TemporaryApplicationType2(ApplicationType):
    type = "temporary_2"
    model_class = FakeModel2

    def get_api_urls(self):
        return ["url_3"]


def test_application_registry_register():
    temporary_1 = TemporaryApplicationType1()

    registry = ApplicationTypeRegistry()
    registry.register(temporary_1)

    with pytest.raises(ApplicationTypeAlreadyRegistered):
        registry.register(temporary_1)


def test_application_registry_get():
    registry = ApplicationTypeRegistry()

    with pytest.raises(ApplicationTypeDoesNotExist):
        registry.get("something")


def test_application_get_api_urls():
    temporary_1 = TemporaryApplicationType1()
    temporary_2 = TemporaryApplicationType2()

    registry = ApplicationTypeRegistry()
    registry.register(temporary_1)
    registry.register(temporary_2)

    assert registry.api_urls == ["url_1", "url_2", "url_3"]
