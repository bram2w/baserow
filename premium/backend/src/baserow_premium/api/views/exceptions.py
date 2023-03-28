class CannotUpdatePremiumAttributesOnTemplate(Exception):
    """Raised when a user tries to update premium attributes on a template group."""


class InvalidSelectOptionParameter(Exception):
    """Raised when an invalid select option query parameter is provided."""

    def __init__(self, select_option_name, *args, **kwargs):
        self.select_option_name = select_option_name
        super().__init__(*args, **kwargs)
