import os
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from freezegun import freeze_time
from itsdangerous.exc import SignatureExpired, BadSignature

from django.contrib.auth import get_user_model
from django.conf import settings

from baserow.contrib.database.models import (
    Database,
    Table,
    GridView,
    TextField,
    LongTextField,
    BooleanField,
    DateField,
)
from baserow.contrib.database.views.models import GridViewFieldOptions
from baserow.core.exceptions import (
    BaseURLHostnameNotAllowed,
    GroupInvitationEmailMismatch,
    GroupInvitationDoesNotExist,
)
from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser
from baserow.core.registries import plugin_registry
from baserow.core.user.exceptions import (
    UserAlreadyExist,
    UserNotFound,
    PasswordDoesNotMatchValidation,
    InvalidPassword,
    DisabledSignupError,
)
from baserow.core.user.handler import UserHandler

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
def test_get_user(data_fixture):
    user_1 = data_fixture.create_user(email="user1@localhost")

    handler = UserHandler()

    with pytest.raises(ValueError):
        handler.get_user()

    with pytest.raises(UserNotFound):
        handler.get_user(user_id=-1)

    with pytest.raises(UserNotFound):
        handler.get_user(email="user3@localhost")

    assert handler.get_user(user_id=user_1.id).id == user_1.id
    assert handler.get_user(email=user_1.email).id == user_1.id


@pytest.mark.django_db
def test_create_user(data_fixture):
    plugin_mock = MagicMock()
    plugin_registry.registry["mock"] = plugin_mock

    user_handler = UserHandler()
    valid_password = "thisIsAValidPassword"

    data_fixture.update_settings(allow_new_signups=False)
    with pytest.raises(DisabledSignupError):
        user_handler.create_user("Test1", "test@test.nl", valid_password)
    assert User.objects.all().count() == 0
    data_fixture.update_settings(allow_new_signups=True)

    user = user_handler.create_user("Test1", "test@test.nl", valid_password)
    assert user.pk
    assert user.first_name == "Test1"
    assert user.email == "test@test.nl"
    assert user.username == "test@test.nl"

    assert Group.objects.all().count() == 1
    group = Group.objects.all().first()
    assert group.users.filter(id=user.id).count() == 1
    assert group.name == "Test1's group"

    assert Database.objects.all().count() == 1
    assert Table.objects.all().count() == 2
    assert GridView.objects.all().count() == 2
    assert TextField.objects.all().count() == 3
    assert LongTextField.objects.all().count() == 1
    assert BooleanField.objects.all().count() == 2
    assert DateField.objects.all().count() == 1
    assert GridViewFieldOptions.objects.all().count() == 3

    tables = Table.objects.all().order_by("id")

    model_1 = tables[0].get_model()
    model_1_results = model_1.objects.all()
    assert len(model_1_results) == 4
    assert model_1_results[0].order == Decimal("1.00000000000000000000")
    assert model_1_results[1].order == Decimal("2.00000000000000000000")
    assert model_1_results[2].order == Decimal("3.00000000000000000000")
    assert model_1_results[3].order == Decimal("4.00000000000000000000")

    model_2 = tables[1].get_model()
    model_2_results = model_2.objects.all()
    assert len(model_2_results) == 3
    assert model_2_results[0].order == Decimal("1.00000000000000000000")
    assert model_2_results[1].order == Decimal("2.00000000000000000000")
    assert model_2_results[2].order == Decimal("3.00000000000000000000")

    plugin_mock.user_created.assert_called_with(user, group, None, None)

    with pytest.raises(UserAlreadyExist):
        user_handler.create_user("Test1", "test@test.nl", valid_password)


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_password", invalid_passwords)
def test_create_user_invalid_password(data_fixture, invalid_password):
    user_handler = UserHandler()

    with pytest.raises(PasswordDoesNotMatchValidation):
        user_handler.create_user("Test1", "test@test.nl", invalid_password)


@pytest.mark.django_db
def test_first_ever_created_user_is_staff(data_fixture):
    user_handler = UserHandler()
    valid_password = "thisIsAValidPassword"

    data_fixture.update_settings(allow_new_signups=True)

    first_user = user_handler.create_user(
        "First Ever User", "test@test.nl", valid_password
    )
    assert first_user.first_name == "First Ever User"
    assert first_user.is_staff

    second_user = user_handler.create_user(
        "Second User", "test2@test.nl", valid_password
    )
    assert second_user.first_name == "Second User"
    assert not second_user.is_staff


