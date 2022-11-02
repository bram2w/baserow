import base64
import binascii
import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser

from defusedxml import ElementTree
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT, entity
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from saml2.response import AuthnResponse

from baserow_enterprise.api.sso.utils import (
    get_saml_acs_absolute_url,
    get_valid_relay_state_url,
)
from baserow_enterprise.auth_provider.handler import AuthProviderHandler, UserInfo
from baserow_enterprise.sso.saml.models import SamlAuthProviderModel

from .exceptions import (
    InvalidSamlConfiguration,
    InvalidSamlRequest,
    InvalidSamlResponse,
)

logger = logging.getLogger(__name__)


class SamlAuthProviderHandler:
    @classmethod
    def get_saml_client(
        cls,
        identity_provider_metadata: str,
    ) -> Saml2Client:
        """
        Returns a SAML client with the correct configuration for the given
        authentication provider.

        :param assertion_consumer_service_url: The url that should be used as
            the assertion consumer service url.
        :param saml_auth_provider: The authentication provider that needs to be
            used to authenticate the user.
        :return: The SAML client that can be used to authenticate the user.
        """

        acs_url = get_saml_acs_absolute_url()

        saml_settings: Dict[str, Any] = {
            "entityid": acs_url,
            "metadata": {"inline": [identity_provider_metadata]},
            "allow_unknown_attributes": True,
            "debug": settings.DEBUG,
            "service": {
                "sp": {
                    "endpoints": {
                        "assertion_consumer_service": [
                            (acs_url, BINDING_HTTP_REDIRECT),
                            (acs_url, BINDING_HTTP_POST),
                        ],
                    },
                    "allow_unsolicited": True,
                    "authn_requests_signed": False,
                    "logout_requests_signed": True,
                    "want_assertions_signed": False,
                    "want_response_signed": False,
                },
            },
        }
        sp_config = Saml2Config()
        sp_config.load(saml_settings)
        return Saml2Client(config=sp_config)

    @classmethod
    def check_authn_response_is_valid_or_raise(cls, authn_response: AuthnResponse):
        """
        Checks if the authn response is valid and raises an exception if not.

        :param authn_response: The authn response that should be checked.
        :raises InvalidSamlResponse: When the authn response is not valid.
        :return: True if the authn response is valid.
        """

        if not authn_response:
            raise InvalidSamlResponse(
                "There was no response from SAML identity provider."
            )

        if not authn_response.name_id:
            raise InvalidSamlResponse("No name_id in SAML response.")

        if not authn_response.issuer():
            raise InvalidSamlResponse("No issuer/entity_id in SAML response.")

        if not authn_response.get_identity():
            raise InvalidSamlResponse("No user identity in SAML response.")

    @classmethod
    def get_saml_auth_provider_from_saml_response(
        cls,
        saml_raw_response: str,
    ) -> SamlAuthProviderModel:
        """
        Parses the saml response and returns the authentication provider that needs to
        be used to authenticate the user.

        :param saml_raw_response: The raw saml response that was received from the
            identity provider.
        :raises InvalidSamlResponse: When the saml response is not valid.
        :raises InvalidSamlConfiguration: When the correct authentication provider is
            not found in the system based on the information of saml response received.
        :return: The authentication provider that needs to be used to authenticate the
            user.
        """

        try:
            decoded_saml_response = ElementTree.fromstring(
                base64.b64decode(saml_raw_response).decode("utf-8")
            )
            issuer = decoded_saml_response.find(
                "{urn:oasis:names:tc:SAML:2.0:assertion}Issuer"
            ).text
        except (binascii.Error, ElementTree.ParseError, AttributeError):
            raise InvalidSamlResponse("Impossible decode SAML response.")

        saml_auth_provider = SamlAuthProviderModel.objects.filter(
            enabled=True, metadata__contains=issuer
        ).first()
        if not saml_auth_provider:
            raise InvalidSamlConfiguration("SAML auth provider not found.")
        return saml_auth_provider

    @classmethod
    def get_user_identity_from_authn_response(
        cls,
        authn_response: AuthnResponse,
    ) -> Dict[str, Any]:
        """
        Extracts the user identity from the authn response and return a dict that
        can be sent to the UserHandler to create or update the user.

        :param authn_response: The authn response that contains the user identity.
        :return: A dictionary containing the user info that can be sent to the
            UserHandler.create_user() method.
        """

        user_identity = authn_response.get_identity()
        email = user_identity["user.email"][0]
        if "user.name" in user_identity:
            name = user_identity["user.name"][0]
        else:
            first_name = user_identity["user.first_name"][0]
            if "user.last_name" in user_identity:
                last_name = user_identity["user.last_name"][0]
            else:
                last_name = ""
            name = f"{first_name} {last_name}".strip()
        return UserInfo(email, name)

    @classmethod
    def get_saml_auth_provider_from_email(
        cls,
        email: Optional[str] = None,
    ) -> SamlAuthProviderModel:
        """
        It returns the Saml Identity Provider for the the given email address.
        If the email address and only one IdP is configured, it returns that IdP.

        :param email: The email address of the user.
        :raises InvalidSamlRequest: If there is no Saml Identity Provider for the domain
            or the email is invalid.
        :return: The Saml Identity Provider for the domain of the email address.
        """

        base_queryset = SamlAuthProviderModel.objects.filter(enabled=True)

        if email is not None:
            try:
                domain = email.rsplit("@", 1)[1]
            except IndexError:
                raise InvalidSamlRequest("Invalid mail address provided.")
            base_queryset = base_queryset.filter(domain=domain)

        try:
            return base_queryset.get()
        except (
            SamlAuthProviderModel.DoesNotExist,
            SamlAuthProviderModel.MultipleObjectsReturned,
        ):
            raise InvalidSamlRequest("No valid SAML identity provider found.")

    @classmethod
    def sign_in_user_from_saml_response(cls, saml_response: str) -> AbstractUser:
        """
        Signs in the user using the SAML response received from the identity
        provider.

        :param saml_response: The encoded SAML response sent from the Identity
            Provider.
        :raises InvalidSamlResponse: When the SAML response is not valid.
        :raises InvalidSamlConfiguration: When the SAML configuration is not
            valid.
        :return: The user that was signed in.
        """

        if saml_response is None:
            raise InvalidSamlRequest(
                "SAML response is missing. Verify the SAML provider configuration."
            )

        try:
            saml_auth_provider = cls.get_saml_auth_provider_from_saml_response(
                saml_response
            )

            saml_client = cls.get_saml_client(saml_auth_provider.metadata)
            authn_response = saml_client.parse_authn_request_response(
                saml_response, entity.BINDING_HTTP_POST
            )
            cls.check_authn_response_is_valid_or_raise(authn_response)
            idp_provided_user_info = cls.get_user_identity_from_authn_response(
                authn_response
            )
        except (InvalidSamlConfiguration, InvalidSamlResponse) as exc:
            raise exc
        except Exception as exc:
            logger.exception(exc)
            raise InvalidSamlResponse(str(exc))

        user = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
            idp_provided_user_info, saml_auth_provider
        )

        # since we correctly sign in a user, we can set this IdP as verified
        # This means it can be used as unique authentication provider form now on
        if not saml_auth_provider.is_verified:
            saml_auth_provider.is_verified = True
            saml_auth_provider.save()

        return user

    @classmethod
    def get_sign_in_url_for_auth_provider(
        cls,
        saml_auth_provider: SamlAuthProviderModel,
        original_url: str = "",
    ) -> str:
        """
        Returns the redirect url to the identity provider. This url is used to
        initiate the SAML authentication flow from the service provider.

        :param saml_auth_provider: The identity provider to which the user
            should be redirected.
        :param acs_url: The assertion consumer service endpoint where the
            identity provider will send the SAML response.
        :param original_url: The url to which the user should be redirected
            after a successful login.
        :raises InvalidSamlConfiguration: If the SAML configuration is invalid.
        :return: The redirect url to the identity provider.
        """

        saml_client = cls.get_saml_client(saml_auth_provider.metadata)
        _, info = saml_client.prepare_for_authenticate(relay_state=original_url)

        for key, value in info["headers"]:
            if key == "Location":
                redirect_url = value
                return redirect_url
        else:
            raise InvalidSamlConfiguration("No Location header found in SAML response.")

    @classmethod
    def get_sign_in_url(cls, user_email: str, original_url: str = "") -> str:
        """
        Returns the sign in url for the correct identity provider. This url is
        used to initiate the SAML authentication flow from the service provider.

        :param user_email: The email address of the user that wants to login.
        :param original_url: The url to which the user would be redirected
            after a successful login.
        :raises InvalidSamlRequest: If the email address is invalid.
        :raises InvalidSamlConfiguration: If the SAML configuration is invalid.
        :return: The redirect url to the identity provider.
        """

        valid_relay_state_url = get_valid_relay_state_url(original_url)

        try:
            saml_auth_provider = cls.get_saml_auth_provider_from_email(user_email)
            return cls.get_sign_in_url_for_auth_provider(
                saml_auth_provider, valid_relay_state_url
            )
        except (InvalidSamlRequest, InvalidSamlConfiguration) as exc:
            raise exc
        except Exception as exc:
            logger.exception(exc)
            raise InvalidSamlRequest(str(exc))
