from django.conf import settings
from django.core.signing import BadSignature

import pytest

from baserow.core.context import clear_current_workspace_id, set_current_workspace_id
from baserow_enterprise.secure_file_serve.storage import (
    EnterpriseFileStorage,
    SecureFileServeSignerPayload,
)


def test_enterprise_storage_sign_data():
    storage = EnterpriseFileStorage()
    names = [None, "", "path/to/file.txt"]
    for name in names:
        signed_data = storage.sign_data(name=name)
        assert isinstance(signed_data, str)
        payload = storage.unsign_data(signed_data=signed_data)
        assert isinstance(payload, SecureFileServeSignerPayload)
        assert payload.name == name
        assert payload.workspace_id is None


def test_enterprise_storage_sign_data_with_workspace_id():
    storage = EnterpriseFileStorage()
    name = "path/to/file.txt"

    set_current_workspace_id(1)
    signed_data = storage.sign_data(name=name)
    assert isinstance(signed_data, str)
    payload = storage.unsign_data(signed_data=signed_data)
    assert isinstance(payload, SecureFileServeSignerPayload)
    assert payload.name == name
    assert payload.workspace_id == 1
    clear_current_workspace_id()


def test_enterprise_storage_unsign_data_with_invalid_payload():
    storage = EnterpriseFileStorage()
    signed_data_samples = [None, "", "invalid_payload"]

    for signed_data in signed_data_samples:
        with pytest.raises(BadSignature):
            storage.unsign_data(signed_data=signed_data)


def test_enterprise_storage_get_signed_file_path():
    storage = EnterpriseFileStorage()
    for name in [None, "", "path/to/file.txt"]:
        signed_file_path = storage.get_signed_file_path(name=name)
        assert isinstance(signed_file_path, str)


def test_enterprise_storage_url():
    storage = EnterpriseFileStorage()
    for name in [None, "", "path/to/file.txt"]:
        signed_file_path = storage.url(name=name)
        assert isinstance(signed_file_path, str)
        assert signed_file_path.startswith(settings.PUBLIC_BACKEND_URL)
