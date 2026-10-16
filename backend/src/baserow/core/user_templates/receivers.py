from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from baserow.core.user_templates.handler import UserTemplateHandler
from baserow.core.user_templates.models import CreateUserTemplateJob

User = get_user_model()


@receiver(pre_delete, sender=User, dispatch_uid="mark_owned_user_templates_deleted")
def mark_owned_user_templates_deleted(sender, instance, **kwargs):
    """
    Deleting the user sets `owner` to null afterwards, which a live user template
    must not have, so their templates are marked for deletion first.
    """

    UserTemplateHandler().mark_owned_templates_for_deletion(instance)


@receiver(
    pre_delete,
    sender=CreateUserTemplateJob,
    dispatch_uid="delete_create_user_template_job_content",
)
def delete_create_user_template_job_content(sender, instance, **kwargs):
    """
    Deleting an unfinished job, when it expires or with its user, would lose
    track of the workspace and archive it copied, so they're deleted along. A
    failure is logged, so that it doesn't stop deleting the other jobs.
    """

    workspace_id, archive_name = instance.workspace_id, instance.archive_name
    if workspace_id is None and not archive_name:
        return

    transaction.on_commit(
        lambda: UserTemplateHandler().delete_content_without_template(
            workspace_id, archive_name
        ),
        robust=True,
    )
