import uuid

from django.db import models

from baserow.core.models import CreatedAndUpdatedOnMixin
from baserow.contrib.database.table.models import Table

from .validators import header_name_validator, header_value_validator


class WebhookRequestMethods(models.TextChoices):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class TableWebhook(CreatedAndUpdatedOnMixin, models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    active = models.BooleanField(
        default=True,
        help_text="Indicates whether the web hook is active. When a webhook has "
        "failed multiple times, it will automatically be deactivated.",
    )
    use_user_field_names = models.BooleanField(
        default=True,
        help_text="Indicates whether the field names must be used as payload key "
        "instead of the id.",
    )
    url = models.URLField(
        help_text="The URL that must call when the webhook is " "triggered."
    )
    request_method = models.CharField(
        max_length=10,
        choices=WebhookRequestMethods.choices,
        default=WebhookRequestMethods.POST,
        help_text="The request method that be used when the event occurs.",
    )
    name = models.CharField(
        max_length=255, help_text="An internal name of the webhook."
    )
    include_all_events = models.BooleanField(
        default=True,
        help_text="Indicates whether this webhook should listen to all events.",
    )
    failed_triggers = models.IntegerField(
        default=0, help_text="The amount of failed webhook calls."
    )

    @property
    def header_dict(self):
        return {header.name: header.value for header in self.headers.all()}

    class Meta:
        ordering = ("id",)


class TableWebhookEvent(CreatedAndUpdatedOnMixin, models.Model):
    webhook = models.ForeignKey(
        TableWebhook, related_name="events", on_delete=models.CASCADE
    )
    event_type = models.CharField(max_length=50)


class TableWebhookHeader(models.Model):
    webhook = models.ForeignKey(
        TableWebhook, related_name="headers", on_delete=models.CASCADE
    )
    name = models.TextField(validators=[header_name_validator])
    value = models.TextField(validators=[header_value_validator])


class TableWebhookCall(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(
        TableWebhook, related_name="calls", on_delete=models.CASCADE
    )
    event_type = models.CharField(max_length=50)
    called_time = models.DateTimeField(null=True)
    called_url = models.URLField()
    request = models.TextField(
        null=True, help_text="A text copy of the request headers and body."
    )
    response = models.TextField(
        null=True, help_text="A text copy of the response headers and body."
    )
    response_status = models.IntegerField(
        null=True, help_text="The HTTP response status code."
    )
    error = models.TextField(
        null=True, help_text="An internal error reflecting what went wrong."
    )

    class Meta:
        ordering = ("-called_time",)
