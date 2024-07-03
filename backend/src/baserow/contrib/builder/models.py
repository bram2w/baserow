from django.db import models

from baserow.contrib.builder.domains.models import Domain, PublishDomainJob
from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.theme.models import (
    ButtonThemeConfigBlock,
    ColorThemeConfigBlock,
    TypographyThemeConfigBlock,
)
from baserow.core.models import Application, UserFile

__all__ = [
    "Builder",
    "Page",
    "Domain",
    "PublishDomainJob",
    "Element",
    "ColorThemeConfigBlock",
    "TypographyThemeConfigBlock",
    "ButtonThemeConfigBlock",
]


class Builder(Application):
    favicon_file = models.ForeignKey(
        UserFile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="builder_favicon_file",
    )

    def get_parent(self):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return self.application_ptr
