from rest_framework import serializers

from baserow.contrib.database.api.utils import extract_user_field_names_from_params


class UserFieldNamesField(serializers.BooleanField):
    def to_internal_value(self, data):
        return extract_user_field_names_from_params({"user_field_names": data})
