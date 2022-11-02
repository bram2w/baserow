from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

import pytest
import responses
from baserow_premium.api.user.user_data_types import ActiveLicensesDataType
from baserow_premium.license.exceptions import CantManuallyChangeSeatsError
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from freezegun import freeze_time
from responses import json_params_matcher

from baserow.api.user.registries import user_data_registry
from baserow.core.models import Settings
from baserow_enterprise.features import RBAC, SSO
from baserow_enterprise.license_types import EnterpriseLicenseType
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment

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
def test_enterprise_users_dont_get_features_if_license_inactive(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_object = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )

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

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(user, None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enabling_enterprise_user_data_gets_enterprise_features_instance_wide(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    license_obj = LicenseHandler.register_license(
        user, VALID_ONE_SEAT_ENTERPRISE_LICENSE
    )

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    assert al.get_user_data(user, None) == {
        "instance_wide": {"enterprise": True},
        "per_group": {},
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_data_no_enterprise_features_instance_wide_not_active(
    data_fixture,
):
    Settings.objects.update_or_create(defaults={"instance_id": "1"})
    user = data_fixture.create_user(is_staff=True)
    LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)

    al = user_data_registry.get_by_type(ActiveLicensesDataType)
    # Before the license is active
    with freeze_time("2020-02-01 01:23"):
        assert al.get_user_data(user, None) == {
            "instance_wide": {},
            "per_group": {},
        }


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_check_licenses_with_enterprise_license_sends_seat_data(
    enterprise_data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://host.docker.internal:8001/api/saas/licenses/check/",
            json={
                VALID_ONE_SEAT_ENTERPRISE_LICENSE.decode(): {
                    "type": "ok",
                    "detail": "",
                },
            },
            match=[
                json_params_matcher(
                    {
                        "licenses": [VALID_ONE_SEAT_ENTERPRISE_LICENSE.decode()],
                        "instance_id": Settings.objects.get().instance_id,
                        "extra_license_info": [
                            {
                                "id": license_object.id,
                                "free_users_count": 0,
                                "seats_taken": 1,
                            }
                        ],
                    }
                )
            ],
            status=200,
        )

        LicenseHandler.check_licenses([license_object])

    responses.assert_call_count(
        "http://host.docker.internal:8001/api/saas/licenses/check/", 1
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_enterprise_license_counts_viewers_as_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    user3 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2, user3])

    table = data_fixture.create_database_table(user=user)

    admin_role = Role.objects.get(uid="ADMIN")
    viewer_role = Role.objects.get(uid="VIEWER")

    role_assignment_handler = RoleAssignmentHandler()

    assert len(RoleAssignment.objects.all()) == 0

    role_assignment_handler.assign_role(user, group, admin_role)
    role_assignment_handler.assign_role(user2, group, viewer_role)
    role_assignment_handler.assign_role(user3, group, viewer_role)

    assert EnterpriseLicenseType().get_free_users_count(license_object) == 2
    assert EnterpriseLicenseType().get_seats_taken(license_object) == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_who_is_commenter_in_one_group_and_viewer_in_another_is_not_free(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group1 = data_fixture.create_group(user=user, members=[user2])
    group2 = data_fixture.create_group(user=user, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    commenter_role = Role.objects.get(uid="COMMENTER")
    viewer_role = Role.objects.get(uid="VIEWER")

    role_assignment_handler = RoleAssignmentHandler()

    role_assignment_handler.assign_role(user, group1, admin_role)
    role_assignment_handler.assign_role(user2, group1, viewer_role)
    role_assignment_handler.assign_role(user, group2, admin_role)
    role_assignment_handler.assign_role(user2, group2, commenter_role)

    assert len(RoleAssignment.objects.all()) == 0

    assert EnterpriseLicenseType().get_free_users_count(license_object) == 0
    assert EnterpriseLicenseType().get_seats_taken(license_object) == 2


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_marked_for_deletion_is_not_counted_as_a_paid_user(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user()
    group1 = data_fixture.create_group(user=user, members=[user2])
    group2 = data_fixture.create_group(user=user, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    commenter_role = Role.objects.get(uid="COMMENTER")
    viewer_role = Role.objects.get(uid="VIEWER")

    role_assignment_handler = RoleAssignmentHandler()

    role_assignment_handler.assign_role(user, group1, admin_role)
    role_assignment_handler.assign_role(user2, group1, viewer_role)
    role_assignment_handler.assign_role(user, group2, admin_role)
    role_assignment_handler.assign_role(user2, group2, commenter_role)

    assert len(RoleAssignment.objects.all()) == 0

    user2.profile.to_be_deleted = True
    user2.profile.save()

    assert EnterpriseLicenseType().get_free_users_count(license_object) == 0
    assert EnterpriseLicenseType().get_seats_taken(license_object) == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_user_deactivated_user_is_not_counted_as_a_paid_user(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user()
    user2 = data_fixture.create_user(is_active=False)
    group1 = data_fixture.create_group(user=user, members=[user2])
    group2 = data_fixture.create_group(user=user, members=[user2])

    admin_role = Role.objects.get(uid="ADMIN")
    commenter_role = Role.objects.get(uid="COMMENTER")
    builder_role = Role.objects.get(uid="BUILDER")

    role_assignment_handler = RoleAssignmentHandler()

    role_assignment_handler.assign_role(user, group1, admin_role)
    role_assignment_handler.assign_role(user2, group1, builder_role)
    role_assignment_handler.assign_role(user, group2, admin_role)
    role_assignment_handler.assign_role(user2, group2, commenter_role)

    assert len(RoleAssignment.objects.all()) == 0
    assert EnterpriseLicenseType().get_free_users_count(license_object) == 0
    assert EnterpriseLicenseType().get_seats_taken(license_object) == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_add_seats_to_enterprise_version(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.add_user_to_license(user, license_object, user2)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_remove_seats_from_enterprise_version(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.remove_user_from_license(user, license_object, user2)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_add_all_users_to_seats_in_enterprise_version(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.fill_remaining_seats_of_license(user, license_object)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_manually_remove_all_users_from_seats_in_enterprise_version(
    enterprise_data_fixture, data_fixture, synced_roles
):
    license_object = enterprise_data_fixture.enable_enterprise()
    user = data_fixture.create_user(is_staff=True)
    user2 = data_fixture.create_user()
    data_fixture.create_group(user=user, members=[user2])
    with pytest.raises(CantManuallyChangeSeatsError):
        LicenseHandler.remove_all_users_from_license(user, license_object)
