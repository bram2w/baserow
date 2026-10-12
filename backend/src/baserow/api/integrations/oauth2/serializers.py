from rest_framework import serializers


class OAuth2AuthorizeRequestSerializer(serializers.Serializer):
    return_url = serializers.URLField(
        help_text="The frontend page the browser returns to once the provider "
        "has answered; it receives `oauth2_status` and `oauth2_integration` query "
        "parameters."
    )


class OAuth2AuthorizeResponseSerializer(serializers.Serializer):
    authorization_url = serializers.URLField(
        help_text="The provider's consent page to send the browser to."
    )


class OAuth2CompleteRequestSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text="The authorization code the provider issued."
    )
    state = serializers.CharField(
        help_text="The signed state Baserow put in the consent URL."
    )


class OAuth2CompleteResponseSerializer(serializers.Serializer):
    integration_id = serializers.IntegerField(
        help_text="The integration that is now connected."
    )
    return_url = serializers.URLField(
        help_text="The frontend page the connection was started from."
    )


class OAuth2RedirectUriResponseSerializer(serializers.Serializer):
    redirect_uri = serializers.URLField(
        help_text="The redirect URI to register with the provider's app."
    )
