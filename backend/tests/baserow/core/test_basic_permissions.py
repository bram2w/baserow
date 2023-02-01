import inspect

from django.contrib.auth.models import AnonymousUser
from django.db.models import Q, QuerySet
from django.test.utils import override_settings

import pytest

from baserow.contrib.database.operations import ListTablesDatabaseTableOperationType
from baserow.core.exceptions import (
    PermissionDenied,
    UserInvalidGroupPermissionsError,
    UserNotInGroup,
)
from baserow.core.handler import CoreHandler
from baserow.core.operations import (
    ListApplicationsGroupOperationType,
    ListGroupsOperationType,
    UpdateGroupOperationType,
    UpdateSettingsOperationType,
)
from baserow.core.permission_manager import (
    BasicPermissionManagerType,
    CorePermissionManagerType,
    GroupMemberOnlyPermissionManagerType,
    StaffOnlyPermissionManagerType,
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
    user_group = data_fixture.create_user_group(permissions="ADMIN")
    user_group_2 = data_fixture.create_user_group(permissions="MEMBER")
    user_group_3 = data_fixture.create_user_group()
    data_fixture.create_template(group=user_group_3.group)

    # An external user shouldn't be allowed
    with pytest.raises(UserNotInGroup):
        CoreHandler().check_permissions(
            user,
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    with pytest.raises(UserNotInGroup):
        CoreHandler().check_permissions(
            user,
            UpdateGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    assert (
        CoreHandler().check_permissions(
            user,
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
            raise_permission_exceptions=False,
        )
        is False
    )

    assert CoreHandler().check_permissions(
        user_group.user,
        ListApplicationsGroupOperationType.type,
        group=user_group.group,
        context=user_group.group,
    )
    assert CoreHandler().check_permissions(
        user_group.user,
        UpdateGroupOperationType.type,
        group=user_group.group,
        context=user_group.group,
    )

    assert CoreHandler().check_permissions(
        user_group_2.user,
        ListApplicationsGroupOperationType.type,
        group=user_group_2.group,
        context=user_group.group,
    )

    with pytest.raises(UserInvalidGroupPermissionsError):
        assert CoreHandler().check_permissions(
            user_group_2.user,
            UpdateGroupOperationType.type,
            group=user_group_2.group,
            context=user_group_2.group,
        )

    with pytest.raises(PermissionDenied):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    basic_permission_manager = permission_manager_type_registry.get("basic")
    original_check = basic_permission_manager.check_multiple_permissions
    basic_permission_manager.check_multiple_permissions = lambda *args, **kwargs: {}

    # should be refused by default if the basic permission manager doesn't answer.
    with pytest.raises(PermissionDenied):
        CoreHandler().check_permissions(
            user_group.user,
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    basic_permission_manager.check_multiple_permissions = original_check

    with pytest.raises(UserInvalidGroupPermissionsError):
        assert CoreHandler().check_permissions(
            user_group_2.user,
            UpdateGroupOperationType.type,
            group=user_group_2.group,
            context=user_group_2.group,
            allow_if_template=True,
        )

    assert CoreHandler().check_permissions(
        user_group_3.user,
        UpdateGroupOperationType.type,
        group=user_group_3.group,
        context=user_group_3.group,
        allow_if_template=True,
    )

    with pytest.raises(PermissionDenied):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            allow_if_template=True,
            context=user_group.group,
        )


@pytest.mark.django_db
def test_check_multiple_permissions(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    user_4 = data_fixture.create_user()
    group = data_fixture.create_group(
        user=admin,
        custom_permissions=[(user_2, "MEMBER"), (user_3, "MEMBER")],
    )
    database = data_fixture.create_database_application(user=admin, group=group)

    checks = []
    result = CoreHandler().check_multiple_permissions(checks, group)

    assert result == {}

    checks = []
    for user in [admin, user_2, user_3, user_4, AnonymousUser()]:
        for type, scope in [
            (UpdateSettingsOperationType.type, None),
            (ListGroupsOperationType.type, group),
            (UpdateGroupOperationType.type, group),
            (ListApplicationsGroupOperationType.type, group),
            (ListTablesDatabaseTableOperationType.type, database),
        ]:
            checks.append(PermissionCheck(user, type, scope))

    perm_manager = CorePermissionManagerType()

    result = perm_manager.check_multiple_permissions(
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], group
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
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], group
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

    perm_manager = GroupMemberOnlyPermissionManagerType()
    result = perm_manager.check_multiple_permissions(
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], group
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
        [c for c in checks if perm_manager.actor_is_supported(c.actor)], group
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
    result = CoreHandler().check_multiple_permissions(checks, group)

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
    group = data_fixture.create_group(
        user=admin,
        custom_permissions=[(user_2, "ADMIN"), (user_3, "MEMBER")],
    )

    result = CoreHandler().get_permissions(admin)
    print(result)

    assert result == [
        {"name": "core", "permissions": ["list_groups"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_group"],
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

    result = CoreHandler().get_permissions(admin, group)
    print(result)

    assert result == [
        {"name": "core", "permissions": ["list_groups"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_group"],
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
                    "group.list_invitations",
                    "group.create_invitation",
                    "invitation.read",
                    "invitation.update",
                    "invitation.delete",
                    "group.list_group_users",
                    "group.update",
                    "group.delete",
                    "group_user.update",
                    "group_user.delete",
                ],
                "is_admin": True,
            },
        },
    ]

    result = CoreHandler().get_permissions(user_2)

    assert result == [
        {"name": "core", "permissions": ["list_groups"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_group"],
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

    result = CoreHandler().get_permissions(user_2, group)

    assert result == [
        {"name": "core", "permissions": ["list_groups"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_group"],
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
                    "group.list_invitations",
                    "group.create_invitation",
                    "invitation.read",
                    "invitation.update",
                    "invitation.delete",
                    "group.list_group_users",
                    "group.update",
                    "group.delete",
                    "group_user.update",
                    "group_user.delete",
                ],
                "is_admin": True,
            },
        },
    ]

    result = CoreHandler().get_permissions(user_3)

    assert result == [
        {"name": "core", "permissions": ["list_groups"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_group"],
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

    result = CoreHandler().get_permissions(user_3, group)

    assert result == [
        {"name": "core", "permissions": ["list_groups"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_group"],
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
                    "group.list_invitations",
                    "group.create_invitation",
                    "invitation.read",
                    "invitation.update",
                    "invitation.delete",
                    "group.list_group_users",
                    "group.update",
                    "group.delete",
                    "group_user.update",
                    "group_user.delete",
                ],
                "is_admin": False,
            },
        },
    ]

    result = CoreHandler().get_permissions(user_4, group)

    assert result == [
        {"name": "core", "permissions": ["list_groups"]},
        {
            "name": "setting_operation",
            "permissions": {
                "staff_only_operations": [],
                "always_allowed_operations": ["create_group"],
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
