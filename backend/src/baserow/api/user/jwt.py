from baserow.api.user.registries import user_data_registry


from .serializers import UserSerializer


def jwt_response_payload_handler(token, user=None, request=None, issued_at=None):
    payload = {
        "token": token,
        "user": UserSerializer(user, context={"request": request}).data,
    }

    # Update the payload with the additional user data that must be added. The
    # `user_data_registry` contains instances that want to add additional information
    # to this payload.
    payload.update(**user_data_registry.get_all_user_data(user, request))

    return payload
