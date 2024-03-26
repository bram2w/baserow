from django.contrib.auth.models import AnonymousUser

import pytest

from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.elements.operations import ListElementsPageOperationType
from baserow.contrib.builder.elements.permission_manager import (
    ElementVisibilityPermissionManager,
)
from baserow.contrib.builder.workflow_actions.models import BuilderWorkflowAction
from baserow.contrib.builder.workflow_actions.operations import (
    DispatchBuilderWorkflowActionOperationType,
    ListBuilderWorkflowActionsPageOperationType,
)
from baserow.core.types import PermissionCheck
from baserow.core.user_sources.user_source_user import UserSourceUser


@pytest.mark.django_db
def test_element_visibility_permission_manager_check_permission(data_fixture):
    user = data_fixture.create_user(username="Auth user")
    builder = data_fixture.create_builder_application(user=user)
    builder_to = data_fixture.create_builder_application(workspace=None)
    domain1 = data_fixture.create_builder_custom_domain(
        builder=builder, published_to=builder_to
    )

    public_page = data_fixture.create_builder_page(builder=builder_to)

    public_user_source = data_fixture.create_user_source_with_first_type(
        application=builder_to
    )

    element_all = data_fixture.create_builder_button_element(
        page=public_page, visibility=Element.VISIBILITY_TYPES.ALL
    )

    element_logged_in = data_fixture.create_builder_button_element(
        page=public_page, visibility=Element.VISIBILITY_TYPES.LOGGED_IN
    )

    element_not_logged = data_fixture.create_builder_button_element(
        page=public_page, visibility=Element.VISIBILITY_TYPES.NOT_LOGGED
    )

    workflow_action_all = data_fixture.create_local_baserow_create_row_workflow_action(
        page=public_page, element=element_all
    )
    workflow_action_logged_in = (
        data_fixture.create_local_baserow_create_row_workflow_action(
            page=public_page, element=element_logged_in
        )
    )
    workflow_action_not_logged = (
        data_fixture.create_local_baserow_create_row_workflow_action(
            page=public_page, element=element_not_logged
        )
    )

    public_user_source_user = UserSourceUser(
        public_user_source, None, 1, "US public", "e@ma.il"
    )

    perm_manager = ElementVisibilityPermissionManager()
    checks = []
    for user in [
        public_user_source_user,
        AnonymousUser(),
    ]:
        for perm_type, scope in [
            (
                DispatchBuilderWorkflowActionOperationType.type,
                workflow_action_all,
            ),
            (
                DispatchBuilderWorkflowActionOperationType.type,
                workflow_action_logged_in,
            ),
            (
                DispatchBuilderWorkflowActionOperationType.type,
                workflow_action_not_logged,
            ),
        ]:
            checks.append(PermissionCheck(user, perm_type, scope))

    result = perm_manager.check_multiple_permissions(checks, builder.workspace)

    list_result = [
        (
            c.actor.username,
            c.operation_name,
            c.context.element.visibility,
            result.get(c, None),
        )
        for c in checks
    ]

    assert list_result == [
        (
            "US public",
            "builder.page.workflow_action.dispatch",
            Element.VISIBILITY_TYPES.ALL,
            None,
        ),
        (
            "US public",
            "builder.page.workflow_action.dispatch",
            Element.VISIBILITY_TYPES.LOGGED_IN,
            None,
        ),
        (
            "US public",
            "builder.page.workflow_action.dispatch",
            Element.VISIBILITY_TYPES.NOT_LOGGED,
            False,
        ),
        (
            "",
            "builder.page.workflow_action.dispatch",
            Element.VISIBILITY_TYPES.ALL,
            None,
        ),
        (
            "",
            "builder.page.workflow_action.dispatch",
            Element.VISIBILITY_TYPES.LOGGED_IN,
            False,
        ),
        (
            "",
            "builder.page.workflow_action.dispatch",
            Element.VISIBILITY_TYPES.NOT_LOGGED,
            None,
        ),
    ]


@pytest.mark.django_db
def test_element_visibility_permission_manager_filter_queryset(data_fixture):
    user = data_fixture.create_user(username="Auth user")
    builder = data_fixture.create_builder_application(user=user)
    builder_to = data_fixture.create_builder_application(workspace=None)
    domain1 = data_fixture.create_builder_custom_domain(
        builder=builder, published_to=builder_to
    )

    public_page = data_fixture.create_builder_page(builder=builder_to)

    public_user_source = data_fixture.create_user_source_with_first_type(
        application=builder_to
    )

    element_all = data_fixture.create_builder_button_element(
        page=public_page, visibility=Element.VISIBILITY_TYPES.ALL
    )

    element_logged_in = data_fixture.create_builder_button_element(
        page=public_page, visibility=Element.VISIBILITY_TYPES.LOGGED_IN
    )

    element_not_logged = data_fixture.create_builder_button_element(
        page=public_page, visibility=Element.VISIBILITY_TYPES.NOT_LOGGED
    )

    workflow_action_all = data_fixture.create_local_baserow_create_row_workflow_action(
        page=public_page, element=element_all
    )
    workflow_action_logged_in = (
        data_fixture.create_local_baserow_create_row_workflow_action(
            page=public_page, element=element_logged_in
        )
    )
    workflow_action_not_logged = (
        data_fixture.create_local_baserow_create_row_workflow_action(
            page=public_page, element=element_not_logged
        )
    )

    public_user_source_user = UserSourceUser(
        public_user_source, None, 1, "US public", "e@ma.il"
    )

    perm_manager = ElementVisibilityPermissionManager()

    # Element

    all_elements_for_auth = perm_manager.filter_queryset(
        public_user_source_user,
        ListElementsPageOperationType.type,
        Element.objects.all(),
    )

    assert len(all_elements_for_auth) == 2

    assert all(
        [
            e.visibility != Element.VISIBILITY_TYPES.NOT_LOGGED
            for e in all_elements_for_auth
        ]
    )

    all_elements_for_anonymous = perm_manager.filter_queryset(
        AnonymousUser(),
        ListElementsPageOperationType.type,
        Element.objects.all(),
    )

    assert len(all_elements_for_anonymous) == 2

    assert all(
        [
            e.visibility != Element.VISIBILITY_TYPES.LOGGED_IN
            for e in all_elements_for_anonymous
        ]
    )

    # Workflow actions

    all_was_for_auth = perm_manager.filter_queryset(
        public_user_source_user,
        ListBuilderWorkflowActionsPageOperationType.type,
        BuilderWorkflowAction.objects.all(),
    )

    assert len(all_was_for_auth) == 2

    assert all(
        [
            wa.element.visibility != Element.VISIBILITY_TYPES.NOT_LOGGED
            for wa in all_was_for_auth
        ]
    )

    all_was_for_anonymous = perm_manager.filter_queryset(
        AnonymousUser(),
        ListBuilderWorkflowActionsPageOperationType.type,
        BuilderWorkflowAction.objects.all(),
    )

    assert len(all_was_for_anonymous) == 2

    assert all(
        [
            wa.element.visibility != Element.VISIBILITY_TYPES.LOGGED_IN
            for wa in all_was_for_anonymous
        ]
    )
