import pytest

from django.core.exceptions import ImproperlyConfigured

from rest_framework.serializers import IntegerField, ModelSerializer
from rest_framework.exceptions import APIException

from baserow.contrib.database.models import Database
from baserow.core.registry import (
    Instance,
    ModelInstanceMixin,
    Registry,
    ModelRegistryMixin,
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    MapAPIExceptionsInstanceMixin,
)
from baserow.core.exceptions import (
    InstanceTypeAlreadyRegistered,
    InstanceTypeDoesNotExist,
)


class FakeModel(object):
    pass


class FakeModel2(object):
    pass


class TemporaryApplication1(ModelInstanceMixin, Instance):
    type = "temporary_1"
    model_class = FakeModel


class TemporaryApplication2(ModelInstanceMixin, Instance):
    type = "temporary_2"
    model_class = FakeModel2


class TemporaryRegistry(ModelRegistryMixin, Registry):
    name = "temporary"


class CustomFieldsTemporaryRegistry(
    ModelRegistryMixin, CustomFieldsRegistryMixin, Registry
):
    name = "temporary"


class TemporaryGroupInstanceType(
    ModelInstanceMixin, CustomFieldsInstanceMixin, Instance
):
    type = "temporary_3"
    model_class = Database
    allowed_fields = ["name"]
    serializer_field_names = ["name"]
    serializer_field_overrides = {"name": IntegerField()}


class TemporarySerializer(ModelSerializer):
    class Meta:
        fields = ["id"]


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
        registry.register("NOT AN APPLICATION")

    with pytest.raises(InstanceTypeAlreadyRegistered):
        registry.register(temporary_1)

    assert len(registry.registry.items()) == 2
    assert registry.registry["temporary_1"] == temporary_1
    assert registry.registry["temporary_2"] == temporary_2

    registry.unregister(temporary_1)

    assert len(registry.registry.items()) == 1

    registry.unregister("temporary_2")

    assert len(registry.registry.items()) == 0

    with pytest.raises(ValueError):
        registry.unregister(000)


def test_registry_get():
    temporary_1 = TemporaryApplication1()
    registry = TemporaryRegistry()
    registry.register(temporary_1)

    assert registry.get("temporary_1") == temporary_1
    with pytest.raises(InstanceTypeDoesNotExist):
        registry.get("something")

    assert registry.get_by_model(FakeModel) == temporary_1
    assert registry.get_by_model(FakeModel()) == temporary_1
    with pytest.raises(InstanceTypeDoesNotExist):
        registry.get_by_model(FakeModel2)
    with pytest.raises(InstanceTypeDoesNotExist):
        registry.get_by_model(FakeModel2())

    assert registry.get_types() == ["temporary_1"]


def test_api_exceptions_api_mixins():
    class FakeInstance(MapAPIExceptionsInstanceMixin, Instance):
        type = "fake_instance"
        api_exceptions_map = {ValueError: "RANDOM_ERROR"}

    instance = FakeInstance()

    with pytest.raises(Exception):
        with instance.map_api_exceptions():
            raise Exception("Failing normally here")

    with pytest.raises(APIException) as e:
        with instance.map_api_exceptions():
            raise ValueError("Should be converted.")

    assert e.value.detail["error"] == "RANDOM_ERROR"
    assert e.value.detail["detail"] == ""


@pytest.mark.django_db
def test_get_serializer(data_fixture):
    database = data_fixture.create_database_application(name="1")
    registry = CustomFieldsTemporaryRegistry()
    registry.register(TemporaryGroupInstanceType())

    serializer = registry.get_serializer(database)

    assert serializer.__class__.__name__ == "DatabaseSerializer"
    assert "id" not in serializer.data
    assert serializer.data["name"] == 1

    serializer = registry.get_serializer(database, base_class=TemporarySerializer)
    assert "id" in serializer.data
