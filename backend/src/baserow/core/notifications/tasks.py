from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db import transaction

from baserow.api.notifications.serializers import NotificationRecipientSerializer
from baserow.config.celery import app
from baserow.ws.tasks import broadcast_to_users

User = get_user_model()


@app.task(bind=True)
def send_queued_notifications_to_users(self):
    from .models import NotificationRecipient

    with transaction.atomic():
        queued_notificationrecipients = (
            NotificationRecipient.objects.filter(queued=True)
            .select_related("notification", "notification__sender")
            .order_by("recipient_id", "-created_on")
            .select_for_update(of=("notification",), skip_locked=True)
        )

        notifications_grouped_by_user = defaultdict(list)
        notifications_count_per_user_and_workspace = defaultdict(
            lambda: defaultdict(int)
        )
        for notification_recipient in queued_notificationrecipients:
            user_id = notification_recipient.recipient_id
            notifications_grouped_by_user[user_id].append(notification_recipient)
            notifications_count_per_user_and_workspace[user_id][
                notification_recipient.notification.workspace_id
            ] += 1

        if not notifications_grouped_by_user:
            return

        def broadcast_all_notifications_at_once_to_user(
            notification_batch_limit=20,
        ):
            for user_id, notifications in notifications_grouped_by_user.items():
                if len(notifications) <= notification_batch_limit:
                    broadcast_to_users.apply(
                        (
                            [user_id],
                            {
                                "type": "notifications_created",
                                "notifications": NotificationRecipientSerializer(
                                    notifications, many=True
                                ).data,
                            },
                        )
                    )
                else:
                    per_workspace_added_count = [
                        {"workspace_id": k, "count": v}
                        for k, v in notifications_count_per_user_and_workspace[
                            user_id
                        ].items()
                    ]
                    broadcast_to_users.apply(
                        (
                            [user_id],
                            {
                                "type": "notifications_fetch_required",
                                "notifications_added": per_workspace_added_count,
                            },
                        )
                    )

        transaction.on_commit(broadcast_all_notifications_at_once_to_user)

        queued_notificationrecipients.update(queued=False)
