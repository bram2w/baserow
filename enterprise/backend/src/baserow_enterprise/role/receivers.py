from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete

User = get_user_model()


def cascade_subject_delete(sender, instance, **kwargs):
    """
    Delete role assignments linked to deleted subjects.
    """

    from .models import RoleAssignment

    subject_ct = ContentType.objects.get_for_model(instance)
    RoleAssignment.objects.filter(
        subject_id=instance.id, subject_type=subject_ct
    ).delete()


def cascade_group_user_delete(sender, instance, **kwargs):
    """
    Delete role assignments linked user to deleted GroupUser.
    """

    from .models import RoleAssignment

    user_id = instance.user_id
    group_id = instance.group_id
    user_ct = ContentType.objects.get_for_model(User)
    RoleAssignment.objects.filter(
        subject_id=user_id, subject_type=user_ct, group_id=group_id
    ).delete()


def cascade_scope_delete(sender, instance, **kwargs):
    """
    Delete role assignments linked to deleted scope.
    """

    from .models import RoleAssignment

    scope_ct = ContentType.objects.get_for_model(instance)
    RoleAssignment.objects.filter(scope_id=instance.id, scope_type=scope_ct).delete()


def connect_to_post_delete_signals_to_cascade_deletion_to_role_assignments():
    """
    Connect to post_delete signal of all role_assignment generic foreign key to delete
    all related role_assignments.
    """

    from baserow.core.models import GroupUser
    from baserow.core.registries import (
        object_scope_type_registry,
        subject_type_registry,
    )
    from baserow_enterprise.role.constants import ROLE_ASSIGNABLE_OBJECT_MAP

    # Add the subject handler
    for subject_type in subject_type_registry.get_all():
        post_delete.connect(cascade_subject_delete, subject_type.model_class)

    # Add the GroupUser handler
    post_delete.connect(cascade_group_user_delete, GroupUser)

    # Add the scope handler
    for role_assignable_object_type in ROLE_ASSIGNABLE_OBJECT_MAP.keys():
        scope_type = object_scope_type_registry.get(role_assignable_object_type)
        post_delete.connect(cascade_scope_delete, scope_type.model_class)
