import inspect

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, QuerySet
from django.test.utils import override_settings

import pytest

from baserow.contrib.database.operations import ListTablesDatabaseTableOperationType
from baserow.core.exceptions import (
    PermissionDenied,
    UserInvalidWorkspacePermissionsError,
    UserNotInWorkspace,
)
from baserow.core.handler import CoreHandler
from baserow.core.operations import (
    ListApplicationsWorkspaceOperationType,
    ListWorkspacesOperationType,
    UpdateSettingsOperationType,
    UpdateWorkspaceOperationType,
)
from baserow.core.permission_manager import (
    BasicPermissionManagerType,
    CorePermissionManagerType,
    StaffOnlyPermissionManagerType,
    WorkspaceMemberOnlyPermissionManagerType,
)
from baserow.core.registries import (
    ObjectScopeType,
    OperationType,
    object_scope_type_registry,
    operation_type_registry,
    permission_manager_type_registry,
)
from baserow.core.types import PermissionCheck


@pytest.mark.django_db
@override_settings(
    PERMISSION_MANAGERS=[
        "core",
        "setting_operation",
        "staff",
        "member",
        "token",
        "basic",
    ]
)
def test_check_permissions(data_fixture):
    user = data_fixture.create_user()
    user_workspace = data_fixture.create_user_workspace(permissions="ADMIN")
    user_workspace_2 = data_fixture.create_user_workspace(permissions="MEMBER")
    user_workspace_3 = data_fixture.create_user_workspace()
    data_fixture.create_template(workspace=user_workspace_3.workspace)

    # An external user shouldn't be allowed
    with pytest.raises(UserNotInWorkspace):
        CoreHandler().check_permissions(
            user,
            ListApplicationsWorkspaceOperationType.type,
            workspace=user_workspace.workspace,
            context=user_workspace.workspace,
        )

    with pytest.raises(UserNotInWorkspace):
        CoreHandler().check_permissions(
            user,
            UpdateWorkspaceOperationType.type,
            workspace=user_workspace.workspace,
            context=user_workspace.workspace,
        )

    assert (
        CoreHandler().check_permissions(
            user,
            ListApplicationsWorkspaceOperationType.type,
            workspace=user_workspace.workspace,
            context=user_workspace.workspace,
            raise_permission_exceptions=False,
        )
        is False
    )

    assert CoreHandler().check_permissions(
        user_workspace.user,
        ListApplicationsWorkspaceOperationType.type,
        workspace=user_workspace.workspace,
        context=user_workspace.workspace,
    )
    assert CoreHandler().check_permissions(
        user_workspace.user,
        UpdateWorkspaceOperationType.type,
        workspace=user_workspace.workspace,
        context=user_workspace.workspace,
    )

    assert CoreHandler().check_permissions(
        user_workspace_2.user,
        ListApplicationsWorkspaceOperationType.type,
        workspace=user_workspace_2.workspace,
        context=user_workspace.workspace,
    )

    with pytest.raises(UserInvalidWorkspacePermissionsError):
        assert CoreHandler().check_permissions(
            user_workspace_2.user,
            UpdateWorkspaceOperationType.type,
            workspace=user_workspace_2.workspace,
            context=user_workspace_2.workspace,
        )

    with pytest.raises(PermissionDenied):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsWorkspaceOperationType.type,
            workspace=user_workspace.workspace,
            context=user_workspace.workspace,
        )

    basic_permission_manager = permission_manager_type_registry.get("basic")
    original_check = basic_permission_manager.check_multiple_permissions
    basic_permission_manager.check_multiple_permissions = lambda *args, **kwargs: {}

    # should be refused by default if the basic permission manager doesn't answer.
    with pytest.raises(PermissionDenied):
        CoreHandler().check_permissions(
            user_workspace.user,
            ListApplicationsWorkspaceOperationType.type,
            workspace=user_workspace.workspace,
            context=user_workspace.workspace,
        )

    basic_permission_manager.check_multiple_permissions = original_check

    with pytest.raises(UserInvalidWorkspacePermissionsError):
        assert CoreHandler().check_permissions(
            user_workspace_2.user,
            UpdateWorkspaceOperationType.type,
            workspace=user_workspace_2.workspace,
            context=user_workspace_2.workspace,
            allow_if_template=True,
        )

    assert CoreHandler().check_permissions(
        user_workspace_3.user,
        UpdateWorkspaceOperationType.type,
        workspace=user_workspace_3.workspace,
        context=user_workspace_3.workspace,
        allow_if_template=True,
    )

    with pytest.raises(PermissionDenied):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsWorkspaceOperationType.type,
            workspace=user_workspace.workspace,
            allow_if_template=True,
            context=user_workspace.workspace,
        )


