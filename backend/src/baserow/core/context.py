"""
This module handles the storage of request-specific variables, particularly:

* workspace_id: Represents the ID of the current workspace related to the request.
    This ID can be utilized by storage backends to generate URLs specific to the
    workspace.
"""

from asgiref.local import Local

_thread_locals = Local()


def get_current_workspace_id():
    return getattr(_thread_locals, "workspace_id", None)


def set_current_workspace_id(workspace_id):
    # FIXME: Temporarily setting the current workspace ID for URL generation in
    # storage backends, enabling permission checks at download time.
    _thread_locals.workspace_id = workspace_id


def clear_current_workspace_id():
    _thread_locals.workspace_id = None
