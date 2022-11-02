import logging
import urllib
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from django.conf import settings
from django.urls import reverse

import requests
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix

from baserow.api.utils import ExceptionMappingType
from baserow.core.auth_provider.auth_provider_types import AuthProviderType
from baserow.core.auth_provider.models import AuthProviderModel
from baserow_enterprise.api.sso.oauth2.errors import ERROR_INVALID_PROVIDER_URL
from baserow_enterprise.auth_provider.handler import UserInfo
from baserow_enterprise.sso.exceptions import AuthFlowError, InvalidProviderUrl
from baserow_enterprise.sso.utils import is_sso_feature_active

from .models import (
    FacebookAuthProviderModel,
    GitHubAuthProviderModel,
    GitLabAuthProviderModel,
    GoogleAuthProviderModel,
    OpenIdConnectAuthProviderModel,
)

OAUTH_BACKEND_URL = settings.PUBLIC_BACKEND_URL


logger = logging.getLogger(__name__)


@dataclass
class WellKnownUrls:
    authorization_url: str
    access_token_url: str
    user_info_url: str


class OAuth2AuthProviderMixin:
    """
    Mixin that can be used together with a subclass of AuthProviderType
    to reuse some common OAuth2 logic.

    Expects the following to be set:
    - self.type
    - self.model_class
    - self.AUTHORIZATION_URL
    - self.SCOPE
    """

    def can_create_new_providers(self):
        return True

    def get_login_options(self, **kwargs) -> Optional[Dict[str, Any]]:
        if not is_sso_feature_active():
            return {}

        instances = self.model_class.objects.all()
        items = []
        for instance in instances:
            if instance.enabled:
                items.append(
                    {
                        "redirect_url": urllib.parse.urljoin(
                            OAUTH_BACKEND_URL,
                            reverse(
                                "api:enterprise:sso:oauth2:login", args=(instance.id,)
                            ),
                        ),
                        "name": instance.name,
                        "type": self.type,
                    }
                )
        return {
            "type": self.type,
            "items": items,
        }

    def get_base_url(self, instance: AuthProviderModel) -> str:
        """
        Returns base URL for the provider instance.

        :param instance: A subclass of AuthProviderModel for which to
            return base URL.
        :return: Base URL.
        """

        return self.AUTHORIZATION_URL

    def get_authorization_url(self, instance: AuthProviderModel) -> str:
        """
        Generates authorization URL for the instance provider that will
        start OAuth2 login flow.

        :param instance: A subclass of AuthProviderModel for which to
            generate the login URL.
        :return: URL that will redirect user to the provider's login
            page.
        """

        oauth = self.get_oauth_session(instance)
        authorization_url, state = oauth.authorization_url(self.get_base_url(instance))
        return authorization_url

    def get_oauth_session(self, instance: AuthProviderModel) -> OAuth2Session:
        """
        Creates OAuth2Session client to be used to interact with the provider
        during OAuth2 flow.

        :param instance: A subclass of AuthProviderModel for which to
            create the session client.
        :return: HTTP client with the correct session.
        """

        redirect_uri = urllib.parse.urljoin(
            OAUTH_BACKEND_URL,
            reverse("api:enterprise:sso:oauth2:callback", args=(instance.id,)),
        )
        return OAuth2Session(
            instance.client_id, redirect_uri=redirect_uri, scope=self.SCOPE
        )


class GoogleAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The Google authentication provider type allows users to
    login using OAuth2 through Google.
    """

    type = "google"
    model_class = GoogleAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "client_id", "secret"]

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    SCOPE = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    ACCESS_TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"  # nosec B105
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"  # nosec B105

    def get_user_info(self, instance: GoogleAuthProviderModel, code: str) -> UserInfo:
        """
        Queries the provider to obtain user info data (name and email).

        :param instance: Provider model that will be used to retrieve the user
            info.
        :param code: The security code that was passed from the provider to
            the callback endpoint.
        :raises AuthFlowError if the provider is unavailable, misconfigured or
            the provided code is not valid.
        :return: User info with user's name and email.
        """

        try:
            oauth = self.get_oauth_session(instance)
            oauth.fetch_token(
                self.ACCESS_TOKEN_URL,
                code=code,
                client_secret=instance.secret,
            )
            response = oauth.get(self.USER_INFO_URL)
            name = response.json().get("name", None)
            email = response.json().get("email", None)
            return UserInfo(name=name, email=email)
        except Exception as exc:
            logger.exception(exc)
            raise AuthFlowError()


class GitHubAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The Github authentication provider type allows users to
    login using OAuth2 through Github.
    """

    type = "github"
    model_class = GitHubAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "client_id", "secret"]

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    SCOPE = "read:user,user:email"

    ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # nosec B105
    USER_INFO_URL = "https://api.github.com/user"  # nosec B105
    EMAILS_URL = "https://api.github.com/user/emails"

    def get_user_info(self, instance: GitHubAuthProviderModel, code: str) -> UserInfo:
        """
        Queries the provider to obtain user info data (name and email).

        :param instance: Provider model that will be used to retrieve the user
            info.
        :param code: The security code that was passed from the provider to
            the callback endpoint.
        :raises AuthFlowError if the provider is unavailable, misconfigured or
            the provided code is not valid.
        :return: User info with user's name and email.
        """

        try:
            oauth = self.get_oauth_session(instance)
            token = oauth.fetch_token(
                self.ACCESS_TOKEN_URL,
                code=code,
                client_secret=instance.secret,
            )
            response = oauth.get(self.USER_INFO_URL)
            name = response.json().get("name", None)
            email = self.get_email(
                {"Authorization": "token {}".format(token.get("access_token"))},
            )
            return UserInfo(name=name, email=email)
        except Exception as exc:
            logger.exception(exc)
            raise AuthFlowError()

    def get_email(self, headers) -> str:
        """
        Helper method to obtain user's email from GitHub.

        :param headers: Authorization headers that will authorize the request.
        :return: User's email.
        """

        email = None
        resp = requests.get(self.EMAILS_URL, headers=headers)
        resp.raise_for_status()
        emails = resp.json()
        if resp.status_code == 200 and emails:
            email = emails[0]
            primary_emails = [
                e for e in emails if not isinstance(e, dict) or e.get("primary")
            ]
            if primary_emails:
                email = primary_emails[0]
            if isinstance(email, dict):
                email = email.get("email", "")
        return email


class GitLabAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The GitLab authentication provider type allows users to
    login using OAuth2 through GitLab.
    """

    type = "gitlab"
    model_class = GitLabAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "base_url", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "base_url", "client_id", "secret"]

    AUTHORIZATION_PATH = "/oauth/authorize"
    SCOPE = ["read_user"]

    ACCESS_TOKEN_PATH = "/oauth/token"  # nosec B105
    USER_INFO_PATH = "/api/v4/user"  # nosec B105

    def get_base_url(self, instance: AuthProviderModel) -> str:
        return f"{instance.base_url}{self.AUTHORIZATION_PATH}"

    def get_user_info(self, instance: GitLabAuthProviderModel, code: str) -> UserInfo:
        """
        Queries the provider to obtain user info data (name and email).

        :param instance: Provider model that will be used to retrieve the user
            info.
        :param code: The security code that was passed from the provider to
            the callback endpoint.
        :raises AuthFlowError if the provider is unavailable, misconfigured or
            the provided code is not valid.
        :return: User info with user's name and email.
        """

        try:
            oauth = self.get_oauth_session(instance)
            oauth.fetch_token(
                instance.base_url + self.ACCESS_TOKEN_PATH,
                code=code,
                client_secret=instance.secret,
            )
            response = oauth.get(instance.base_url + self.USER_INFO_PATH)
            name = response.json().get("name", None)
            email = response.json().get("email", None)
            return UserInfo(name=name, email=email)
        except Exception as exc:
            logger.exception(exc)
            raise AuthFlowError()


class FacebookAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The Facebook authentication provider type allows users to
    login using OAuth2 through Facebook.
    """

    type = "facebook"
    model_class = FacebookAuthProviderModel
    allowed_fields = ["id", "enabled", "name", "client_id", "secret"]
    serializer_field_names = ["enabled", "name", "client_id", "secret"]

    AUTHORIZATION_URL = "https://www.facebook.com/dialog/oauth"
    SCOPE = ["email"]

    ACCESS_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"  # nosec B105
    USER_INFO_URL = "https://graph.facebook.com/me?fields=id,email,name"  # nosec B105

    def get_authorization_url(self, instance: FacebookAuthProviderModel) -> str:
        oauth = self.get_oauth_session(instance)
        oauth = facebook_compliance_fix(oauth)
        authorization_url, state = oauth.authorization_url(self.AUTHORIZATION_URL)
        return authorization_url

    def get_user_info(self, instance: FacebookAuthProviderModel, code: str) -> UserInfo:
        """
        Queries the provider to obtain user info data (name and email).

        :param instance: Provider model that will be used to retrieve the user
            info.
        :param code: The security code that was passed from the provider to
            the callback endpoint.
        :raises AuthFlowError if the provider is unavailable, misconfigured or
            the provided code is not valid.
        :return: User info with user's name and email.
        """

        try:
            oauth = self.get_oauth_session(instance)
            oauth = facebook_compliance_fix(oauth)
            oauth.fetch_token(
                self.ACCESS_TOKEN_URL,
                code=code,
                client_secret=instance.secret,
            )
            response = oauth.get(self.USER_INFO_URL)
            name = response.json().get("name", None)
            email = response.json().get("email", None)
            return UserInfo(name=name, email=email)
        except Exception as exc:
            logger.exception(exc)
            raise AuthFlowError()


