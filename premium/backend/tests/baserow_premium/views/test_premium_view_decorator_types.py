import pytest
from unittest.mock import patch

from django.test.utils import override_settings

from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import ViewDecoration

from baserow_premium.license.exceptions import NoPremiumLicenseError


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_left_border_color_with_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()
    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="left_border_color",
        value_provider_type_name="",
        value_provider_conf={},
        user=user,
    )

    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_left_border_color_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=False)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with pytest.raises(NoPremiumLicenseError):
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="left_border_color",
            value_provider_type_name="",
            value_provider_conf={},
            user=user,
        )

    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="left_border_color",
        value_provider_type_name="",
        value_provider_conf={},
    )
    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_left_border_color_without_premium_license_for_group(
    premium_data_fixture,
):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [
            {"type": "group", "id": grid_view.table.database.group.id}
        ]
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="left_border_color",
            value_provider_type_name="",
            value_provider_conf={},
            user=user,
        )

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [{"type": "group", "id": 0}]
        with pytest.raises(NoPremiumLicenseError):
            handler.create_decoration(
                view=grid_view,
                decorator_type_name="left_border_color",
                value_provider_type_name="",
                value_provider_conf={},
                user=user,
            )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_background_color_with_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()
    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="background_color",
        value_provider_type_name="",
        value_provider_conf={},
        user=user,
    )

    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_background_color_without_premium_license(premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=False)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with pytest.raises(NoPremiumLicenseError):
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="background_color",
            value_provider_type_name="",
            value_provider_conf={},
            user=user,
        )

    decoration = handler.create_decoration(
        view=grid_view,
        decorator_type_name="background_color",
        value_provider_type_name="",
        value_provider_conf={},
    )
    assert isinstance(decoration, ViewDecoration)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_background_color_without_premium_license_for_group(
    premium_data_fixture,
):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    grid_view = premium_data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [
            {"type": "group", "id": grid_view.table.database.group.id}
        ]
        handler.create_decoration(
            view=grid_view,
            decorator_type_name="background_color",
            value_provider_type_name="",
            value_provider_conf={},
            user=user,
        )

    with patch(
        "baserow_premium.license.handler.has_active_premium_license_for"
    ) as mock_has_active_premium_license_for:
        mock_has_active_premium_license_for.return_value = [{"type": "group", "id": 0}]
        with pytest.raises(NoPremiumLicenseError):
            handler.create_decoration(
                view=grid_view,
                decorator_type_name="background_color",
                value_provider_type_name="",
                value_provider_conf={},
                user=user,
            )
