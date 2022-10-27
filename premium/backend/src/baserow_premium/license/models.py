from django.contrib.auth import get_user_model
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import make_aware, now, utc

from dateutil import parser

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
        from .handler import LicenseHandler

        possibly_encoded_license = self.license
        if isinstance(possibly_encoded_license, str):
            encoded_license = possibly_encoded_license.encode()
        else:
            encoded_license = possibly_encoded_license
        return LicenseHandler.decode_license(encoded_license)

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

    @property
    def license_type(self):
        from baserow_premium.license.registries import license_type_registry

        return license_type_registry.get(self.product_code)


class LicenseUser(models.Model):
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="users")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("license", "user")
