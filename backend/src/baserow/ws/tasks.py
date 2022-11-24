from typing import Any, Dict, Iterable, List, Optional

from baserow.config.celery import app


@app.task(bind=True)
def broadcast_to_users(
    self,
    user_ids: List[int],
    payload: Dict[Any, Any],
    ignore_web_socket_id: Optional[int] = None,
    send_to_all_users: bool = False,
):
    """
    Broadcasts a JSON payload the provided users.

    :param user_ids: A list containing the user ids that will be sent the payload.
    :param payload: A dictionary object containing the payload that will be
        broadcast.
    :param ignore_web_socket_id: An optional web socket id which will not be sent the
        payload if provided. This is normally the web socket id that has originally
        made the change request.
    :param send_to_all_users: If set to True all users will be sent the payload and
        the user_ids parameter will be ignored. ignore_web_socket_id however will still
        be respected.
    """

    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "users",
        {
            "type": "broadcast_to_users",
            "user_ids": user_ids,
            "payload": payload,
            "ignore_web_socket_id": ignore_web_socket_id,
            "send_to_all_users": send_to_all_users,
        },
    )


@app.task(bind=True)
def broadcast_to_channel_group(self, group, payload, ignore_web_socket_id=None):
    """
    Broadcasts a JSON payload all the users within the channel group having the
    provided name.

    :param group: The name of the channel group where the payload must be broad casted
        to.
    :type group: str
    :param payload: A dictionary object containing the payload that must be
        broadcasted.
    :type payload: dict
    :param ignore_web_socket_id: The web socket id to which the message must not be
        send. This is normally the web socket id that has originally made the change
        request.
    :type ignore_web_socket_id: str
    """

    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "broadcast_to_group",
            "payload": payload,
            "ignore_web_socket_id": ignore_web_socket_id,
        },
    )


@app.task(bind=True)
def broadcast_to_group(self, group_id, payload, ignore_web_socket_id=None):
    """
    Broadcasts a JSON payload to all users that are in provided group (Group model) id.

    :param group_id: The message will only be broadcasted to the users within the
        provided group id.
    :type group_id: int
    :param payload: A dictionary object containing the payload that must be
        broadcasted.
    :type payload: dict
    :param ignore_web_socket_id: The web socket id to which the message must not be
        send. This is normally the web socket id that has originally made the change
        request.
    :type ignore_web_socket_id: str
    """

    from baserow.core.models import GroupUser

    user_ids = [
        user["user_id"]
        for user in GroupUser.objects.filter(group_id=group_id).values("user_id")
    ]

    if len(user_ids) == 0:
        return

    broadcast_to_users(user_ids, payload, ignore_web_socket_id)


@app.task(bind=True)
def broadcast_to_groups(
    self, group_ids: Iterable[int], payload: dict, ignore_web_socket_id: str = None
):
    """
    Broadcasts a JSON payload to all users that are in the provided groups.

    :param group_ids: Ids of groups to broadcast to.
    :param payload: A dictionary object containing the payload that must be
        broadcasted.
    :param ignore_web_socket_id: The web socket id to which the message must not be
        sent. This is normally the web socket id that has originally made the change
        request.
    """

    from baserow.core.models import GroupUser

    user_ids = list(
        GroupUser.objects.filter(group_id__in=group_ids)
        .distinct("user_id")
        .order_by("user_id")
        .values_list("user_id", flat=True)
    )

    if len(user_ids) == 0:
        return

    broadcast_to_users(user_ids, payload, ignore_web_socket_id)
