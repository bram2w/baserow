import pytest
import responses
import string

from freezegun import freeze_time
from PIL import Image
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from baserow.core.models import UserFile
from baserow.core.user_files.exceptions import (
    InvalidFileStreamError,
    FileSizeTooLargeError,
    FileURLCouldNotBeReached,
    MaximumUniqueTriesError,
    InvalidFileURLError,
)
from baserow.core.user_files.handler import UserFileHandler


@pytest.mark.django_db
def test_user_file_path(data_fixture):
    handler = UserFileHandler()
    assert handler.user_file_path("test.jpg") == "user_files/test.jpg"
    assert handler.user_file_path("another_file.png") == "user_files/another_file.png"

    user_file = data_fixture.create_user_file()
    assert handler.user_file_path(user_file) == f"user_files/{user_file.name}"


@pytest.mark.django_db
def test_user_file_thumbnail_path(data_fixture):
    handler = UserFileHandler()
    assert (
        handler.user_file_thumbnail_path("test.jpg", "tiny")
        == "thumbnails/tiny/test.jpg"
    )
    assert (
        handler.user_file_thumbnail_path("another_file.png", "small")
        == "thumbnails/small/another_file.png"
    )

    user_file = data_fixture.create_user_file()
    assert (
        handler.user_file_thumbnail_path(user_file, "tiny")
        == f"thumbnails/tiny/{user_file.name}"
    )


@pytest.mark.django_db
def test_generate_unique(data_fixture):
    user = data_fixture.create_user()
    handler = UserFileHandler()

    assert len(handler.generate_unique("test", "txt", 32)) == 32
    assert len(handler.generate_unique("test", "txt", 10)) == 10
    assert handler.generate_unique("test", "txt", 32) != handler.generate_unique(
        "test", "txt", 32
    )

    unique = handler.generate_unique("test", "txt", 32)
    assert not UserFile.objects.filter(unique=unique).exists()

    for char in string.ascii_letters + string.digits:
        data_fixture.create_user_file(
            uploaded_by=user, unique=char, original_extension="txt", sha256_hash="test"
        )

    with pytest.raises(MaximumUniqueTriesError):
        handler.generate_unique("test", "txt", 1, 3)

    handler.generate_unique("test2", "txt", 1, 3)
    handler.generate_unique("test", "txt2", 1, 3)


