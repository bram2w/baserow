from dataclasses import asdict, dataclass
from typing import Optional
from urllib.parse import urljoin

from django.conf import settings
from django.core.signing import BadSignature, TimestampSigner
from django.urls import reverse
from django.utils.module_loading import import_string

from baserow.core.context import get_current_workspace_id

from .constants import SECURE_FILE_SERVE_SIGNER_SALT


class EnterpriseFileStorageMeta(type):
    def __new__(cls, name, bases, dct):
        base_class = import_string(settings.BASE_FILE_STORAGE)
        return super().__new__(cls, name, (base_class,), dct)


def _get_signer():
    """
    Returns a signer object that can be used to sign and unsign file names.
    """

    return TimestampSigner(salt=SECURE_FILE_SERVE_SIGNER_SALT)


@dataclass
class SecureFileServeSignerPayload:
    name: str
    workspace_id: Optional[int] = None


class EnterpriseFileStorage(metaclass=EnterpriseFileStorageMeta):
    """
    Overrides the default file storage class to provide a way to sign and unsign file
    names. This is used to securely serve files through the backend. The file name is
    signed and then returned as a URL. The URL can be used to download the file. The
    signature is verified before serving the file to ensure that the user has access to
    the file.
    """

    @classmethod
    def sign_data(cls, name: str) -> str:
        """
        Signs the data and returns the signed data.

        :param name: The name of the file to sign.
        :return: The signed data.
        """

        signer = _get_signer()

        workspace_id = get_current_workspace_id()
        return signer.sign_object(
            asdict(SecureFileServeSignerPayload(name, workspace_id))
        )

    @classmethod
    def unsign_data(cls, signed_data: str) -> SecureFileServeSignerPayload:
        """
        Unsign the signed data and returns the payload. If the signature is invalid or
        expired, a BadSignature or SignatureExpired exception is raised.

        :param signed_data: The signed data to unsign.
        :return: The payload extracted from the signed data.
        :raises BadSignature: If the signature is invalid.
        :raises SignatureExpired: If the signature is expired.
        """

        signer = _get_signer()
        try:
            return SecureFileServeSignerPayload(
                **signer.unsign_object(
                    signed_data,
                    max_age=settings.BASEROW_SERVE_FILES_THROUGH_BACKEND_EXPIRE_SECONDS,
                )
            )
        except TypeError:
            raise BadSignature("Malformed payload")

    def get_signed_file_path(self, name: str) -> str:
        """
        Signs the file name and returns the signed file path to the file to serve via
        the backend.

        :param name: The name of the file to sign.
        :return: The signed file path to the file to serve via the backend.
        """

        return reverse(
            "api:enterprise:files:download",
            kwargs={"signed_data": self.sign_data(name)},
        )

    def url(self, name):
        signed_path = self.get_signed_file_path(name)
        return urljoin(settings.PUBLIC_BACKEND_URL, signed_path)
