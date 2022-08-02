import pytest
from rest_framework.serializers import Serializer

from baserow.api.user_files.serializers import UserFileField


@pytest.mark.django_db
def test_user_file_field(data_fixture):
    user_file_1 = data_fixture.create_user_file()

    class TmpSerializer(Serializer):
        user_file = UserFileField(allow_null=True)

    serializer = TmpSerializer(data={"user_file": "invalid"})
    assert not serializer.is_valid()
    assert serializer.errors["user_file"][0].code == "invalid_value"

    serializer = TmpSerializer(data={"user_file": {"invalid": user_file_1.name}})
    assert not serializer.is_valid()
    assert serializer.errors["user_file"][0].code == "invalid_value"

    serializer = TmpSerializer(data={"user_file": {"name": "not_existing.jpg"}})
    assert not serializer.is_valid()
    assert serializer.errors["user_file"][0].code == "invalid_user_file"

    serializer = TmpSerializer(data={"user_file": None})
    assert serializer.is_valid()
    assert serializer.data["user_file"] is None

    serializer = TmpSerializer(data={"user_file": {"name": user_file_1.name}})
    assert serializer.is_valid()
    assert serializer.data["user_file"].id == user_file_1.id

    serializer = TmpSerializer({"user_file": user_file_1})
    assert serializer.data["user_file"]["name"] == user_file_1.name
    assert "url" in serializer.data["user_file"]

    serializer = TmpSerializer({"user_file": None})
    assert serializer.data["user_file"] is None
