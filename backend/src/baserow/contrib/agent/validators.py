from rest_framework.exceptions import ValidationError

from .models import AgentApplication

AGENT_TEXT_MAX_LENGTH = 100000


def validate_configuration_values(values: dict) -> None:
    """
    Check configuration value types and lengths, allowing blank drafts.

    :param values: The configuration values to check, by field name.
    :raises ValidationError: When a value is too long for its field or isn't a
        string, unless it is None for a nullable field.
    """

    for field, value in values.items():
        model_field = AgentApplication._meta.get_field(field)
        if value is None and model_field.null:
            continue
        if not isinstance(value, str):
            raise ValidationError({field: "A valid string is required."})
        limit = model_field.max_length or AGENT_TEXT_MAX_LENGTH
        if len(value) > limit:
            raise ValidationError(
                {field: f"This field may not exceed {limit} characters."}
            )
