import pytest

from baserow.core.integrations.registries import integration_type_registry
from baserow.core.integrations.service import IntegrationService


@pytest.mark.django_db
def test_create_local_baserow_integration_with_user(data_fixture):
    user = data_fixture.create_user()
    application = data_fixture.create_builder_application(user=user)

    integration_type = integration_type_registry.get("local_baserow")

    integration = IntegrationService().create_integration(
        user, integration_type, application=application
    )

    assert integration.authorized_user.id == user.id
