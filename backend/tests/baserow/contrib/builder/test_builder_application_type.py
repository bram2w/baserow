import pytest

from baserow.contrib.builder.application_types import BuilderApplicationType
from baserow.contrib.builder.pages.models import Page


@pytest.mark.django_db
def test_builder_application_type_init_application(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    assert Page.objects.count() == 0

    BuilderApplicationType().init_application(user, builder)

    assert Page.objects.count() == 1
