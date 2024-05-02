import pytest

from baserow.core.db import specific_iterator
from baserow.core.service import CoreService


@pytest.mark.django_db
def test_list_applications_in_workspace(
    data_fixture, django_assert_num_queries, bypass_check_permissions
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_database_application(workspace=workspace)
    application_in_another_workspace = data_fixture.create_database_application()

    with django_assert_num_queries(1):
        applications = CoreService().list_applications_in_workspace(user, workspace.id)

    specific_applications = specific_iterator(applications)

    assert application in specific_applications
    assert application_in_another_workspace not in specific_applications
    assert len(specific_applications) == 1
