from rest_framework.serializers import ValidationError

from baserow.contrib.database.airtable.utils import extract_share_id_from_url


def is_publicly_shared_airtable_url(value):
    try:
        extract_share_id_from_url(value)
    except ValueError:
        raise ValidationError(
            "The publicly shared Airtable URL is invalid.", code="invalid"
        )
