from django.contrib.auth.models import AnonymousUser

import pytest

from baserow.contrib.builder.data_sources.operations import (
    DispatchDataSourceOperationType,
    ListDataSourcesPageOperationType,
)
from baserow.contrib.builder.domains.permission_manager import (
    AllowPublicBuilderManagerType,
)
from baserow.contrib.builder.elements.operations import ListElementsPageOperationType
from baserow.contrib.builder.pages.operations import UpdatePageOperationType
from baserow.contrib.builder.workflow_actions.operations import (
    DispatchBuilderWorkflowActionOperationType,
    ListBuilderWorkflowActionsPageOperationType,
)
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
    domain1 = data_fixture.create_builder_custom_domain(
        builder=builder, published_to=builder_to
    )
    domain2 = data_fixture.create_builder_custom_domain(builder=builder)

    public_page = data_fixture.create_builder_page(builder=builder_to)
    non_public_page = data_fixture.create_builder_page(builder=builder)

    public_data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=public_page
    )
    non_public_data_source = (
        data_fixture.create_builder_local_baserow_get_row_data_source(
            page=non_public_page
        )
    )

    public_workflow_action = data_fixture.create_notification_workflow_action(
        page=public_page
    )
    non_public_workflow_action = data_fixture.create_notification_workflow_action(
        page=non_public_page
    )

    perm_manager = AllowPublicBuilderManagerType()

    checks = []
    for user in [user, AnonymousUser()]:
        for perm_type, scope in [
            (ListElementsPageOperationType.type, public_page),
            (ListElementsPageOperationType.type, non_public_page),
            (ListDataSourcesPageOperationType.type, public_page),
            (ListDataSourcesPageOperationType.type, non_public_page),
            (ListBuilderWorkflowActionsPageOperationType.type, public_page),
            (ListBuilderWorkflowActionsPageOperationType.type, non_public_page),
            (UpdatePageOperationType.type, public_page),
            (ReadApplicationOperationType.type, builder_to.application_ptr),
            (ReadApplicationOperationType.type, builder.application_ptr),
            (UpdateApplicationOperationType.type, builder_to.application_ptr),
            (DispatchDataSourceOperationType.type, public_data_source),
            (DispatchDataSourceOperationType.type, non_public_data_source),
            (DispatchBuilderWorkflowActionOperationType.type, public_workflow_action),
            (
                DispatchBuilderWorkflowActionOperationType.type,
                non_public_workflow_action,
            ),
        ]:
            checks.append(PermissionCheck(user, perm_type, scope))

    result = perm_manager.check_multiple_permissions(checks, builder.workspace)

    list_result = [result.get(c, None) for c in checks]

    assert list_result == [
        # Authenticated
        True,
        None,
        True,
        None,
        True,
        None,
        None,
        True,
        None,
        None,
        True,
        None,
        True,
        None,
        # Anonymous
        True,
        None,
        True,
        None,
        True,
        None,
        None,
        True,
        None,
        None,
        True,
        None,
        True,
        None,
    ]
