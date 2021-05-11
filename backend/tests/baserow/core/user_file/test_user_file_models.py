import pytest

from baserow.core.user_files.exceptions import InvalidUserFileNameError
from baserow.core.models import UserFile


@pytest.mark.django_db
def test_serialize_user_file():
    user_file = UserFile.objects.create(
        original_name="test.txt",
        original_extension="txt",
        unique="sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA",
        size=10,
        mime_type="plain/text",
        is_image=True,
        image_width=100,
        image_height=100,
        sha256_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
    )
    assert user_file.serialize() == {
        "name": "sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA_"
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e.txt",
        "size": 10,
        "mime_type": "plain/text",
        "is_image": True,
        "image_width": 100,
        "image_height": 100,
        "uploaded_at": user_file.uploaded_at.isoformat(),
    }


@pytest.mark.django_db
def test_user_file_name():
    user_file = UserFile.objects.create(
        original_name="test.txt",
        original_extension="txt",
        unique="sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA",
        size=0,
        mime_type="plain/text",
        is_image=True,
        image_width=0,
        image_height=0,
        sha256_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
    )
    assert user_file.name == (
        "sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA_"
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e.txt"
    )


@pytest.mark.django_db
def test_user_file_deconstruct_name():
    with pytest.raises(InvalidUserFileNameError):
        UserFile.deconstruct_name("something.jpg")

    with pytest.raises(InvalidUserFileNameError):
        UserFile.deconstruct_name("something__test.jpg")

    with pytest.raises(InvalidUserFileNameError):
        UserFile.deconstruct_name("something_testjpg")

    with pytest.raises(InvalidUserFileNameError):
        UserFile.deconstruct_name("nothing_test.-")

    assert UserFile.deconstruct_name("random_hash.jpg") == {
        "unique": "random",
        "sha256_hash": "hash",
        "original_extension": "jpg",
    }
    assert UserFile.deconstruct_name(
        "sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA_"
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e.txt"
    ) == {
        "unique": "sdafi6WtHfnDrU6S1lQKh9PdC7PeafCA",
        "sha256_hash": (
            "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        ),
        "original_extension": "txt",
    }