class OpenIdConnectAuthProviderType(OAuth2AuthProviderMixin, AuthProviderType):
    """
    The OpenId authentication provider type allows users to
    login using OAuth2 through OpenId Connect compatible provider.
    """

    type = "openid_connect"
    model_class = OpenIdConnectAuthProviderModel
    allowed_fields = [
        "id",
        "enabled",
        "name",
        "base_url",
        "client_id",
        "secret",
        "authorization_url",
        "access_token_url",
        "user_info_url",
    ]
    serializer_field_names = ["enabled", "name", "base_url", "client_id", "secret"]
    api_exceptions_map: ExceptionMappingType = {
        InvalidProviderUrl: ERROR_INVALID_PROVIDER_URL
    }

    SCOPE = ["openid", "email", "profile"]

    def create(self, **values):
        urls = self.get_wellknown_urls(values["base_url"])
        return super().create(**values, **asdict(urls))

    def update(self, provider, **values):
        if values.get("base_url"):
            urls = self.get_wellknown_urls(values["base_url"])
            return super().update(provider, **values, **asdict(urls))
        return super().update(provider, **values)

    def get_base_url(self, instance: AuthProviderModel) -> str:
        return instance.authorization_url

    def get_user_info(
        self, instance: OpenIdConnectAuthProviderModel, code: str
    ) -> UserInfo:
        """
        Queries the provider to obtain user info data (name and email).

        :param instance: Provider model that will be used to retrieve the user
            info.
        :param code: The security code that was passed from the provider to
            the callback endpoint.
        :raises AuthFlowError if the provider is unavailable, misconfigured or
            the provided code is not valid.
        :return: User info with user's name and email.
        """

        try:
            oauth = self.get_oauth_session(instance)
            oauth.fetch_token(
                instance.access_token_url,
                code=code,
                client_secret=instance.secret,
            )
            response = oauth.get(instance.user_info_url)
            name = response.json().get("name", None)
            email = response.json().get("email", None)
            return UserInfo(name=name, email=email)
        except Exception as exc:
            logger.exception(exc)
            raise AuthFlowError()

    def get_wellknown_urls(self, base_url: str) -> WellKnownUrls:
        """
        Queries the provider "wellknown URL endpoint" to retrieve OpenId Connect
        wellknown URLS like authorization url, access token url or user info url.

        :param base_url: The provider base URL (domain URL).
        :return: The collection of well-known OpenId Connect URL needed to
            work with the provider.
        """

        try:
            wellknown_url = f"{base_url}/.well-known/openid-configuration"
            response = requests.get(wellknown_url)
            return WellKnownUrls(
                authorization_url=response.json()["authorization_endpoint"],
                access_token_url=response.json()["token_endpoint"],
                user_info_url=response.json()["userinfo_endpoint"],
            )
        except Exception as exc:
            logger.exception(exc)
            raise InvalidProviderUrl()
