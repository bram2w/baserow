import pytest

from baserow.contrib.builder.models import Builder
from baserow.core.handler import CoreHandler


@pytest.mark.django_db
def test_can_duplicate_builder_application(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    builder_clone = CoreHandler().duplicate_application(user, builder)

    assert builder.id != builder_clone.id
    assert builder.name in builder_clone.name

    assert Builder.objects.count() == 2