@pytest.mark.django_db
def test_create_user_with_invitation(data_fixture):
    plugin_mock = MagicMock()
    plugin_registry.registry["mock"] = plugin_mock
    valid_password = "thisIsAValidPassword"

    user_handler = UserHandler()
    core_handler = CoreHandler()

    invitation = data_fixture.create_group_invitation(email="test0@test.nl")
    signer = core_handler.get_group_invitation_signer()

    with pytest.raises(BadSignature):
        user_handler.create_user("Test1", "test0@test.nl", valid_password, "INVALID")

    with pytest.raises(GroupInvitationDoesNotExist):
        user_handler.create_user(
            "Test1", "test0@test.nl", valid_password, signer.dumps(99999)
        )

    with pytest.raises(GroupInvitationEmailMismatch):
        user_handler.create_user(
            "Test1", "test1@test.nl", valid_password, signer.dumps(invitation.id)
        )

    user = user_handler.create_user(
        "Test1", "test0@test.nl", valid_password, signer.dumps(invitation.id)
    )

    assert Group.objects.all().count() == 1
    assert Group.objects.all().first().id == invitation.group_id
    assert GroupUser.objects.all().count() == 2

    plugin_mock.user_created.assert_called_once()
    args = plugin_mock.user_created.call_args
    assert args[0][0] == user
    assert args[0][1].id == invitation.group_id
    assert args[0][2].email == invitation.email
    assert args[0][2].group_id == invitation.group_id

    # We do not expect any initial data to have been created.
    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0


@pytest.mark.django_db
def test_create_user_with_template(data_fixture):
    old_templates = settings.APPLICATION_TEMPLATES_DIR
    settings.APPLICATION_TEMPLATES_DIR = os.path.join(
        settings.BASE_DIR, "../../../tests/templates"
    )
    template = data_fixture.create_template(slug="example-template")
    user_handler = UserHandler()
    valid_password = "thisIsAValidPassword"
    user_handler.create_user(
        "Test1", "test0@test.nl", valid_password, template=template
    )

    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 1
    # We expect the example template to be installed
    assert Database.objects.all().count() == 1
    assert Database.objects.all().first().name == "Event marketing"
    assert Table.objects.all().count() == 2

    settings.APPLICATION_TEMPLATES_DIR = old_templates


@pytest.mark.django_db(transaction=True)
def test_send_reset_password_email(data_fixture, mailoutbox):
    user = data_fixture.create_user(email="test@localhost")
    handler = UserHandler()

    with pytest.raises(BaseURLHostnameNotAllowed):
        handler.send_reset_password_email(user, "http://test.nl/reset-password")

    signer = handler.get_reset_password_signer()
    handler.send_reset_password_email(user, "http://localhost:3000/reset-password")

    assert len(mailoutbox) == 1
    email = mailoutbox[0]

    assert email.subject == "Reset password - Baserow"
    assert email.from_email == "no-reply@localhost"
    assert "test@localhost" in email.to

    html_body = email.alternatives[0][0]
    search_url = "http://localhost:3000/reset-password/"
    start_url_index = html_body.index(search_url)

    assert start_url_index != -1

    end_url_index = html_body.index('"', start_url_index)
    token = html_body[start_url_index + len(search_url) : end_url_index]

    user_id = signer.loads(token)
    assert user_id == user.id


@pytest.mark.django_db
def test_reset_password(data_fixture):
    user = data_fixture.create_user(email="test@localhost")
    handler = UserHandler()
    valid_password = "thisIsAValidPassword"

    signer = handler.get_reset_password_signer()

    with pytest.raises(BadSignature):
        handler.reset_password("test", valid_password)
        assert not user.check_password(valid_password)

    with freeze_time("2020-01-01 12:00"):
        token = signer.dumps(9999)

    with freeze_time("2020-01-02 12:00"):
        with pytest.raises(UserNotFound):
            handler.reset_password(token, valid_password)
            assert not user.check_password(valid_password)

    with freeze_time("2020-01-01 12:00"):
        token = signer.dumps(user.id)

    with freeze_time("2020-01-04 12:00"):
        with pytest.raises(SignatureExpired):
            handler.reset_password(token, valid_password)
            assert not user.check_password(valid_password)

    with freeze_time("2020-01-02 12:00"):
        user = handler.reset_password(token, valid_password)
        assert user.check_password(valid_password)


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_password", invalid_passwords)
def test_reset_password_invalid_new_password(data_fixture, invalid_password):
    user = data_fixture.create_user(email="test@localhost")
    handler = UserHandler()

    signer = handler.get_reset_password_signer()
    token = signer.dumps(user.id)

    with pytest.raises(PasswordDoesNotMatchValidation):
        handler.reset_password(token, invalid_password)


@pytest.mark.django_db
def test_change_password(data_fixture):
    valid_password = "aValidPassword"
    valid_new_password = "aValidNewPassword"
    user = data_fixture.create_user(email="test@localhost", password=valid_password)
    handler = UserHandler()

    with pytest.raises(InvalidPassword):
        handler.change_password(user, "INCORRECT", valid_new_password)

    user.refresh_from_db()
    assert user.check_password(valid_password)

    user = handler.change_password(user, valid_password, valid_new_password)
    assert user.check_password(valid_new_password)


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_password", invalid_passwords)
def test_change_password_invalid_new_password(data_fixture, invalid_password):
    validOldPW = "thisPasswordIsValid"
    user = data_fixture.create_user(email="test@localhost", password=validOldPW)
    handler = UserHandler()

    with pytest.raises(PasswordDoesNotMatchValidation):
        handler.change_password(user, validOldPW, invalid_password)

    user.refresh_from_db()
    assert user.check_password(validOldPW)
