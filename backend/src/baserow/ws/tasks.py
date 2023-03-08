from typing import Any, Dict, Iterable, List, Optional

from baserow.config.celery import app


async def closing_group_send(channel_layer, channel, message):
    """
    All channel_layer.*send* methods must have close_pools called after due to a
    bug in channels 4.0.0 as recommended on
    https://github.com/django/channels_redis/issues/332
    """

    await channel_layer.group_send(channel, message)
    if hasattr(channel_layer, "close_pools"):
        # The inmemory channel layer in tests does not have this function.
        await channel_layer.close_pools()


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
    async_to_sync(closing_group_send)(
        channel_layer,
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
def broadcast_to_permitted_users(
    self,
    group_id: int,
    operation_type: str,
    scope_name: str,
    scope_id: int,
    payload: Dict[str, any],
    ignore_web_socket_id: Optional[int] = None,
):
    """
    This task will broadcast a websocket message to all the users that are permitted
    to perform the operation provided.

    :param self:
    :param group_id: The group the users are in
    :param operation_type: The operation that should be checked for
    :param scope_name: The name of the scope that the operation is executed on
    :param scope_id: The id of the scope instance
    :param payload: The message being sent
    :param ignore_web_socket_id: An optional web socket id which will not be sent the
        payload if provided. This is normally the web socket id that has originally
        made the change request.
    :return:
    """

    from baserow.core.handler import CoreHandler
    from baserow.core.mixins import TrashableModelMixin
    from baserow.core.models import Group, GroupUser
    from baserow.core.registries import object_scope_type_registry

    group = Group.objects.get(id=group_id)

    users_in_group = [
        group_user.user
        for group_user in GroupUser.objects.filter(group=group).select_related("user")
    ]

    scope_type = object_scope_type_registry.get(scope_name)
    scope_model_class = scope_type.model_class

    objects = (
        scope_model_class.objects_and_trash
        if issubclass(scope_model_class, TrashableModelMixin)
        else scope_model_class.objects
    )

    scope = objects.get(id=scope_id)

    user_ids = [
        u.id
        for u in CoreHandler().check_permission_for_multiple_actors(
            users_in_group,
            operation_type,
            group,
            context=scope,
        )
    ]

    broadcast_to_users(user_ids, payload, ignore_web_socket_id=ignore_web_socket_id)


@app.task(bind=True)
def broadcast_to_users_individual_payloads(
    self, payload_map: Dict[str, any], ignore_web_socket_id: Optional[int] = None
):
    """
    This task will broadcast different payloads to different users by just using one
    message.

    :param payload_map: A mapping from user_id to the payload that should be sent to
        the user. The id has to be stringified to not violate redis channel policy
    :param ignore_web_socket_id: An optional web socket id which will not be sent the
        payload if provided. This is normally the web socket id that has originally
        made the change request.
    """

    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    async_to_sync(closing_group_send)(
        channel_layer,
        "users",
        {
            "type": "broadcast_to_users_individual_payloads",
            "payload_map": payload_map,
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
    async_to_sync(closing_group_send)(
        channel_layer,
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


@app.task(bind=True)
def broadcast_application_created(
    self, application_id: int, ignore_web_socket_id: Optional[int]
):
    """
    This task is called when an application is created. We made this a task instead of
    running the code in the signal because calculating the individual payloads can take
    a lot of computational power and should therefore not run on a gunicorn worker.

    :param application_id: The id of the application that was created
    :param ignore_web_socket_id: The web socket id to ignore
    :return:
    """

    from baserow.api.applications.serializers import get_application_serializer
    from baserow.core.handler import CoreHandler
    from baserow.core.models import Application, GroupUser
    from baserow.core.operations import ReadApplicationOperationType

    application = Application.objects.get(id=application_id)
    group = application.group
    users_in_group = [
        group_user.user
        for group_user in GroupUser.objects.filter(group=group).select_related("user")
    ]

    user_ids = [
        u.id
        for u in CoreHandler().check_permission_for_multiple_actors(
            users_in_group,
            ReadApplicationOperationType.type,
            group,
            context=application,
        )
    ]

    users_in_group_id_map = {user.id: user for user in users_in_group}

    payload_map = {}
    for user_id in user_ids:
        user = users_in_group_id_map[user_id]
        application_serialized = get_application_serializer(
            application, context={"user": user}
        ).data

        payload_map[str(user_id)] = {
            "type": "application_created",
            "application": application_serialized,
        }

    broadcast_to_users_individual_payloads(payload_map, ignore_web_socket_id)
