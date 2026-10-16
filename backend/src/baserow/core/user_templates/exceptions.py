class InvalidTemplateIcon(Exception):
    """Raised when the icon of a user template isn't in the allowed list."""


class InvalidTemplateCategory(Exception):
    """
    Raised when a user template has no category, or one of its categories doesn't
    exist.
    """


class NoApplicationsSelected(Exception):
    """Raised when a user template is created without any application."""


class TemplateSlugGenerationFailed(Exception):
    """Raised when no free slug was found for a user template after a few tries."""
