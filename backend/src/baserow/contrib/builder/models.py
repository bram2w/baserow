from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.pages.models import Page
from baserow.core.models import Application

__all__ = ["Builder", "Page", "Domain"]


class Builder(Application):
    pass
