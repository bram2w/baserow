from django.db import models
from django.db.models import SET_NULL

from baserow.contrib.builder.elements.models import Element


class AuthFormElement(Element):
    """
    An element to authenticate against a user source.
    """

    user_source = models.ForeignKey(
        "core.UserSource",
        null=True,
        on_delete=SET_NULL,
        help_text="Display the auth form for the selected user source",
    )
