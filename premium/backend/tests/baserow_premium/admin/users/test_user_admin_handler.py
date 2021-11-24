import pytest
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from baserow.core.exceptions import IsNotAdminError
from baserow.core.user.exceptions import PasswordDoesNotMatchValidation
from baserow_premium.admin.users.exceptions import (
    CannotDeactivateYourselfException,
    CannotDeleteYourselfException,
    UserDoesNotExistException,
)
from baserow_premium.admin.users.handler import (
    UserAdminHandler,
)
from baserow_premium.license.exceptions import NoPremiumLicenseError

User = get_user_model()
invalid_passwords = [
    "",
    "a",
    "ab",
    "ask",
    "oiue",
    "dsj43",
    "984kds",
    "dsfkjh4",
    (
        "Bgvmt95en6HGJZ9Xz0F8xysQ6eYgo2Y54YzRPxxv10b5n16F4rZ6YH4ulonocwiFK6970KiAxoYhU"
        "LYA3JFDPIQGj5gMZZl25M46sO810Zd3nyBg699a2TDMJdHG7hAAi0YeDnuHuabyBawnb4962OQ1OO"
        "f1MxzFyNWG7NR2X6MZQL5G1V61x56lQTXbvK1AG1IPM87bQ3YAtIBtGT2vK3Wd83q3he5ezMtUfzK"
        "2ibj0WWhf86DyQB4EHRUJjYcBiI78iEJv5hcu33X2I345YosO66cTBWK45SqJEDudrCOq"
    ),
]


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_delete_user(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    user_to_delete = premium_data_fixture.create_user(
        email="delete_me@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    handler.delete_user(admin_user, user_to_delete.id)
    assert not User.objects.filter(id=user_to_delete.id).exists()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_non_admin_cant_delete_user(premium_data_fixture):
    handler = UserAdminHandler()
    non_admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
        has_active_premium_license=True,
    )
    with pytest.raises(IsNotAdminError):
        handler.delete_user(non_admin_user, non_admin_user.id)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_delete_user_without_premium_license(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
    )
    with pytest.raises(NoPremiumLicenseError):
        handler.delete_user(admin_user, admin_user.id)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_modify_allowed_user_attributes(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    user_to_modify = premium_data_fixture.create_user(
        email="delete_me@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
        is_active=False,
        has_active_premium_license=True,
    )
    old_password = user_to_modify.password
    handler.update_user(
        admin_user,
        user_to_modify.id,
        **{
            "username": "new_email@example.com",
            "name": "new full name",
            "is_active": True,
            "is_staff": True,
            "password": "new_password",
        },
    )
    user_to_modify.refresh_from_db()
    assert user_to_modify.username == "new_email@example.com"
    assert user_to_modify.email == "new_email@example.com"
    assert user_to_modify.first_name == "new full name"
    assert user_to_modify.is_staff
    assert user_to_modify.is_active
    assert old_password != user_to_modify.password


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_deactive_and_unstaff_other_users(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    staff_user = premium_data_fixture.create_user(
        email="staff@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    active_user = premium_data_fixture.create_user(
        email="active@test.nl",
        password="password",
        first_name="Test1",
        is_active=True,
        has_active_premium_license=True,
    )

    handler.update_user(
        admin_user,
        staff_user.id,
        is_staff=False,
    )
    staff_user.refresh_from_db()
    assert not staff_user.is_staff

    handler.update_user(
        admin_user,
        active_user.id,
        is_active=False,
    )
    active_user.refresh_from_db()
    assert not active_user.is_active


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_updating_a_users_password_uses_djangos_built_in_smart_set_password(
    premium_data_fixture, mocker
):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    user_to_modify = premium_data_fixture.create_user(
        email="delete_me@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
        is_active=False,
        has_active_premium_license=True,
    )
    old_password_hash = user_to_modify.password
    set_password_spy = mocker.spy(User, "set_password")
    updated_user = handler.update_user(
        admin_user,
        user_to_modify.id,
        password="new_password",
    )
    assert updated_user.password != "new_password"
    assert updated_user.password != old_password_hash
    assert set_password_spy.call_count == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
@pytest.mark.parametrize("invalid_password", invalid_passwords)
def test_updating_a_users_password_with_invalid_password_raises_error(
    premium_data_fixture, invalid_password
):
    handler = UserAdminHandler()
    valid_password = "thisIsAValidPassword"

    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password=valid_password,
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    user_to_modify = premium_data_fixture.create_user(
        email="delete_me@test.nl",
        password=valid_password,
        first_name="Test1",
        is_staff=False,
        is_active=False,
        has_active_premium_license=True,
    )

    with pytest.raises(PasswordDoesNotMatchValidation):
        handler.update_user(
            admin_user,
            user_to_modify.id,
            password=invalid_password,
        )
    user_to_modify.refresh_from_db()
    assert user_to_modify.check_password(valid_password)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_non_admin_cant_edit_user(premium_data_fixture):
    handler = UserAdminHandler()
    non_admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
        has_active_premium_license=True,
    )
    with pytest.raises(IsNotAdminError):
        handler.update_user(non_admin_user, non_admin_user.id, "new_email@example.com")
    non_admin_user.refresh_from_db()
    assert non_admin_user.username == "test@test.nl"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_cant_deactivate_themselves(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        is_active=True,
        has_active_premium_license=True,
    )
    with pytest.raises(CannotDeactivateYourselfException):
        handler.update_user(
            admin_user,
            admin_user.id,
            is_active=False,
        )
    admin_user.refresh_from_db()
    assert admin_user.is_active


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_cant_destaff_themselves(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        is_active=True,
        has_active_premium_license=True,
    )
    with pytest.raises(CannotDeactivateYourselfException):
        handler.update_user(
            admin_user,
            admin_user.id,
            is_staff=False,
        )
    admin_user.refresh_from_db()
    assert admin_user.is_staff


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_update_user_without_premium_license(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
    )
    with pytest.raises(NoPremiumLicenseError):
        handler.update_user(admin_user, admin_user.id)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_cant_delete_themselves(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        is_active=True,
        has_active_premium_license=True,
    )
    with pytest.raises(CannotDeleteYourselfException):
        handler.delete_user(admin_user, admin_user.id)

    assert User.objects.filter(id=admin_user.id).exists()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_raises_exception_when_deleting_an_unknown_user(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        is_active=True,
        has_active_premium_license=True,
    )
    with pytest.raises(UserDoesNotExistException):
        handler.delete_user(admin_user, 99999)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_raises_exception_when_updating_an_unknown_user(premium_data_fixture):
    handler = UserAdminHandler()
    admin_user = premium_data_fixture.create_user(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        is_active=True,
        has_active_premium_license=True,
    )
    with pytest.raises(UserDoesNotExistException):
        handler.update_user(admin_user, 99999, username="new_password")
