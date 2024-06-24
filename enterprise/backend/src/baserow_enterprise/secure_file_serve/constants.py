from enum import Enum


class SecureFileServePermission(Enum):
    DISABLED = "DISABLED"
    SIGNED_IN = "SIGNED_IN"
    WORKSPACE_ACCESS = "WORKSPACE_ACCESS"


SECURE_FILE_SERVE_SIGNER_SALT = "secure_file_serve"
