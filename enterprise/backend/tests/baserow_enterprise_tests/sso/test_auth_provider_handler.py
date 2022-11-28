from django.contrib.auth import get_user_model
from django.test.utils import override_settings

import pytest

from baserow.core.handler import CoreHandler
from baserow.core.user.exceptions import DeactivatedUserException
from baserow_enterprise.auth_provider.exceptions import DifferentAuthProvider
from baserow_enterprise.auth_provider.handler import AuthProviderHandler, UserInfo


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_get_or_create_user_from_sso_user_info(enterprise_data_fixture):
    auth_provider_1 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test1.com"
    )
    user_info = UserInfo("john@acme.com", "John")

    User = get_user_model()
    assert User.objects.count() == 0

    # test the user is created if not already present in the database
    (
        user,
        created,
    ) = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
        user_info, auth_provider_1
    )

    assert created is True
    assert user is not None
    assert user.email == user_info.email
    assert user.first_name == user_info.name
    assert user.password == ""
    assert User.objects.count() == 1
    assert user.groupuser_set.count() == 1
    assert user.auth_providers.filter(id=auth_provider_1.id).exists()

    # the next times the user is just retrieved
    (
        user,
        created,
    ) = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
        user_info, auth_provider_1
    )
    assert created is False
    assert user.email == user_info.email

    auth_provider_2 = enterprise_data_fixture.create_saml_auth_provider(
        domain="test2.com"
    )
    with pytest.raises(DifferentAuthProvider):
        user, _ = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
            user_info, auth_provider_2
        )

    assert User.objects.count() == 1
    assert not user.auth_providers.filter(id=auth_provider_2.id).exists()

    group_user = enterprise_data_fixture.create_user_group(user=user)
    invitation = enterprise_data_fixture.create_group_invitation(
        group=group_user.group, email="mario@acme.com", invited_by=user
    )
    core_handler = CoreHandler()
    signer = core_handler.get_group_invitation_signer()
    invitation_token = signer.dumps(invitation.id)
    user2_info = UserInfo(
        "mario@acme.com",
        "Mario",
        language="it",
        group_invitation_token=invitation_token,
    )

    (
        user2,
        created,
    ) = AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
        user2_info, auth_provider_1
    )
    assert created is True
    assert user2 is not None
    assert user2.email == user2_info.email
    assert user2.first_name == user2_info.name
    assert user2.profile.language == user2_info.language
    assert user2.password == ""
    assert User.objects.count() == 2
    assert user2.groupuser_set.count() == 1
    assert user2.groupuser_set.first().group == group_user.group
    assert user2.auth_providers.filter(id=auth_provider_1.id).exists()

    # a disabled user will raise a UserAlreadyExist exception
    user.is_active = False
    user.save()

    with pytest.raises(DeactivatedUserException):
        AuthProviderHandler.get_or_create_user_and_sign_in_via_auth_provider(
            user_info, auth_provider_2
        )
