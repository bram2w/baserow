from django.conf import settings
from django.db import transaction

from baserow.config.celery import app


@app.task(bind=True, max_retries=settings.WEBHOOKS_MAX_RETRIES_PER_CALL, queue="export")
def call_webhook(
    self,
    webhook_id: int,
    event_id: str,
    event_type: str,
    method: str,
    url: str,
    headers: dict,
    payload: dict,
    **kwargs: dict
):
    """
    This task should be called asynchronously when the webhook call must be trigged.
    All the raw values should be provided as argument. If the call fails for whatever
    reason, it tries again until the max retries have been reached.

    :param webhook_id: The id of the webhook related to the call.
    :param event_id: A unique event id that can used as id for the table webhook call
        model.
    :param event_type: The event type related to the webhook trigger.
    :param method: The request method the must be used.
    :param url: The URL can must be called.
    :param headers: The additional headers that must be added to the request. The key
        is the name and the value is the value.
    :param payload: The JSON serializable payload that must be used as request body.
    """

    from django.utils import timezone
    from requests import RequestException
    from advocate import UnacceptableAddressException

    from .handler import WebhookHandler
    from .models import TableWebhook, TableWebhookCall

    with transaction.atomic():
        handler = WebhookHandler()

        try:
            webhook = TableWebhook.objects.select_for_update().get(id=webhook_id)
        except TableWebhook.DoesNotExist:
            # If the webhook has been deleted while executing, we don't want to continue
            # trying to call the URL because we can't update the state of the webhook.
            return

        request = None
        response = None
        success = False
        error = ""

        try:
            response = handler.make_request(method, url, headers, payload)
            request = response.request
            success = response.ok
        except RequestException as exception:
            request = exception.request
            response = exception.response
            error = str(exception)
        except UnacceptableAddressException as exception:
            error = str(exception)

        TableWebhookCall.objects.update_or_create(
            id=event_id,
            event_type=event_type,
            webhook=webhook,
            defaults={
                "called_time": timezone.now(),
                "called_url": url,
                "request": handler.format_request(request)
                if request is not None
                else None,
                "response": handler.format_response(response)
                if response is not None
                else None,
                "response_status": response.status_code
                if response is not None
                else None,
                "error": error,
            },
        )
        handler.clean_webhook_calls(webhook)

        if success and webhook.failed_triggers != 0:
            # If the call was successful and failed triggers had been increased in
            # the past, we can safely reset it to 0 again to prevent deactivation of
            # the webhook.
            webhook.failed_triggers = 0
            webhook.save()
        elif not success and (
            webhook.failed_triggers < settings.WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES
        ):
            # If the task has reached the maximum amount of failed calls, we're going to
            # give up and increase the total failed triggers of the webhook if we're
            # still operating within the limits of the max consecutive trigger failures.
            webhook.failed_triggers += 1
            webhook.save()
        elif not success:
            # If webhook has reached the maximum amount of failed triggers,
            # we're going to deactivate it because we can reasonable assume that the
            # target doesn't listen anymore. At this point we've tried 8 * 10 times.
            # The user can manually activate it again when it's fixed.
            webhook.active = False
            webhook.save()

    # This part must be outside of the transaction block, otherwise it could cause
    # the transaction to rollback when the retry exception is raised, and we don't want
    # that to happen.
    if not success and self.request.retries < settings.WEBHOOKS_MAX_RETRIES_PER_CALL:
        # If the task is still operating within the max retries per call limit,
        # then we want to retry the task with an exponential backoff.
        self.retry(countdown=2 ** self.request.retries)
