from datetime import timedelta

from django.db import transaction

from baserow.config.celery import app


@app.task(bind=True, queue="export")
def license_check(self):
    """
    Periodic tasks that check all the licenses with the authority.
    """

    from .handler import LicenseHandler
    from .models import License

    all_licenses = License.objects.all()

    if len(all_licenses) > 0:
        with transaction.atomic():
            LicenseHandler.check_licenses(all_licenses)


# noinspection PyUnusedLocal
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(timedelta(hours=1), license_check.s())
