from baserow.config.celery import app


@app.task(bind=True)
def broadcast_to_users(self, user_ids, payload, ignore_web_socket_id=None):
    """
    Broadcasts a JSON payload the provided users.

    :param user_ids: A list containing the user ids that should receive the payload.
    :type user_ids: list
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
        "users",
        {
            "type": "broadcast_to_users",
            "user_ids": user_ids,
            "payload": payload,
            "ignore_web_socket_id": ignore_web_socket_id,
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
