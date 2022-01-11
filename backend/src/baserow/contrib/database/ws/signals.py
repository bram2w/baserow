from django.conf import settings

from .table.signals import table_created, table_updated, table_deleted
from .views.signals import view_created, views_reordered, view_updated, view_deleted
from .rows.signals import row_created, row_updated, row_deleted
from .fields.signals import field_created, field_updated, field_deleted

if settings.DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS:
    PUBLIC_SIGNALS = []
else:
    # noinspection PyUnresolvedReferences
    from .public.rows.signals import (  # noqa: F401
        public_row_created,
        public_row_deleted,
        public_row_updated,
    )

    # noinspection PyUnresolvedReferences
    from .public.views.signals import (  # noqa: F401
        public_view_filter_created,
        public_view_filter_deleted,
        public_view_filter_updated,
        public_view_updated,
        public_view_field_options_updated,
    )

    # noinspection PyUnresolvedReferences
    from .public.fields.signals import (  # noqa: F401
        public_field_created,
        public_field_deleted,
        public_field_updated,
        public_field_restored,
    )

    PUBLIC_SIGNALS = [
        "public_row_created",
        "public_row_deleted",
        "public_row_updated",
        "public_view_filter_updated",
        "public_view_filter_deleted",
        "public_view_filter_created",
        "public_view_updated",
        "public_view_field_options_updated",
        "public_field_created",
        "public_field_deleted",
        "public_field_updated",
        "public_field_restored",
    ]

__all__ = [
    "table_created",
    "table_updated",
    "table_deleted",
    "views_reordered",
    "view_created",
    "view_updated",
    "view_deleted",
    "row_created",
    "row_updated",
    "row_deleted",
    "field_created",
    "field_updated",
    "field_deleted",
    *PUBLIC_SIGNALS,
]