@pytest.mark.django_db
def test_upload_user_file(data_fixture, tmpdir):
    user = data_fixture.create_user()

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    handler = UserFileHandler()

    with pytest.raises(InvalidFileStreamError):
        handler.upload_user_file(user, "test.txt", "NOT A STREAM!", storage=storage)

    with pytest.raises(InvalidFileStreamError):
        handler.upload_user_file(user, "test.txt", None, storage=storage)

    old_limit = settings.USER_FILE_SIZE_LIMIT
    settings.USER_FILE_SIZE_LIMIT = 6
    with pytest.raises(FileSizeTooLargeError):
        handler.upload_user_file(user, "test.txt", ContentFile(b"Hello World"))
    settings.USER_FILE_SIZE_LIMIT = old_limit

    with freeze_time("2020-01-01 12:00"):
        user_file = handler.upload_user_file(
            user, "test.txt", ContentFile(b"Hello World"), storage=storage
        )

    assert user_file.original_name == "test.txt"
    assert user_file.original_extension == "txt"
    assert len(user_file.unique) == 32
    assert user_file.size == 11
    assert user_file.mime_type == "text/plain"
    assert user_file.uploaded_by_id == user.id
    assert user_file.uploaded_at.year == 2020
    assert user_file.uploaded_at.month == 1
    assert user_file.uploaded_at.day == 1
    assert user_file.is_image is False
    assert user_file.image_width is None
    assert user_file.image_height is None
    assert user_file.sha256_hash == (
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    )
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()
    assert file_path.open().read() == "Hello World"

    user_file = handler.upload_user_file(
        user, "another.txt", BytesIO(b"Hello"), storage=storage
    )
    assert user_file.original_name == "another.txt"
    assert user_file.original_extension == "txt"
    assert user_file.mime_type == "text/plain"
    assert user_file.size == 5
    assert user_file.sha256_hash == (
        "185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969"
    )
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()
    assert file_path.open().read() == "Hello"

    assert (
        handler.upload_user_file(
            user, "another.txt", ContentFile(b"Hello"), storage=storage
        ).id
        == user_file.id
    )
    assert (
        handler.upload_user_file(
            user, "another_name.txt", ContentFile(b"Hello"), storage=storage
        ).id
        != user_file.id
    )

    image = Image.new("RGB", (100, 140), color="red")
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")

    user_file = handler.upload_user_file(
        user, "some image.png", image_bytes, storage=storage
    )
    assert user_file.mime_type == "image/png"
    assert user_file.is_image is True
    assert user_file.image_width == 100
    assert user_file.image_height == 140
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()
    file_path = tmpdir.join("thumbnails", "tiny", user_file.name)
    assert file_path.isfile()
    thumbnail = Image.open(file_path.open("rb"))
    assert thumbnail.height == 21
    assert thumbnail.width == 21

    old_thumbnail_settings = settings.USER_THUMBNAILS
    settings.USER_THUMBNAILS = {"tiny": [None, 100]}
    image = Image.new("RGB", (1920, 1080), color="red")
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    user_file = handler.upload_user_file(user, "red.png", image_bytes, storage=storage)
    file_path = tmpdir.join("thumbnails", "tiny", user_file.name)
    assert file_path.isfile()
    thumbnail = Image.open(file_path.open("rb"))
    assert thumbnail.width == 178
    assert thumbnail.height == 100

    image = Image.new("RGB", (400, 400), color="red")
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    user_file = handler.upload_user_file(user, "red2.png", image_bytes, storage=storage)
    file_path = tmpdir.join("thumbnails", "tiny", user_file.name)
    assert file_path.isfile()
    thumbnail = Image.open(file_path.open("rb"))
    assert thumbnail.width == 100
    assert thumbnail.height == 100

    settings.USER_THUMBNAILS = {"tiny": [21, None]}
    image = Image.new("RGB", (1400, 1000), color="red")
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    user_file = handler.upload_user_file(user, "red3.png", image_bytes, storage=storage)
    file_path = tmpdir.join("thumbnails", "tiny", user_file.name)
    assert file_path.isfile()
    thumbnail = Image.open(file_path.open("rb"))
    assert thumbnail.width == 21
    assert thumbnail.height == 15
    settings.USER_THUMBNAILS = old_thumbnail_settings

    assert UserFile.objects.all().count() == 7

    image = Image.new("RGB", (1, 1), color="red")
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    user_file = handler.upload_user_file(
        user,
        "this_file_has_an_extreme_long_file_name_that_should_not_make_the_system_"
        "fail_hard_when_trying_to_upload.png",
        image_bytes,
        storage=storage,
    )

    assert (
        user_file.original_name == "this_file_has_an_extreme_long_f...hard_when_"
        "trying_to_upload.png"
    )


@pytest.mark.django_db
@responses.activate
def test_upload_user_file_by_url(data_fixture, tmpdir):
    user = data_fixture.create_user()

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    handler = UserFileHandler()

    responses.add(
        responses.GET,
        "https://baserow.io/test.txt",
        body=b"Hello World",
        status=200,
        content_type="text/plain",
        stream=True,
    )

    responses.add(
        responses.GET,
        "https://baserow.io/not-found.pdf",
        status=404,
    )

    # Could not be reached because it it responds with a 404
    with pytest.raises(FileURLCouldNotBeReached):
        handler.upload_user_file_by_url(
            user, "https://baserow.io/not-found.pdf", storage=storage
        )

    # Only the http and https protocol are supported.
    with pytest.raises(InvalidFileURLError):
        handler.upload_user_file_by_url(
            user, "ftp://baserow.io/not-found.pdf", storage=storage
        )

    with freeze_time("2020-01-01 12:00"):
        user_file = handler.upload_user_file_by_url(
            user, "https://baserow.io/test.txt", storage=storage
        )

    assert user_file.original_name == "test.txt"
    assert user_file.original_extension == "txt"
    assert len(user_file.unique) == 32
    assert user_file.size == 11
    assert user_file.mime_type == "text/plain"
    assert user_file.uploaded_by_id == user.id
    assert user_file.uploaded_at.year == 2020
    assert user_file.uploaded_at.month == 1
    assert user_file.uploaded_at.day == 1
    assert user_file.is_image is False
    assert user_file.image_width is None
    assert user_file.image_height is None
    assert user_file.sha256_hash == (
        "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    )
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()
    assert file_path.open().read() == "Hello World"


@pytest.mark.django_db
def test_upload_user_file_by_url_within_private_network(data_fixture, tmpdir):
    user = data_fixture.create_user()

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    handler = UserFileHandler()

    # Could not be reached because it is an internal private URL.
    with pytest.raises(FileURLCouldNotBeReached):
        handler.upload_user_file_by_url(
            user, "http://localhost/test.txt", storage=storage
        )

    with pytest.raises(FileURLCouldNotBeReached):
        handler.upload_user_file_by_url(
            user, "http://192.168.1.1/test.txt", storage=storage
        )
