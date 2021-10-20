from dateutil import parser

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import utc, now, make_aware
from django.utils.functional import cached_property


User = get_user_model()


class License(models.Model):
    license = models.TextField()
    last_check = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        try:
            del self.payload
        except AttributeError:
            pass
        return super().save(*args, **kwargs)

    @cached_property
    def payload(self):
        from .handler import decode_license

        premium_license = self.license
        if isinstance(premium_license, str):
            premium_license = premium_license.encode()
        return decode_license(premium_license)

    @property
    def license_id(self):
        return self.payload["id"]

    @property
    def valid_from(self):
        return make_aware(parser.parse(self.payload["valid_from"]), utc)

    @property
    def valid_through(self):
        return make_aware(parser.parse(self.payload["valid_through"]), utc)

    @property
    def is_active(self):
        return self.valid_from <= now() <= self.valid_through

    @property
    def product_code(self):
        return self.payload["product_code"]

    @property
    def seats(self):
        return self.payload["seats"]

    @property
    def issued_on(self):
        return make_aware(parser.parse(self.payload["issued_on"]), utc)

    @property
    def issued_to_email(self):
        return self.payload["issued_to_email"]

    @property
    def issued_to_name(self):
        return self.payload["issued_to_name"]


class LicenseUser(models.Model):
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="users")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("license", "user")
