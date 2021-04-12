from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from baserow.ws.registries import page_registry


class CoreConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

        user = self.scope["user"]
        web_socket_id = self.scope["web_socket_id"]

        await self.send_json(
            {
                "type": "authentication",
                "success": user is not None,
                "web_socket_id": web_socket_id,
            }
        )

        if not user:
            await self.close()
            return

        await self.channel_layer.group_add("users", self.channel_name)

    async def receive_json(self, content, **parameters):
        if "page" in content:
            await self.add_to_page(content)

    async def add_to_page(self, content):
        """
        Subscribes the connection to a page abstraction. Based on the provided the page
        type we can figure out to which page the connection wants to subscribe to. This
        is for example used when the users visits a page that he might want to
        receive real time updates for.

        :param content: The provided payload by the user. This should contain the page
            type and additional parameters.
        :type content: dict
        """

        user = self.scope["user"]
        web_socket_id = self.scope["web_socket_id"]

        if not user:
            return

        # If the user has already joined another page we need to discard that
        # page first before we can join a new one.
        await self.discard_current_page()

        try:
            page_type = page_registry.get(content["page"])
        except page_registry.does_not_exist_exception_class:
            return

        parameters = {
            parameter: content.get(parameter) for parameter in page_type.parameters
        }

        can_add = await database_sync_to_async(page_type.can_add)(
            user, web_socket_id, **parameters
        )

        if not can_add:
            return

        group_name = page_type.get_group_name(**parameters)
        await self.channel_layer.group_add(group_name, self.channel_name)
        self.scope["page"] = page_type
        self.scope["page_parameters"] = parameters

        await self.send_json(
            {"type": "page_add", "page": page_type.type, "parameters": parameters}
        )

    async def discard_current_page(self, send_confirmation=True):
        """
        If the user has subscribed to another page then he will be unsubscribed from
        the last page.
        """

        page = self.scope.get("page")
        if not page:
            return

        page_type = page.type
        page_parameters = self.scope["page_parameters"]

        group_name = page.get_group_name(**self.scope["page_parameters"])
        await self.channel_layer.group_discard(group_name, self.channel_name)
        del self.scope["page"]
        del self.scope["page_parameters"]

        if send_confirmation:
            await self.send_json(
                {
                    "type": "page_discard",
                    "page": page_type,
                    "parameters": page_parameters,
                }
            )

    async def broadcast_to_users(self, event):
        """
        Broadcasts a message to all the users that are in the provided user_ids list.
        Optionally the ignore_web_socket_id is ignored because that is often the
        sender.

        :param event: The event containing the payload, user ids and the web socket
            id that must be ignored.
        :type event: dict
        """

        web_socket_id = self.scope["web_socket_id"]
        payload = event["payload"]
        user_ids = event["user_ids"]
        ignore_web_socket_id = event["ignore_web_socket_id"]

        if (
            not ignore_web_socket_id or ignore_web_socket_id != web_socket_id
        ) and self.scope["user"].id in user_ids:
            await self.send_json(payload)

    async def broadcast_to_group(self, event):
        """
        Broadcasts a message to all the users that are in the provided group name.

        :param event: The event containing the payload, group name and the web socket
            id that must be ignored.
        :type event: dict
        """

        web_socket_id = self.scope["web_socket_id"]
        payload = event["payload"]
        ignore_web_socket_id = event["ignore_web_socket_id"]

        if not ignore_web_socket_id or ignore_web_socket_id != web_socket_id:
            await self.send_json(payload)

    async def disconnect(self, message):
        await self.discard_current_page(send_confirmation=False)
        await self.channel_layer.group_discard("users", self.channel_name)
