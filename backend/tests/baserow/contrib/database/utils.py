import asyncio

from channels.testing import WebsocketCommunicator


async def received_message(communicator: WebsocketCommunicator, message_type: str):
    """
    Can be called to check if a specific type of message has been sent
    to a communicator.

    :param communicator: The communicator receiving the message
    :param message_type: The type of message you are looking for
    :returns: If the message has been received
    """

    return await get_message(communicator, message_type) is not None


async def get_message(communicator: WebsocketCommunicator, message_type: str):
    """
    Can be called to find the next message of the specified type

    :param communicator: The communicator receiving the message
    :param message_type: The type of message you are looking for
    :return: The received message
    """

    while True:
        try:
            message = await communicator.receive_json_from()
            if message["type"] == message_type:
                return message
        except asyncio.exceptions.TimeoutError:  # No more messages
            return None
