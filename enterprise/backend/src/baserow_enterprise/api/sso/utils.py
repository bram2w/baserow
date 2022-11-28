from enum import Enum
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.http import HttpResponse
from django.shortcuts import redirect

from requests.models import PreparedRequest

from baserow.core.user.utils import generate_session_tokens_for_user


# please keep this in sync with baserow_enterprise/locales/en.json
class SsoErrorCode(Enum):
    FEATURE_NOT_ACTIVE = "errorSsoFeatureNotActive"
    INVALID_SAML_REQUEST = "errorInvalidSamlRequest"
    INVALID_SAML_RESPONSE = "errorInvalidSamlResponse"
    USER_DEACTIVATED = "errorUserDeactivated"
    PROVIDER_DOES_NOT_EXIST = "errorProviderDoesNotExist"
    AUTH_FLOW_ERROR = "errorAuthFlowError"
    DIFFERENT_PROVIDER = "errorDifferentProvider"
    GROUP_INVITATION_EMAIL_MISMATCH = "errorGroupInvitationEmailMismatch"
    SIGNUP_DISABLED = "errorSignupDisabled"


def map_sso_exceptions(mapping: Dict[Exception, SsoErrorCode]):
    """
    This decorator can be used to map exceptions to SSO error codes. If the
    decorated function raises an exception that is in the mapping, the
    redirect_to_sign_in_error_page() function will be called with the mapped
    error code. If the exception is not in the mapping, it will be raised
    normally.

    :param mapping: A dictionary that maps exceptions to SSO error codes.
    :return: The decorator.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                for exception, error_code in mapping.items():
                    if isinstance(e, exception):
                        return redirect_to_sign_in_error_page(error_code)
                raise e

        return wrapper

    return decorator


def urlencode_query_params(url: str, query_params: Dict[str, str]) -> str:
    """
    Adds the query parameters to the provided url.

    :param url: The url to which the query parameters should be added.
    :param query_params: The query parameters that should be added to the url.
    :return: The url with the query parameters added.
    """

    req = PreparedRequest()
    req.prepare_url(url, query_params)
    return req.url


def redirect_to_sign_in_error_page(
    error_code: Optional[SsoErrorCode] = None,
) -> HttpResponse:
    """
    Redirects the user to the error page in the frontend providing a message as
    query parameter if provided.

    :param error_message: The message that should be shown to the user.
    :return: The redirect response to the frontend error page with the error
        message encoded as query param.
    """

    frontend_error_page_url = get_frontend_login_error_url()
    if error_code:
        frontend_error_page_url = urlencode_query_params(
            frontend_error_page_url, {"error": error_code.value}
        )
    return redirect(frontend_error_page_url)


def get_valid_frontend_url(
    requested_original_url: Optional[str] = None,
    query_params: Optional[Dict[str, str]] = None,
) -> str:
    """
    Returns a valid absolute frontend url based on the original url requested
    before the redirection to the login (can be relative or absolute). If the
    original url is relative, it will be prefixed with the frontend hostname to
    make the IdP redirection work. If the original url is external to Baserow,
    the default frontend dashboard url will be returned instead.

    :param requested_original_url: The url to which the user should be
        redirected after a successful login.
    :return: The url with the token as a query parameter.
    """

    requested_url_parsed = urlparse(requested_original_url or "")
    default_frontend_url_parsed = urlparse(get_frontend_default_redirect_url())

    if requested_url_parsed.path in ["", "/"]:
        # use the default frontend path if the requested one is empty
        requested_url_parsed = requested_url_parsed._replace(
            path=default_frontend_url_parsed.path
        )
    if requested_url_parsed.hostname is None:
        # provide a correct absolute url if the requested one is relative
        requested_url_parsed = default_frontend_url_parsed._replace(
            path=requested_url_parsed.path
        )
    elif requested_url_parsed.hostname != default_frontend_url_parsed.hostname:
        # return the default url if the requested url is external to Baserow
        requested_url_parsed = default_frontend_url_parsed

    if query_params:
        return urlencode_query_params(requested_url_parsed.geturl(), query_params)

    return str(requested_url_parsed.geturl())


def urlencode_user_token(frontend_url: str, user: AbstractUser) -> str:
    """
    Adds the token as a query parameter to the provided frontend url. Please
    ensure to call the get_url_for_frontend_page_if_valid_or_default() method
    before calling this method, so to be sure to encode the refresh token in a
    valid Baserow frontend url.

    :param frontend_url: The valid frontend url to which the user should be
        redirected after a successful login.
    :param user: The user that sign in with an external provider and is going to
        start a new session in Baserow.
    :return: The url with the token as a query parameter.
    """

    user_tokens = generate_session_tokens_for_user(user, include_refresh_token=True)
    return urlencode_query_params(frontend_url, {"token": user_tokens["refresh_token"]})


def redirect_user_on_success(
    user: AbstractUser, requested_original_url: Optional[str] = None
) -> HttpResponse:
    """
    Ensure that the requested original url is valid or take the frontend default
    url. It adds the JWT token as query parameter to the url so that the user
    can start a new session.

    :param user: The user that sign in with an external provider and is going to
        start a new session in Baserow.
    :param requested_original_url: The url to which the user should be
        redirected after a successful login.
    :return: The redirect HTTP response to the url with the token as a query
        parameter.
    """

    valid_frontend_url = get_valid_frontend_url(requested_original_url)
    redirect_url = urlencode_user_token(valid_frontend_url, user)
    return redirect(redirect_url)


def get_frontend_default_redirect_url() -> str:
    """
    Returns the url to the frontend dashboard.

    :return: The absolute url to the Baserow dashboard.
    """

    return urljoin(settings.PUBLIC_WEB_FRONTEND_URL, "/dashboard")


def get_frontend_login_error_url() -> str:
    """
    Returns the url to the frontend login error page.

    :return: The absolute url to the Baserow login error page.
    """

    return urljoin(settings.PUBLIC_WEB_FRONTEND_URL, "/login/error")
