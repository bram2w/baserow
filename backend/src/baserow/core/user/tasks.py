from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth import get_user_model

from baserow.config.celery import app

User = get_user_model()


@app.task(bind=True, queue="export")
def check_pending_account_deletion(self):
    """
    Periodic tasks that delete pending deletion user account that has overcome the
    grace delay.
    """

    from .handler import UserHandler

    UserHandler().delete_expired_users_and_related_workspaces_if_last_admin()


@app.task(bind=True, queue="export")
def flush_expired_tokens(self):
    """
    Flushes the expired blacklisted refresh tokens.
    """

    from baserow.core.models import BlacklistedToken

    BlacklistedToken.objects.filter(
        expires_at__lte=datetime.now(tz=timezone.utc)
    ).delete()


@app.task(bind=True, queue="export")
def clean_up_user_log_entry(self):
    """
    Execute job cleanup for UserLogEntry.
    """

    from baserow.core.user.handler import UserHandler

    older_than_days = timedelta(days=settings.BASEROW_USER_LOG_ENTRY_RETENTION_DAYS)
    cutoff_datetime = datetime.now(tz=timezone.utc) - older_than_days

    UserHandler().delete_user_log_entries_older_than(cutoff_datetime)


@app.task(bind=True, queue="export")
def share_onboarding_details_with_baserow(self, **kwargs):
    """
    Task wrapper that calls the `share_onboarding_details_with_baserow` method.
    """

    from baserow.core.user.handler import UserHandler

    UserHandler().share_onboarding_details_with_baserow(**kwargs)


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        getattr(settings, "CHECK_PENDING_ACCOUNT_DELETION_INTERVAL", timedelta(days=1)),
        check_pending_account_deletion.s(),
    )
    sender.add_periodic_task(
        timedelta(days=1),
        flush_expired_tokens.s(),
    )
    sender.add_periodic_task(
        timedelta(minutes=settings.BASEROW_USER_LOG_ENTRY_CLEANUP_INTERVAL_MINUTES),
        clean_up_user_log_entry.s(),
    )
