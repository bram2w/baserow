from django.contrib.auth.models import AbstractUser

from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.theme.handler import ThemeHandler
from baserow.contrib.builder.theme.operations import UpdateThemeOperationType
from baserow.contrib.builder.theme.signals import theme_updated
from baserow.core.handler import CoreHandler


class ThemeService:
    def __init__(self):
        self.handler = ThemeHandler()

    def update_theme(self, user: AbstractUser, builder: Builder, **kwargs) -> Builder:
        """
        Updates the theme properties of a builder application.

        :param user: The user trying to update the theme.
        :param builder: The builder of which the theme should be updated.
        :param kwargs: A dict containing the theme properties that must be updated.
        """

        CoreHandler().check_permissions(
            user,
            UpdateThemeOperationType.type,
            workspace=builder.workspace,
            context=builder,
        )

        builder = self.handler.update_theme(builder, **kwargs)

        theme_updated.send(self, builder=builder, user=user, properties=kwargs)

        return builder
