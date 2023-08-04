from django.contrib.auth.models import AnonymousUser

import pytest

from baserow.contrib.builder.data_sources.operations import (
    ListDataSourcesPageOperationType,
)
from baserow.contrib.builder.domains.permission_manager import (
    AllowPublicBuilderManagerType,
)
from baserow.contrib.builder.elements.operations import ListElementsPageOperationType
from baserow.contrib.builder.pages.operations import UpdatePageOperationType
from baserow.core.operations import (
    ReadApplicationOperationType,
    UpdateApplicationOperationType,
)
from baserow.core.types import PermissionCheck


@pytest.mark.django_db
def test_allow_public_builder_manager_type(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    builder_to = data_fixture.create_builder_application(workspace=None)
    domain1 = data_fixture.create_builder_domain(
        builder=builder, published_to=builder_to
    )
    domain2 = data_fixture.create_builder_domain(builder=builder)

    public_page = data_fixture.create_builder_page(builder=builder_to)
    non_public_page = data_fixture.create_builder_page(builder=builder)

    perm_manager = AllowPublicBuilderManagerType()

    checks = []
    for user in [user, AnonymousUser()]:
        for type, scope in [
            (ListElementsPageOperationType.type, public_page),
            (ListElementsPageOperationType.type, non_public_page),
            (ListDataSourcesPageOperationType.type, public_page),
            (ListDataSourcesPageOperationType.type, non_public_page),
            (UpdatePageOperationType.type, public_page),
            (ReadApplicationOperationType.type, builder_to.application_ptr),
            (ReadApplicationOperationType.type, builder.application_ptr),
            (UpdateApplicationOperationType.type, builder_to.application_ptr),
        ]:
            checks.append(PermissionCheck(user, type, scope))

    result = perm_manager.check_multiple_permissions(checks, builder.workspace)

    list_result = [result.get(c, None) for c in checks]

    assert list_result == [
        # Authenticated
        True,
        None,
        True,
        None,
        None,
        True,
        None,
        None,
        # Anonymous
        True,
        None,
        True,
        None,
        None,
        True,
        None,
        None,
    ]
