from pytz import all_timezones

from rest_framework import serializers

from baserow.api.applications.serializers import ApplicationSerializer
from baserow.contrib.database.airtable.models import AirtableImportJob

from .validators import is_publicly_shared_airtable_url


class AirtableImportJobSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.IntegerField(
        source="get_cached_progress_percentage",
        help_text="A percentage indicating how far along the import job is. 100 means "
        "that it's finished.",
    )
    state = serializers.CharField(
        source="get_cached_state",
        help_text="Indicates the state of the import job.",
    )
    database = ApplicationSerializer()

    class Meta:
        model = AirtableImportJob
        fields = (
            "id",
            "group_id",
            "airtable_share_id",
            "progress_percentage",
            "timezone",
            "state",
            "human_readable_error",
            "database",
        )


class CreateAirtableImportJobSerializer(serializers.Serializer):
    group_id = serializers.IntegerField(
        required=True,
        help_text="The group ID where the Airtable base must be imported into.",
    )
    airtable_share_url = serializers.URLField(
        required=True,
        validators=[is_publicly_shared_airtable_url],
        help_text="The publicly shared URL of the Airtable base (e.g. "
        "https://airtable.com/shrxxxxxxxxxxxxxx)",
    )
    timezone = serializers.ChoiceField(
        required=False,
        choices=all_timezones,
        help_text="Optionally a timezone can be provided that must be respected "
        "during import. This is for example setting the correct value of the date "
        "fields.",
    )
