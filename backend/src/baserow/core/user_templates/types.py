from dataclasses import dataclass
from typing import List, TypedDict


class TemplateMetadata(TypedDict, total=False):
    """
    The private metadata of a template revision, only shown to its owner. It's
    read and written through `UserTemplateHandler` only.
    """

    # The workspace the applications of the revision were copied from.
    source_workspace_id: int
    # The ids of the applications the revision was copied from.
    source_application_ids: List[int]


@dataclass
class TemplateDownload:
    """
    What a user downloads of a user template: the stored archive of the revision
    they would install. The storage URL is built by the API.
    """

    # The name of the archive in the default storage.
    archive_name: str
    # The name to save the file as.
    file_name: str
    # The workspace the storage URL is signed with, so that enterprise secure file
    # serve can check access when the file is downloaded.
    url_workspace_id: int
