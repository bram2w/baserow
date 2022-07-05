from rest_framework import serializers


class ReportSerializer(serializers.Serializer):
    failing_rows = serializers.DictField(
        child=serializers.DictField(
            child=serializers.ListField(
                child=serializers.CharField(),
                help_text="Error messages for this field.",
            ),
            help_text=(
                "An object containing error messages by fields. "
                "The key is the field name and the value is an array of error messages "
                "for this field. These messages are localized for the user "
                "who has created the job when the translation is available."
            ),
        ),
        help_text=(
            "An object containing field in error by rows. "
            "The keys are the row indexes from original file and values are objects "
            "of errors by fields."
        ),
    )
