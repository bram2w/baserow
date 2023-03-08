import pytest

from baserow.contrib.builder.handler import BuilderHandler
from baserow.core.exceptions import ApplicationDoesNotExist


@pytest.mark.django_db
def test_get_builder(data_fixture):
    builder = data_fixture.create_builder_application()
    assert BuilderHandler().get_builder(builder.id).id == builder.id


@pytest.mark.django_db
def test_get_builder_does_not_exist(data_fixture):
    with pytest.raises(ApplicationDoesNotExist):
        BuilderHandler().get_builder(9999)
