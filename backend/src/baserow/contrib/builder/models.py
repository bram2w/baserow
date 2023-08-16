from baserow.contrib.builder.domains.models import Domain, PublishDomainJob
from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.theme.models import MainThemeConfigBlock
from baserow.core.models import Application

__all__ = [
    "Builder",
    "Page",
    "Domain",
    "PublishDomainJob",
    "Element",
    "MainThemeConfigBlock",
]


class Builder(Application):
    def get_parent(self):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return self.application_ptr
