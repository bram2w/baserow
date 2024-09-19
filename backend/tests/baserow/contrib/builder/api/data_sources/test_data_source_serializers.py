import pytest
from rest_framework import serializers

from baserow.contrib.builder.api.data_sources.serializers import GetRecordIdsSerializer


@pytest.mark.parametrize(
    "data,expected,valid",
    [
        ({"record_ids": ""}, {"record_ids": []}, True),
        ({"record_ids": "1"}, {"record_ids": ["1"]}, True),
        ({"record_ids": "1,2,3"}, {"record_ids": ["1", "2", "3"]}, True),
        ({"record_ids": "1,invalid"}, {"record_ids": []}, False),
        ({"record_ids": "invalid_1,invalid_2"}, {"record_ids": []}, False),
    ],
)
def test_get_record_ids_serializer(data, expected, valid):
    serializer = GetRecordIdsSerializer()

    if valid:
        assert serializer.to_internal_value(data) == expected
        assert serializer.to_representation(expected) == data
    else:
        with pytest.raises(serializers.ValidationError):
            serializer.to_internal_value(data)
