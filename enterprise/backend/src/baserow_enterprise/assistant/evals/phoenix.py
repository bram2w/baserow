from __future__ import annotations

import os
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

if TYPE_CHECKING:
    from phoenix.client import Client


def get_phoenix_client() -> "Client":
    """Build a Phoenix client using Baserow's configured endpoint."""

    base_url = getattr(settings, "BASEROW_ASSISTANT_PHOENIX_URL", "")
    if not base_url:
        raise ImproperlyConfigured(
            "No Phoenix endpoint configured. Set BASEROW_ASSISTANT_PHOENIX_URL "
            "— see "
            "docs/development/ai-assistant-tracing.md."
        )

    api_key = os.getenv("PHOENIX_API_KEY") or getattr(
        settings, "BASEROW_ASSISTANT_PHOENIX_API_KEY", ""
    )

    from phoenix.client import Client

    return Client(base_url=base_url, api_key=api_key or None)