@pytest.mark.django_db
def test_check_multiple_permissions(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    user_4 = data_fixture.create_user()
    workspace = data_fixture.create_workspace(
        user=admin,
        custom_permissions=[(user_2, "MEMBER"), (user_3, "MEMBER")],
    )
    database = data_fixture.create_database_application(user=admin, workspace=workspace)

    checks = []
    result = CoreHandler().check_multiple_permissions(checks, workspace)

    assert result == {}

    checks = []
    for user in [admin, user_2, user_3, user_4, AnonymousUser()]:
        for type, scope in [
            (UpdateSettingsOperationType.type, None),
            (ListWorkspacesOperationType.type, workspace),
            (UpdateWorkspaceOperationType.type, workspace),
            (ListApplicationsWorkspaceOperationType.type, workspace),
            (ListTablesDatabaseTableOperationType.type, database),
        ]:
            checks.append(PermissionCheck(user, type, scope))

    perm_manager = CorePermissionManagerType()

    result = perm_manager.check_multiple_permissions(
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], workspace
    )

    assert [result[c] if c in result else None for c in checks] == [
        None,
        True,
        None,
        None,
        None,
        None,
        True,
        None,
        None,
        None,
        None,
        True,
        None,
        None,
        None,
        None,
        True,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]

    perm_manager = StaffOnlyPermissionManagerType()
    result = perm_manager.check_multiple_permissions(
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], workspace
    )
    assert [
        (result[c] if result[c] is True else False) if c in result else None
        for c in checks
    ] == [
        True,
        None,
        None,
        None,
        None,
        False,
        None,
        None,
        None,
        None,
        False,
        None,
        None,
        None,
        None,
        False,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]

    perm_manager = WorkspaceMemberOnlyPermissionManagerType()
    result = perm_manager.check_multiple_permissions(
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], workspace
    )
    assert [
        (result[c] if result[c] is True else False) if c in result else None
        for c in checks
    ] == [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        False,
        False,
        False,
        False,
        False,
        None,
        None,
        None,
        None,
        None,
    ]

    perm_manager = BasicPermissionManagerType()
    result = perm_manager.check_multiple_permissions(
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], workspace
    )
    assert [
        (result[c] if result[c] is True else False) if c in result else None
        for c in checks
    ] == [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        None,
        None,
        None,
        None,
        None,
    ]

    # All together
    result = CoreHandler().check_multiple_permissions(checks, workspace)

    permission_result = [result[check] for check in checks]

    assert permission_result == [
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        False,
        True,
        True,
        False,
        True,
        False,
        True,
        True,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ]


