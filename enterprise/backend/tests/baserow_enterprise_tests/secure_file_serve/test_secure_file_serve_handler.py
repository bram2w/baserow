from unittest import mock

from django.core.signing import SignatureExpired
from django.test import override_settings

import pytest

from baserow_enterprise.secure_file_serve.constants import SecureFileServePermission
from baserow_enterprise.secure_file_serve.exceptions import SecureFileServeException
from baserow_enterprise.secure_file_serve.handler import (
    SecureFile,
    SecureFileServeHandler,
)
from baserow_enterprise.secure_file_serve.storage import (
    EnterpriseFileStorage,
    SecureFileServeSignerPayload,
)


def test_secure_file_handler_unsign_data_invalid_payload():
    for payload in [None, "", "invalid_payload"]:
        handler = SecureFileServeHandler()

        with pytest.raises(SecureFileServeException) as error:
            handler.unsign_data(signed_path=payload)
            assert str(error.value) == "Invalid signature"


@mock.patch("baserow_enterprise.secure_file_serve.handler.EnterpriseFileStorage")
def test_secure_file_handler_unsign_data_expired_payload(mocked_storage):
    mocked_storage.unsign_data.side_effect = SignatureExpired()

    handler = SecureFileServeHandler()
    storage = EnterpriseFileStorage()
    signed_data = storage.sign_data(name="path/to/file.txt")

    with pytest.raises(SecureFileServeException) as error:
        handler.unsign_data(signed_path=signed_data)
        assert str(error.value) == "File expired"


def test_secure_file_handler_unsign_valid_data():
    handler = SecureFileServeHandler()
    storage = EnterpriseFileStorage()
    signed_data = storage.sign_data(name="path/to/file.txt")
    expected_payload = SecureFileServeSignerPayload(
        name="path/to/file.txt", workspace_id=None
    )

    payload = handler.unsign_data(signed_path=signed_data)
    assert payload == expected_payload


def test_secure_file_handler_get_file_path_exists():
    handler = SecureFileServeHandler()

    data = SecureFileServeSignerPayload(name="path/to/file.txt", workspace_id=None)

    with mock.patch(
        "baserow_enterprise.secure_file_serve.handler.default_storage"
    ) as mocked_default_storage:
        mocked_default_storage.exists.return_value = True
        file_path = handler.get_file_path(data=data)
        assert file_path == data.name


def test_secure_file_handler_get_file_path_does_not_exist():
    handler = SecureFileServeHandler()

    data = SecureFileServeSignerPayload(name="path/to/file.txt", workspace_id=None)

    with mock.patch(
        "baserow_enterprise.secure_file_serve.handler.default_storage"
    ) as mocked_default_storage:
        mocked_default_storage.exists.return_value = False
        with pytest.raises(SecureFileServeException) as error:
            handler.get_file_path(data=data)
            assert str(error.value) == "File not found"


def test_secure_file_handler_get_file_name():
    handler = SecureFileServeHandler()

    scenarios = [
        (None, ""),
        ("", ""),
        ("path/to/file.txt", "file.txt"),
        ("file.txt", "file.txt"),
    ]

    for given_path, expected_name in scenarios:
        assert handler.get_file_name(given_path) == expected_name


def test_secure_file_handler_extract_file_info_or_raise_invalid_payload():
    handler = SecureFileServeHandler()

    with pytest.raises(SecureFileServeException) as error:
        handler.extract_file_info_or_raise(user=None, signed_data="")
        assert str(error.value) == "Invalid signature"


@pytest.mark.django_db
@override_settings(
    BASEROW_SERVE_FILES_THROUGH_BACKEND_PERMISSION=SecureFileServePermission.DISABLED
)
def test_secure_file_handler_extract_file_info_or_raise_non_existing_file():
    handler = SecureFileServeHandler()

    with mock.patch(
        "baserow_enterprise.secure_file_serve.handler.default_storage"
    ) as mocked_default_storage:
        mocked_default_storage.exists.return_value = False

        with pytest.raises(SecureFileServeException) as error:
            handler.extract_file_info_or_raise(user=None, signed_data="")
            assert str(error.value) == "File not found"


@pytest.mark.django_db
@override_settings(
    BASEROW_SERVE_FILES_THROUGH_BACKEND_PERMISSION=SecureFileServePermission.DISABLED
)
def test_secure_file_handler_extract_file_info_or_raise_valid_data():
    handler = SecureFileServeHandler()

    storage = EnterpriseFileStorage()
    signed_data = storage.sign_data(name="path/to/file.txt")

    with mock.patch(
        "baserow_enterprise.secure_file_serve.handler.default_storage"
    ) as mocked_default_storage:
        mocked_default_storage.exists.return_value = True

        secure_file = handler.extract_file_info_or_raise(
            user=None, signed_data=signed_data
        )
        assert isinstance(secure_file, SecureFile)
        assert secure_file.name == "file.txt"
        assert secure_file.path == "path/to/file.txt"
