import re

from django.db import models

USER_TEMPLATE_DESCRIPTION_MAX_LENGTH = 80

# The icons an author can pick are listed in `templateIcons.js` of the
# web-frontend. The backend only checks that an icon is an iconoir class that fits
# `Template.icon`, so that the list is kept in one place.
USER_TEMPLATE_ICON_MAX_LENGTH = 32
USER_TEMPLATE_ICON_REGEX = re.compile(r"iconoir-[a-z0-9]+(-[a-z0-9]+)*")


class UserTemplateState(models.TextChoices):
    PRIVATE = "private", "Private"
    IN_REVIEW = "in_review", "In review"
    REJECTED = "rejected", "Rejected"
    BLOCKED = "blocked", "Blocked"
    PUBLIC = "public", "Public"
