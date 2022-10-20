import inspect

from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

import pytest
from rest_framework.exceptions import NotAuthenticated

from baserow.core.exceptions import (
    PermissionDenied,
    UserInvalidGroupPermissionsError,
    UserNotInGroup,
)
from baserow.core.handler import CoreHandler
from baserow.core.operations import (
    ListApplicationsGroupOperationType,
    UpdateGroupOperationType,
)
from baserow.core.registries import (
    ObjectScopeType,
    OperationType,
    object_scope_type_registry,
    operation_type_registry,
    permission_manager_type_registry,
)


@pytest.mark.django_db
@override_settings(PERMISSION_MANAGERS=["core", "staff", "member", "basic"])
def test_group_check_basic_permissions(data_fixture):
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
            raise_error=False,
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

    with pytest.raises(NotAuthenticated):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    basic_permission_manager = permission_manager_type_registry.get("basic")
    original_check = basic_permission_manager.check_permissions
    basic_permission_manager.check_permissions = lambda *args, **kwargs: None

    with pytest.raises(PermissionDenied):
        CoreHandler().check_permissions(
            user_group.user,
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    basic_permission_manager.check_permissions = original_check

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

    with pytest.raises(NotAuthenticated):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            allow_if_template=True,
            context=user_group.group,
        )


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
