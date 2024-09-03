from django.db import models
from django.db.models import SET_NULL

from baserow.contrib.builder.elements.models import Element
from baserow.core.formula.field import FormulaField


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

    login_button_label = FormulaField(
        help_text="The label of the login button",
        blank=True,
        default="",
        null=True,  # TODO zdm remove me in next release (after 1.27)
    )