@pytest.mark.django_db
def test_get_permissions(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    user_4 = data_fixture.create_user()
    workspace = data_fixture.create_workspace(
        user=admin,
        custom_permissions=[(user_2, "ADMIN"), (user_3, "MEMBER")],
    )

    result = CoreHandler().get_permissions(admin)
    print(result)

    assert result == [
        {"name": "view_ownership", "permissions": {}},
        {"name": "core", "permissions": ["list_workspaces"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_workspace"],
            },
        },
        {
            "name": "staff",
            "permissions": {
                "staff_only_operations": ["settings.update"],
                "is_staff": True,
            },
        },
        {"name": "member", "permissions": False},
    ]

    result = CoreHandler().get_permissions(admin, workspace)

    assert result == [
        {"name": "view_ownership", "permissions": {}},
        {"name": "core", "permissions": ["list_workspaces"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_workspace"],
            },
        },
        {
            "name": "staff",
            "permissions": {
                "staff_only_operations": ["settings.update"],
                "is_staff": True,
            },
        },
        {
            "name": "basic",
            "permissions": {
                "admin_only_operations": [
                    "workspace.list_invitations",
                    "workspace.create_invitation",
                    "invitation.read",
                    "invitation.update",
                    "invitation.delete",
                    "workspace.list_workspace_users",
                    "workspace.update",
                    "workspace.delete",
                    "workspace_user.update",
                    "workspace_user.delete",
                ],
                "is_admin": True,
            },
        },
    ]

    result = CoreHandler().get_permissions(user_2)

    assert result == [
        {"name": "view_ownership", "permissions": {}},
        {"name": "core", "permissions": ["list_workspaces"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_workspace"],
            },
        },
        {
            "name": "staff",
            "permissions": {
                "staff_only_operations": ["settings.update"],
                "is_staff": False,
            },
        },
        {"name": "member", "permissions": False},
    ]

    result = CoreHandler().get_permissions(user_2, workspace)

    assert result == [
        {"name": "view_ownership", "permissions": {}},
        {"name": "core", "permissions": ["list_workspaces"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_workspace"],
            },
        },
        {
            "name": "staff",
            "permissions": {
                "staff_only_operations": ["settings.update"],
                "is_staff": False,
            },
        },
        {
            "name": "basic",
            "permissions": {
                "admin_only_operations": [
                    "workspace.list_invitations",
                    "workspace.create_invitation",
                    "invitation.read",
                    "invitation.update",
                    "invitation.delete",
                    "workspace.list_workspace_users",
                    "workspace.update",
                    "workspace.delete",
                    "workspace_user.update",
                    "workspace_user.delete",
                ],
                "is_admin": True,
            },
        },
    ]

    result = CoreHandler().get_permissions(user_3)

    assert result == [
        {"name": "view_ownership", "permissions": {}},
        {"name": "core", "permissions": ["list_workspaces"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_workspace"],
            },
        },
        {
            "name": "staff",
            "permissions": {
                "staff_only_operations": ["settings.update"],
                "is_staff": False,
            },
        },
        {"name": "member", "permissions": False},
    ]

    result = CoreHandler().get_permissions(user_3, workspace)

    assert result == [
        {"name": "view_ownership", "permissions": {}},
        {"name": "core", "permissions": ["list_workspaces"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_workspace"],
            },
        },
        {
            "name": "staff",
            "permissions": {
                "staff_only_operations": ["settings.update"],
                "is_staff": False,
            },
        },
        {
            "name": "basic",
            "permissions": {
                "admin_only_operations": [
                    "workspace.list_invitations",
                    "workspace.create_invitation",
                    "invitation.read",
                    "invitation.update",
                    "invitation.delete",
                    "workspace.list_workspace_users",
                    "workspace.update",
                    "workspace.delete",
                    "workspace_user.update",
                    "workspace_user.delete",
                ],
                "is_admin": False,
            },
        },
    ]

    result = CoreHandler().get_permissions(user_4, workspace)

    assert result == [
        {"name": "view_ownership", "permissions": {}},
        {"name": "core", "permissions": ["list_workspaces"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_workspace"],
            },
        },
        {
            "name": "staff",
            "permissions": {
                "staff_only_operations": ["settings.update"],
                "is_staff": False,
            },
        },
        {"name": "member", "permissions": False},
    ]


@pytest.mark.django_db
def test_all_operations_are_registered():
    def get_all_subclasses(cls):
        all_subclasses = []

        for subclass in cls.__subclasses__():
            if not inspect.isabstract(subclass):
                all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses(subclass))

        return all_subclasses

    funcs = operation_type_registry.get_all()
    registered_operation_types = {f.type for f in funcs}
    all_operation_types = {
        t.type
        for t in get_all_subclasses(OperationType)
        if hasattr(t, "type") and t.type is not None
    }
    assert (
        all_operation_types == registered_operation_types
    ), "Please make sure the following operation " "types are added to the registry: " + str(
        all_operation_types.difference(registered_operation_types)
    ) + " or somehow the following operations are registered but not subclasses?: " + str(
        registered_operation_types.difference(all_operation_types)
    )


@pytest.mark.django_db
def test_all_scope_types_are_registered():
    def get_all_subclasses(cls):
        all_subclasses = []

        for subclass in cls.__subclasses__():
            if not inspect.isabstract(subclass):
                all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses(subclass))

        return all_subclasses

    funcs = object_scope_type_registry.get_all()
    registered_operation_types = {f.type for f in funcs}
    all_operation_types = {
        t.type for t in get_all_subclasses(ObjectScopeType) if hasattr(t, "type")
    }
    assert (
        all_operation_types == registered_operation_types
    ), "Please make sure the following operation " "types are added to the registry: " + str(
        all_operation_types.difference(registered_operation_types)
    ) + " or somehow the following operations are registered but not subclasses?: " + str(
        registered_operation_types.difference(all_operation_types)
    )


@pytest.mark.django_db
def test_all_scope_types_referenced_by_operations_are_registered():
    def get_all_subclasses(cls):
        all_subclasses = []

        for subclass in cls.__subclasses__():
            if not inspect.isabstract(subclass):
                all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses(subclass))

        return all_subclasses

    funcs = object_scope_type_registry.get_all()
    object_scope_types = {f.type for f in funcs}
    all_op_context_types = {
        t.context_scope_name for t in get_all_subclasses(OperationType)
    }
    assert (
        all_op_context_types == object_scope_types
    ), "Please make sure the following object_scope_types exist and are added to the " "registry: " + str(
        all_op_context_types.difference(object_scope_types)
    ) + " or somehow the following context types are registered but not subclasses?: " + str(
        object_scope_types.difference(all_op_context_types)
    )


@pytest.mark.django_db
def test_all_scope_types_query_methods():
    all_scope_type = object_scope_type_registry.get_all()

    for scope_type in all_scope_type:
        if scope_type.type == "core":
            continue

        assert isinstance(scope_type.get_base_queryset(), QuerySet)
        assert isinstance(scope_type.get_enhanced_queryset(), QuerySet)

        for parent in scope_type.get_parent_scopes():
            assert isinstance(scope_type.get_filter_for_scope_type(parent, []), Q)
