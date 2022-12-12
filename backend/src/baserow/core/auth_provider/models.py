from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.core.mixins import CreatedAndUpdatedOnMixin, PolymorphicContentTypeMixin


class AuthProviderModel(
    CreatedAndUpdatedOnMixin,
    PolymorphicContentTypeMixin,
    models.Model,
):
    domain = models.CharField(max_length=255, null=True)
    enabled = models.BooleanField(default=True)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="auth_providers",
        on_delete=models.CASCADE,
    )
    users = models.ManyToManyField(
        "auth.User",
        related_name="auth_providers",
        help_text=("The users that have been authenticated with this provider."),
    )

    def user_signed_in(self, user):
        """
        This method is called when a user has successfully signed in with this
        authentication provider. It can be used to update the user model with
        information from the authentication provider.

        :param user: The user that has signed in.
        """

        self.users.add(user)

    class Meta:
        ordering = ["domain"]


class PasswordAuthProviderModel(AuthProviderModel):
    ...
