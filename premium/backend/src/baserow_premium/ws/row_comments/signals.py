from django.db import transaction
from django.dispatch import receiver

from baserow.ws.registries import page_registry
from baserow_premium.row_comments import signals as row_comment_signals
from baserow_premium.api.row_comments.serializers import (
    RowCommentSerializer,
)


@receiver(row_comment_signals.row_comment_created)
def row_comment_created(sender, row_comment, user, **kwargs):
    table_page_type = page_registry.get("table")
    transaction.on_commit(
        lambda: table_page_type.broadcast(
            {
                "type": "row_comment_created",
                "row_comment": RowCommentSerializer(row_comment).data,
            },
            getattr(user, "web_socket_id", None),
            table_id=row_comment.table.id,
        )
    )
