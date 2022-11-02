from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from baserow.core.auth_provider.models import AuthProviderModel


class SamlAuthProviderModel(AuthProviderModel):
    metadata = models.TextField(
        blank=True, help_text="The XML metadata downloaded from the metadata_url."
    )
    is_verified = models.BooleanField(
        default=False,
        help_text=(
            "This will be set to True only after a user successfully login with this IdP. "
            "This must be True to disable normal username/password login and "
            "make SAML the only authentication provider. "
        ),
    )


@receiver(pre_save, sender=SamlAuthProviderModel)
def reset_is_verified_if_metadata_changed(sender, instance, **kwargs):
    """
    When the metadata is changed, we want to reset the is_verified flag to False. This
    will force the user to login again with the IdP to verify that the metadata is still
    valid.
    """

    if instance.pk:
        original = sender.objects.get(pk=instance.pk)
        if original.metadata != instance.metadata:
            instance.is_verified = False
