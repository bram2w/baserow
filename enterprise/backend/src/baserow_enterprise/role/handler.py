from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from baserow_enterprise.models import RoleAssignment

from baserow.core.registries import object_scope_type_registry

User = get_user_model()


class RoleAssignmentHandler:
    def get_current_role_assignment(
        self,
        subject,
        group,
        scope=None,
    ):

        if scope is None:
            scope = group

        content_types = ContentType.objects.get_for_models(scope, subject)

        try:
            role_assignment = RoleAssignment.objects.get(
                scope_id=scope.id,
                scope_type=content_types[scope],
                group=group,
                subject_id=subject.id,
                subject_type=content_types[subject],
            )

            return role_assignment
        except RoleAssignment.DoesNotExist:
            return None

    def assign_role(
        self,
        subject,
        group,
        role=None,
        scope=None,
    ):

        if role is None:
            self.remove_role(subject, group, scope=scope)
            return

        if scope is None:
            scope = group

        content_types = ContentType.objects.get_for_models(scope, subject)

        role_assignment, _ = RoleAssignment.objects.update_or_create(
            subject_id=subject.id,
            subject_type=content_types[subject],
            group=group,
            scope_id=scope.id,
            scope_type=content_types[scope],
            defaults={"role": role},
        )

        return role_assignment

    def remove_role(self, subject, group, scope=None):

        if scope is None:
            scope = group

        content_types = ContentType.objects.get_for_models(scope, subject)

        RoleAssignment.objects.filter(
            subject_id=subject.id,
            subject_type=content_types[subject],
            group=group,
            scope_id=scope.id,
            scope_type=content_types[scope],
        ).delete()

    def get_subject(self, subject_id, subject_type):

        if subject_type == "user":
            content_type = ContentType.objects.get_for_model(User)
            return content_type.get_object_for_this_type(id=subject_id)

        return None

    def get_scope(self, scope_id, scope_type):

        scope_type = object_scope_type_registry.get(scope_type)
        content_type = ContentType.objects.get_for_model(scope_type.model_class)
        return content_type.get_object_for_this_type(id=scope_id)
