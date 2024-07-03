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


@pytest.mark.django_db(transaction=True)
def test_get_builder_select_related_theme_config(
    data_fixture, django_assert_num_queries
):
    builder = data_fixture.create_builder_application()
    builder.colorthemeconfigblock
    builder.typographythemeconfigblock
    builder.buttonthemeconfigblock

    builder = BuilderHandler().get_builder(builder.id)

    with django_assert_num_queries(0):
        builder.colorthemeconfigblock.id
        builder.typographythemeconfigblock.id
        builder.buttonthemeconfigblock.id
