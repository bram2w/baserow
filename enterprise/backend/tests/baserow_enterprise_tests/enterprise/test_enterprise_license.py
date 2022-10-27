from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

import pytest
from baserow_enterprise.features import RBAC, SSO
from baserow_premium.api.user.user_data_types import ActiveLicensesDataType
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from freezegun import freeze_time

from baserow.api.user.registries import user_data_registry
from baserow.core.models import Settings

VALID_ONE_SEAT_ENTERPRISE_LICENSE = (
    # id: "1", instance_id: "1"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjUzODczYmVkLWJlNTQtNDEwZS04N2EzLTE2OTM2ODY2YjBiNiIsICJ2YWxpZF9mcm9tIjogIjIwMjItMTAtMDFUMDA6MDA6MDAiLCAidmFsaWRfdGhyb3VnaCI6ICIyMDY5LTA4LTA5VDIzOjU5OjU5IiwgInByb2R1Y3RfY29kZSI6ICJlbnRlcnByaXNlIiwgInNlYXRzIjogMSwgImlzc3VlZF9vbiI6ICIyMDIyLTEwLTI2VDE0OjQ4OjU0LjI1OTQyMyIsICJpc3N1ZWRfdG9fZW1haWwiOiAidGVzdEB0ZXN0LmNvbSIsICJpc3N1ZWRfdG9fbmFtZSI6ICJ0ZXN0QHRlc3QuY29tIiwgImluc3RhbmNlX2lkIjogIjEifQ==.B7aPXR0R4Fxr28AL7B5oopa2Yiz_MmEBZGdzSEHHLt4wECpnzjd_SF440KNLEZYA6WL1rhNkZ5znbjYIp6KdCqLdcm1XqNYOIKQvNTOtl9tUAYj_Qvhq1jhqSja-n3HFBjIh9Ve7a6T1PuaPLF1DoxSRGFZFXliMeJRBSzfTsiHiO22xRQ4GwafscYfUIWvIJJHGHtYEd9rk0tG6mfGEaQGB4e6KOsN-zw-bgLDBOKmKTGrVOkZnaGHBVVhUdpBn25r3CFWqHIApzUCo81zAA96fECHPlx_fBHhvIJXLsN5i3LdeJlwysg5SBO15Vt-tsdPmdcsec-fOzik-k3ib0A== "
)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_features_will_be_active_instance_wide_when_enterprise_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    assert LicenseHandler.instance_has_feature(RBAC)
    assert LicenseHandler.instance_has_feature(SSO)
    assert LicenseHandler.instance_has_feature(PREMIUM)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_users_not_assigned_a_seat_still_get_enterprise_features(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    assert LicenseHandler.user_has_feature_instance_wide(PREMIUM, user)
    assert LicenseHandler.user_has_feature_instance_wide(SSO, user)
    assert LicenseHandler.user_has_feature_instance_wide(RBAC, user)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_users_assigned_a_seat_still_get_enterprise_features(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_object = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )
    LicenseHandler.add_user_to_license(user, license_object, user)

    assert LicenseHandler.user_has_feature_instance_wide(PREMIUM, user)
    assert LicenseHandler.user_has_feature_instance_wide(SSO, user)
    assert LicenseHandler.user_has_feature_instance_wide(RBAC, user)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_features_will_not_be_active_instance_wide_when_enterprise_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert not LicenseHandler.instance_has_feature(RBAC)
        assert not LicenseHandler.instance_has_feature(SSO)
        assert not LicenseHandler.instance_has_feature(PREMIUM)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_users_not_assigned_a_seat_dont_get_features_if_license_not_active(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert not LicenseHandler.user_has_feature_instance_wide(PREMIUM, user)
        assert not LicenseHandler.user_has_feature_instance_wide(SSO, user)
        assert not LicenseHandler.user_has_feature_instance_wide(RBAC, user)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_users_assigned_a_seat_still_dont_get_features_if_license_inactive(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_object = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )
    LicenseHandler.add_user_to_license(user, license_object, user)

    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert not LicenseHandler.user_has_feature_instance_wide(PREMIUM, user)
        assert not LicenseHandler.user_has_feature_instance_wide(SSO, user)
        assert not LicenseHandler.user_has_feature_instance_wide(RBAC, user)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_anonymous_user_data_has_no_enterprise_license_when_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(AnonymousUser(), None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_anonymous_user_data_enables_enterprise_features_instance_wide(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    assert al.get_user_data(AnonymousUser(), None) == {
        "instance_wide": {"enterprise": True},
        "per_group": {},
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_random_user_user_data_has_no_enterprise_license_when_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    random_user = data_fixture.create_user()
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(random_user, None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_random_user_data_enables_enterprise_features_instance_wide(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    random_user = data_fixture.create_user()
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    assert al.get_user_data(random_user, None) == {
        "instance_wide": {"enterprise": True},
        "per_group": {},
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_license_user_user_data_has_no_enterprise_license_when_not_active(
    data_fixture,
):

    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_obj = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )
    LicenseHandler.add_user_to_license(user, license_obj, user)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(user, None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_assigned_user_data_enables_enterprise_features_instance_wide(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_obj = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )
    LicenseHandler.add_user_to_license(user, license_obj, user)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    assert al.get_user_data(user, None) == {
        "instance_wide": {"enterprise": True},
        "per_group": {},
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_assigned_user_data_no_enterprise_features_instance_wide_not_active(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_obj = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )
    LicenseHandler.add_user_to_license(user, license_obj, user)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(user, None) == {
            "instance_wide": {},
            "per_group": {},
        }
