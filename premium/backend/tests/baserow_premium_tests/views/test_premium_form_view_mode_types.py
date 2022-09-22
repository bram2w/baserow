from unittest.mock import patch

from django.test.utils import override_settings

import pytest
from baserow_premium.license.exceptions import NoPremiumLicenseError

from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import FormView


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_survey_form_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user()
    table = premium_data_fixture.create_database_table(user=user)

    handler = ViewHandler()

    with pytest.raises(NoPremiumLicenseError):
        handler.create_view(
            user=user, table=table, type_name="form", name="Form", mode="survey"
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_survey_form_with_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    table = premium_data_fixture.create_database_table(user=user)

    handler = ViewHandler()
    handler.create_view(
        user=user, table=table, type_name="form", name="Form", mode="survey"
    )

    assert FormView.objects.all().count() == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_survey_form_with_premium_license_for_group(premium_data_fixture):
    user = premium_data_fixture.create_user(
        first_name="Test User", has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)

    handler = ViewHandler()

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [
            {"type": "group", "id": table.database.group.id}
        ]
        handler.create_view(
            user=user, table=table, type_name="form", name="Form", mode="survey"
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_survey_form_without_premium_license_for_group(premium_data_fixture):
    user = premium_data_fixture.create_user(
        first_name="Test User", has_active_premium_license=True
    )
    table = premium_data_fixture.create_database_table(user=user)

    handler = ViewHandler()

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [{"type": "group", "id": 0}]
        with pytest.raises(NoPremiumLicenseError):
            handler.create_view(
                user=user, table=table, type_name="form", name="Form", mode="survey"
            )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_update_to_survey_form_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user()
    form = premium_data_fixture.create_form_view(user=user)

    handler = ViewHandler()

    with pytest.raises(NoPremiumLicenseError):
        handler.update_view(user=user, view=form, mode="survey")


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_update_existing_survey_form_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user()
    form = premium_data_fixture.create_form_view(user=user, mode="survey")

    handler = ViewHandler()
    # This should succeed because the "survey" value is not provided.
    handler.update_view(user=user, view=form, name="test")

    form.refresh_from_db()
    assert form.name == "test"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_update_survey_form_with_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    form = premium_data_fixture.create_form_view(user=user)

    handler = ViewHandler()
    handler.update_view(user=user, view=form, mode="survey")

    view = FormView.objects.all().first()
    assert view.mode == "survey"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_update_survey_form_without_premium_license_for_group(premium_data_fixture):
    user = premium_data_fixture.create_user()
    form = premium_data_fixture.create_form_view(user=user)

    handler = ViewHandler()

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [{"type": "group", "id": 0}]
        with pytest.raises(NoPremiumLicenseError):
            handler.update_view(user=user, view=form, mode="survey")


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_update_survey_form_with_premium_license_for_group(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    form = premium_data_fixture.create_form_view(user=user)

    handler = ViewHandler()

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [
            {"type": "group", "id": form.table.database.group.id}
        ]
        handler.update_view(user=user, view=form, mode="survey")

    view = FormView.objects.all().first()
    assert view.mode == "survey"
