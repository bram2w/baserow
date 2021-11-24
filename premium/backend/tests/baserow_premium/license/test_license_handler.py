import pytest
import responses
import base64
from freezegun import freeze_time
from unittest.mock import patch

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from django.db import transaction
from django.test.utils import override_settings

from baserow.core.exceptions import IsNotAdminError

from baserow_premium.license.handler import (
    has_active_premium_license,
    check_active_premium_license,
    get_public_key,
    decode_license,
    fetch_license_status_with_authority,
    check_licenses,
    register_license,
    remove_license,
    add_user_to_license,
    remove_user_from_license,
    fill_remaining_seats_of_license,
    remove_all_users_from_license,
)
from baserow_premium.license.models import License, LicenseUser
from baserow_premium.license.exceptions import (
    NoPremiumLicenseError,
    InvalidPremiumLicenseError,
    UnsupportedPremiumLicenseError,
    PremiumLicenseInstanceIdMismatchError,
    PremiumLicenseHasExpired,
    PremiumLicenseAlreadyExists,
    NoSeatsLeftInPremiumLicenseError,
    UserAlreadyOnPremiumLicenseError,
    LicenseAuthorityUnavailable,
)


VALID_ONE_SEAT_LICENSE = (
    # id: "1", instance_id: "1"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjEiLCAidmFsaWRfZnJvbSI6ICIyMDIxLTA4LTI5VDE5OjUyOjU3"
    b"Ljg0MjY5NiIsICJ2YWxpZF90aHJvdWdoIjogIjIwMjEtMDktMjlUMTk6NTI6NTcuODQyNjk2IiwgInBy"
    b"b2R1Y3RfY29kZSI6ICJwcmVtaXVtIiwgInNlYXRzIjogMSwgImlzc3VlZF9vbiI6ICIyMDIxLTA4LTI5"
    b"VDE5OjUyOjU3Ljg0MjY5NiIsICJpc3N1ZWRfdG9fZW1haWwiOiAiYnJhbUBiYXNlcm93LmlvIiwgImlz"
    b"c3VlZF90b19uYW1lIjogIkJyYW0iLCAiaW5zdGFuY2VfaWQiOiAiMSJ9.e33Z4CxLSmD-R55Es24P3mR"
    b"8Oqn3LpaXvgYLzF63oFHat3paon7IBjBmOX3eyd8KjirVf3empJds4uUw2Nn2m7TVvRAtJ8XzNl-8ytf"
    b"2RLtmjMx1Xkgp5VZ8S7UqJ_cKLyl76eVRtGEA1DH2HdPKu1vBPJ4bzDfnhDPYl4k5z9XSSgqAbQ9WO0U"
    b"5kiI3BYjVRZSKnZMeguAGZ47ezDj_WArGcHAB8Pa2v3HFp5Y34DMJ8r3_hD5hxCKgoNx4AHx1Q-hRDqp"
    b"Aroj-4jl7KWvlP-OJNc1BgH2wnhFmeKHotv-Iumi83JQohyceUbG6j8rDDQvJfcn0W2_ebmUH3TKr-w="
    b"="
)
VALID_UPGRADED_TEN_SEAT_LICENSE = (
    # id: "1", instance_id: "1"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjEiLCAidmFsaWRfZnJvbSI6ICIyMDIxLTA4LTI5VDE5OjUyOjU3"
    b"Ljg0MjY5NiIsICJ2YWxpZF90aHJvdWdoIjogIjIwMjEtMDktMjlUMTk6NTI6NTcuODQyNjk2IiwgInBy"
    b"b2R1Y3RfY29kZSI6ICJwcmVtaXVtIiwgInNlYXRzIjogMTAsICJpc3N1ZWRfb24iOiAiMjAyMS0wOC0z"
    b"MFQxOTo1Mjo1Ny44NDI2OTYiLCAiaXNzdWVkX3RvX2VtYWlsIjogImJyYW1AYmFzZXJvdy5pbyIsICJp"
    b"c3N1ZWRfdG9fbmFtZSI6ICJCcmFtIiwgImluc3RhbmNlX2lkIjogIjEifQ==.MLZn4TG1iZbXo1kjryk"
    b"B98fFnYf8tOu8DG_I9CpkS5UGboI1-BNcq0pdtKxRgaTkRb-Q09D4J-LHKri5KA9WyQQNY8bb4antS1s"
    b"svi8Yrp6p9VQhtCunKCqUuLA8mpHFNLV6nbsTKLds5imyFSMzT-8RLejT774RUQ3-DUYd2N-awbxBwDs"
    b"Zpsupq3_7UrYIPhDcpVs_5G47p8ZT-z2fcC2cPOB2tRc6eQw7eUx95-nIxcR9IbLsHmQjYj3dxOjdsmN"
    b"SDekPuwzbQiZnDpfy7kzc93-752AHTZ-O2gd83PFZziaIJSyu7mUsxWk4rkMQalO_XG9X0AOEraT0SQQ"
    b"r0A=="
)
VALID_TWO_SEAT_LICENSE = (
    # id: "2", instance_id: "1"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjIiLCAidmFsaWRfZnJvbSI6ICIyMDIxLTA4LTI5VDE5OjUzOjM3"
    b"LjA5MjMwMyIsICJ2YWxpZF90aHJvdWdoIjogIjIwMjEtMDktMjlUMTk6NTM6MzcuMDkyMzAzIiwgInBy"
    b"b2R1Y3RfY29kZSI6ICJwcmVtaXVtIiwgInNlYXRzIjogMiwgImlzc3VlZF9vbiI6ICIyMDIxLTA4LTI5"
    b"VDE5OjUzOjM3LjA5MjMwMyIsICJpc3N1ZWRfdG9fZW1haWwiOiAiYnJhbUBiYXNlcm93LmlvIiwgImlz"
    b"c3VlZF90b19uYW1lIjogIkJyYW0iLCAiaW5zdGFuY2VfaWQiOiAiMSJ9.d41tB1kx69gw-9xDrRI0kER"
    b"KDUtR-P6yRM3ufKZ_XRDewVCBAniCLe9-ce7TKabnMedE2cqHjYVLlI66Dfa5oH8fGswnyC16c9ZHlOU"
    b"jQ5CpHTorZm6eyCXaP6MDdhstCNKdDrZns3qvVMAqDpmxS8wmiG9Y6gZjvBGXZWeoCraF1SVcUnFBBlf"
    b"UemfGSQUwPitVlxJ6GWN-hzi7b1GZqWJKDb2YYJ0T30VMJeNO7oi6YHMUOH33041FU79DSET2A2NNEFu"
    b"e-jnCcw5NFpH-zGzBDv1wpR3DFmJa78KwGbj0Kdzim85AUzi1xGRlIyxxTdTkVy2B-08lPaoG8Q62bw="
    b"="
)
VALID_INSTANCE_TWO_LICENSE = (
    # id: "2", instance_id: "2"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjEiLCAidmFsaWRfZnJvbSI6ICIyMDIxLTA4LTI5VDE5OjUyOjU3"
    b"Ljg0MjY5NiIsICJ2YWxpZF90aHJvdWdoIjogIjIwMjEtMDktMjlUMTk6NTI6NTcuODQyNjk2IiwgInBy"
    b"b2R1Y3RfY29kZSI6ICJwcmVtaXVtIiwgInNlYXRzIjogMSwgImlzc3VlZF9vbiI6ICIyMDIxLTA4LTI5"
    b"VDE5OjUyOjU3Ljg0MjY5NiIsICJpc3N1ZWRfdG9fZW1haWwiOiAiYnJhbUBiYXNlcm93LmlvIiwgImlz"
    b"c3VlZF90b19uYW1lIjogIkJyYW0iLCAiaW5zdGFuY2VfaWQiOiAiMiJ9.i3Og4ZJwz__TxWyFc2B6lDi"
    b"ZBAIOVTZv_jXVzQQqcjG-flPAicqXFECl7MbbexVmtsMES-U7VPebOh0t4oPoDXL1LiftfjmT63wO4An"
    b"A3FMS0Ip0GIx2upkQC-MlU1kSR9Tltrr1qySuQvXORDRUaSxaRQQacwZTOIviVdcxG9vesjkFwn6LMYp"
    b"-GhmCJXB0YfMgsvPm6kj6qTWPh3ed8aLNFnekUhB-dUwA4tqPicCQHRQCRZqzo9vx-hKdeHCGZMg0htG"
    b"EB4cAeV4I29JXPC83qtwt6DSCPxudlJsli3tYsLMcxAHysVN3H_FAY8qg54MP33OKvZuwww5uFDITMQ="
    b"="
)
INVALID_SIGNATURE_LICENSE = (
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogMSwgInZhbGlkX2Zyb20iOiAiMjAyMS0wOC0yOVQxOTo1NDoxMi4w"
    b"NjY4NDYiLCAidmFsaWRfdGhyb3VnaCI6ICIyMDIxLTA5LTI5VDE5OjU0OjEyLjA2Njg0NiIsICJwcm9k"
    b"dWN0X2NvZGUiOiAicHJlbWl1bSIsICJzZWF0cyI6IDEsICJ0b19lbWFpbCI6ICJicmFtQGJhc2Vyb3cu"
    b"aW8iLCAidG9fbmFtZSI6ICJCcmFtIn0=.hYaWGO0M6s1pA9bhcBlk1fE1QMrhlDGNiBIBG_2O2AMGFPj"
    b"gnsHdwfUIe_eo6dyAyvsToxBrpxr6N1vRqPdA61cKjTlhUdFqvj7NTeydS4Z9TlfP-vFslQk9CO_ok7Z"
    b"ws8AHTQ2pKfsdzqcWNZnWKZeQGEtO73MIoFJbHr07mtWA1ZZgJNBTBpp-7BNtvj2bQyUeXyRKD5LVj8G"
    b"ESDcapZCNt5ufesbYvpfs1c6p6UP4z3gszOYrzMApMqWHty7j10SDjcLIEsUTd02r_Pbip-KxmGfecXg"
    b"B0HF7HJZwkY9ZdlZ7ODGtV0e455dQwh5sSHa3RRd71AXVou-cuOS87g=="
)
INVALID_PAYLOAD_LICENSE = (
    b"e30=.gtDuoJAHn-LTPX1ReoGo8cm3DsXq0mf9MwpIccwCQXucpnh-r6yeJzRGbx5F80OGKXZJ1XcxLRr"
    b"8-IssyxlGVcrhHt6iYXmNoPXUrxN1slOzMO4_tutvEHSuOntW5gctm9SFfcRrdbejYue_47brp779bP2"
    b"pzwejOdQbSLUeNQ4bHIKQJYZ4cCooW8yICz6a8m4NFRDu_gr0Y1ud1Eo3h2E_BL2upNg14v8BRZJCHpj"
    b"CC5Eg4ErKqm88iFStIEpub-vem9rEwKR2kIvdJ6DaD7AJTG507GEtbI9lNCkm2aPJSf142Rf8_NrTVh3"
    b"QBqZnCo-XrquQe1h4r3fvjAf5tQ=="
)
INVALID_VERSION_LICENSE = (
    b"eyJ2ZXJzaW9uIjogOTk5OX0=.rzAyL6qBkz_Eb3GYaSOXy9CJ2HJg4uAxtrbinh4aDYy7Eq4e4RpfaPm"
    b"4dZLocIRxSmx_wUYSI0CMqmkwABHgzxRVmzVAmXf5MxX7vAGjjEnQX_dQOl8kY15gXhEQZv5pjSPVcZW"
    b"CLll95OFoBUJhtOQqNC6JLA1LZdiSPG6zFhvi5V27sRGBz3E8jhFLWY-Y2WIq5_9q2d_hVFM0KHwRcxb"
    b"CVof8RBUq1DgMcDKEGE7WRHYDVP1QugBjf4GZlvIE4ZVr3tKr0aKPX8nuNVhbQeudCW8tnturmxevpRN"
    b"vLS5ETSQzJoP46cGuw0HUV20P4SnvQP_NRd5zifgllJqsUw=="
)
NOT_JSON_PAYLOAD_LICENSE = (
    b"dGVzdA==.I37aSmuKN0WSrw6IDTg2xBOlQ3UOE5cjaWfc4MF5pgIadMUjkOh0D32R7RqRhmsxhdsqK6a"
    b"bU8u8cT6ZG0PxjsRnFjrkbhdcFR1Yw9fHQ7plHShnpsj0NT8fMuDaVfCibKxyi-Z8nVmwHEIlyRkLfKV"
    b"NMTR7q2bzdM9-LZ-jJsgp4qqtSE8ct8YwwdwUS8clKzb-wVyCDeGD2kBRyxNRU_hhiwN_aDv6zEEqd6u"
    b"1lkIxotWs8hHJ3kT9EB9LY9Nb5qlm9Qt4bJY9OB4Bc8eEpXgEXGMUik11sTo5E3thoV6HJTUQWLwozbo"
    b"fXwhO9qsjxisGZPEFinezHN124jSWxQ=="
)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_has_active_premium_license(data_fixture):
    user_in_license = data_fixture.create_user()
    second_user_in_license = data_fixture.create_user()
    user_not_in_license = data_fixture.create_user()
    license = License.objects.create(license=VALID_TWO_SEAT_LICENSE.decode())
    License.objects.create(license=VALID_ONE_SEAT_LICENSE.decode())
    LicenseUser.objects.create(license=license, user=user_in_license)
    license_user_2 = LicenseUser.objects.create(
        license=license, user=second_user_in_license
    )

    with freeze_time("2021-08-01 12:00"):
        assert not has_active_premium_license(user_in_license)
        assert not has_active_premium_license(second_user_in_license)
        assert not has_active_premium_license(user_not_in_license)

    with freeze_time("2021-09-01 12:00"):
        assert has_active_premium_license(user_in_license)
        assert has_active_premium_license(second_user_in_license)
        assert not has_active_premium_license(user_not_in_license)

    with freeze_time("2021-10-01 12:00"):
        assert not has_active_premium_license(user_in_license)
        assert not has_active_premium_license(second_user_in_license)
        assert not has_active_premium_license(user_not_in_license)

    license_user_2.delete()
    with freeze_time("2021-09-01 12:00"):
        assert has_active_premium_license(user_in_license)
        assert not has_active_premium_license(second_user_in_license)
        assert not has_active_premium_license(user_not_in_license)

        check_active_premium_license(user_in_license)

        with pytest.raises(NoPremiumLicenseError):
            check_active_premium_license(second_user_in_license)

        with pytest.raises(NoPremiumLicenseError):
            check_active_premium_license(user_not_in_license)

    # When the license can't be decoded, it should also return false.
    invalid_user = data_fixture.create_user()
    invalid_license = License.objects.create(license="invalid")
    LicenseUser.objects.create(license=invalid_license, user=invalid_user)
    assert not has_active_premium_license(invalid_user)


@override_settings(DEBUG=True)
def test_get_public_key_debug():
    public_key = get_public_key()
    signature = base64.b64decode(
        b"UnRzVNbgO8XxAHEjn6uzGrjdVjwf5rU2BcOe+G2nKHhF50m8nf/DAmmk6rsCFolrCXke2tJFnER"
        b"0aeoPKwjZItnYJhkX0xt1PwkpImBoSZYQfdGycVuLwRv28yQaWP1tGonNIqpUuAiyuTrTEOWPid"
        b"vbaYtAXu/I9aRwBSpjD3cM8mvyb4BE/lsC6RC1qYj6V2vUmoWum8sCQLHcToAs75CjV8NVVH97X"
        b"TUnUellH3s+UpwHL9Rauq8rnPdAWLf6wujcqeBtdtsjp4HakuTsNYK+AcceSGeGSrlVqD0OoQei"
        b"Cc2d0/5SkO3DyndZ/X73eX2psYpyd0p1ZDkCSbKJpA=="
    )

    # We do not expect the `InvalidSignature` exception.
    assert (
        public_key.verify(
            signature,
            b"test",
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        is None
    )


@override_settings(DEBUG=False)
def test_get_public_key_production():
    public_key = get_public_key()
    signature = base64.b64decode(
        b"UnRzVNbgO8XxAHEjn6uzGrjdVjwf5rU2BcOe+G2nKHhF50m8nf/DAmmk6rsCFolrCXke2tJFnER"
        b"0aeoPKwjZItnYJhkX0xt1PwkpImBoSZYQfdGycVuLwRv28yQaWP1tGonNIqpUuAiyuTrTEOWPid"
        b"vbaYtAXu/I9aRwBSpjD3cM8mvyb4BE/lsC6RC1qYj6V2vUmoWum8sCQLHcToAs75CjV8NVVH97X"
        b"TUnUellH3s+UpwHL9Rauq8rnPdAWLf6wujcqeBtdtsjp4HakuTsNYK+AcceSGeGSrlVqD0OoQei"
        b"Cc2d0/5SkO3DyndZ/X73eX2psYpyd0p1ZDkCSbKJpA=="
    )

    # We expect the `InvalidSignature` exception because the signature has been
    # signed with the wrong private key. This way, we know the debug key is not used
    # in production.
    with pytest.raises(InvalidSignature):
        public_key.verify(
            signature,
            b"test",
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_fetch_license_status_with_authority_unavailable(data_fixture):
    data_fixture.update_settings(instance_id="1")

    with pytest.raises(LicenseAuthorityUnavailable):
        fetch_license_status_with_authority(["test"])

    responses.add(
        responses.POST,
        "http://172.17.0.1:8001/api/saas/licenses/check/",
        json={"error": "error"},
        status=400,
    )

    with pytest.raises(LicenseAuthorityUnavailable):
        fetch_license_status_with_authority(["test"])

    responses.add(
        responses.POST,
        "http://172.17.0.1:8001/api/saas/licenses/check/",
        body="not_json",
        status=200,
    )

    with pytest.raises(LicenseAuthorityUnavailable):
        fetch_license_status_with_authority(["test"])


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_fetch_license_status_with_authority_invalid_response(data_fixture):
    data_fixture.update_settings(instance_id="1")

    responses.add(
        responses.POST,
        "http://172.17.0.1:8001/api/saas/licenses/check/",
        body="not_json",
        status=200,
    )

    with pytest.raises(LicenseAuthorityUnavailable):
        fetch_license_status_with_authority(["test"])


@pytest.mark.django_db
@override_settings(DEBUG=False)
@responses.activate
def test_fetch_license_status_in_production_mode(data_fixture):
    data_fixture.update_settings(instance_id="1")

    responses.add(
        responses.POST,
        "https://api.baserow.io/api/saas/licenses/check/",
        json={"success": True},
        status=200,
    )

    response = fetch_license_status_with_authority(["test"])
    assert response["success"] is True


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_fetch_license_status_with_authority(data_fixture):
    data_fixture.update_settings(instance_id="1")

    responses.add(
        responses.POST,
        "http://172.17.0.1:8001/api/saas/licenses/check/",
        json={"test": {"type": "ok", "detail": ""}},
        status=200,
    )

    response = fetch_license_status_with_authority(["test"])
    assert len(response) == 1
    assert response["test"]["type"] == "ok"


@pytest.mark.django_db
@override_settings(DEBUG=True)
# Activate the responses because we want to check with the authority to fail.
@responses.activate
def test_check_licenses_with_authority_check(premium_data_fixture):
    invalid_license = premium_data_fixture.create_premium_license(license="invalid")
    does_not_exist_license = premium_data_fixture.create_premium_license(
        license="does_not_exist"
    )
    instance_id_mismatch_license = premium_data_fixture.create_premium_license(
        license="instance_id_mismatch"
    )
    updated_license = premium_data_fixture.create_premium_license(license="update")
    ok_license = premium_data_fixture.create_premium_license(
        license=VALID_TWO_SEAT_LICENSE.decode()
    )

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://172.17.0.1:8001/api/saas/licenses/check/",
            json={
                "invalid": {"type": "invalid", "detail": ""},
                "does_not_exist": {"type": "does_not_exist", "detail": ""},
                "instance_id_mismatch": {
                    "type": "instance_id_mismatch",
                    "detail": "",
                },
                "update": {
                    "type": "update",
                    "detail": "",
                    "new_license_payload": VALID_ONE_SEAT_LICENSE.decode(),
                },
                VALID_TWO_SEAT_LICENSE.decode(): {"type": "ok", "detail": ""},
            },
            status=200,
        )

        check_licenses(
            [
                invalid_license,
                does_not_exist_license,
                instance_id_mismatch_license,
                updated_license,
                ok_license,
            ]
        )

        all_licenses = License.objects.all().order_by("id")
        assert len(all_licenses) == 2
        assert all_licenses[0].id == updated_license.id
        assert all_licenses[0].license == VALID_ONE_SEAT_LICENSE.decode()
        assert all_licenses[0].license_id == "1"
        assert all_licenses[0].last_check.year == 2021
        assert all_licenses[1].id == ok_license.id
        assert all_licenses[1].last_check.year == 2021


@pytest.mark.django_db
@override_settings(DEBUG=True)
# Activate the responses because we want to check with the authority to fail.
@responses.activate
def test_check_licenses_without_authority_check(premium_data_fixture):
    with freeze_time("2021-07-01 12:00"):
        license_object = premium_data_fixture.create_premium_license(
            license=VALID_TWO_SEAT_LICENSE.decode()
        )
        premium_data_fixture.create_premium_license_user(license=license_object)
        premium_data_fixture.create_premium_license_user(license=license_object)
        premium_data_fixture.create_premium_license_user(license=license_object)
        premium_data_fixture.create_premium_license_user(license=license_object)

        # This license is expected to be delete because the payload is invalid.
        license_object_2 = premium_data_fixture.create_premium_license(
            license="invalid_license"
        )

        assert License.objects.all().count() == 2
        assert license_object.users.all().count() == 4
        check_licenses([license_object, license_object_2])
        assert License.objects.all().count() == 1
        assert license_object.users.all().count() == 2
        assert license_object.last_check.year == 2021


@override_settings(DEBUG=True)
def test_decode_license_with_valid_license():
    assert decode_license(VALID_ONE_SEAT_LICENSE) == {
        "version": 1,
        "id": "1",
        "valid_from": "2021-08-29T19:52:57.842696",
        "valid_through": "2021-09-29T19:52:57.842696",
        "product_code": "premium",
        "seats": 1,
        "issued_on": "2021-08-29T19:52:57.842696",
        "issued_to_email": "bram@baserow.io",
        "issued_to_name": "Bram",
        "instance_id": "1",
    }
    assert decode_license(VALID_UPGRADED_TEN_SEAT_LICENSE) == {
        "version": 1,
        "id": "1",
        "valid_from": "2021-08-29T19:52:57.842696",
        "valid_through": "2021-09-29T19:52:57.842696",
        "product_code": "premium",
        "seats": 10,
        "issued_on": "2021-08-30T19:52:57.842696",
        "issued_to_email": "bram@baserow.io",
        "issued_to_name": "Bram",
        "instance_id": "1",
    }
    assert decode_license(VALID_TWO_SEAT_LICENSE) == {
        "version": 1,
        "id": "2",
        "valid_from": "2021-08-29T19:53:37.092303",
        "valid_through": "2021-09-29T19:53:37.092303",
        "product_code": "premium",
        "seats": 2,
        "issued_on": "2021-08-29T19:53:37.092303",
        "issued_to_email": "bram@baserow.io",
        "issued_to_name": "Bram",
        "instance_id": "1",
    }
    assert decode_license(VALID_INSTANCE_TWO_LICENSE) == {
        "version": 1,
        "id": "1",
        "valid_from": "2021-08-29T19:52:57.842696",
        "valid_through": "2021-09-29T19:52:57.842696",
        "product_code": "premium",
        "seats": 1,
        "issued_on": "2021-08-29T19:52:57.842696",
        "issued_to_email": "bram@baserow.io",
        "issued_to_name": "Bram",
        "instance_id": "2",
    }


@override_settings(DEBUG=True)
def test_invalid_signature_decode_license():
    with pytest.raises(InvalidPremiumLicenseError):
        decode_license(INVALID_SIGNATURE_LICENSE)

    with pytest.raises(InvalidPremiumLicenseError):
        decode_license(INVALID_PAYLOAD_LICENSE)

    with pytest.raises(InvalidPremiumLicenseError):
        decode_license(b"test")

    with pytest.raises(InvalidPremiumLicenseError):
        decode_license(b"test.test")

    with pytest.raises(InvalidPremiumLicenseError):
        decode_license(b"test.test==")

    with pytest.raises(InvalidPremiumLicenseError):
        decode_license(b"eyJ2ZXJzaW9uIjog.rzAyL6qBkz_Eb==")

    with pytest.raises(InvalidPremiumLicenseError):
        decode_license(NOT_JSON_PAYLOAD_LICENSE)


@override_settings(DEBUG=True)
def test_unsupported_version_decode_license():
    with pytest.raises(UnsupportedPremiumLicenseError):
        decode_license(INVALID_VERSION_LICENSE)


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_register_license_with_authority_check_ok(data_fixture):
    data_fixture.update_settings(instance_id="1")
    admin_user = data_fixture.create_user(is_staff=True)

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://172.17.0.1:8001/api/saas/licenses/check/",
            json={VALID_ONE_SEAT_LICENSE.decode(): {"type": "ok", "detail": ""}},
            status=200,
        )

        license_1 = register_license(admin_user, VALID_ONE_SEAT_LICENSE)
        assert license_1.license == VALID_ONE_SEAT_LICENSE.decode()


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_register_license_with_authority_check_updated(data_fixture):
    data_fixture.update_settings(instance_id="1")
    admin_user = data_fixture.create_user(is_staff=True)

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://172.17.0.1:8001/api/saas/licenses/check/",
            json={
                VALID_ONE_SEAT_LICENSE.decode(): {
                    "type": "update",
                    "detail": "",
                    "new_license_payload": VALID_UPGRADED_TEN_SEAT_LICENSE.decode(),
                }
            },
            status=200,
        )

        license_1 = register_license(admin_user, VALID_ONE_SEAT_LICENSE)
        assert license_1.license == VALID_UPGRADED_TEN_SEAT_LICENSE.decode()
        assert license_1.license_id == "1"


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_register_license_with_authority_check_does_not_exist(data_fixture):
    data_fixture.update_settings(instance_id="1")
    admin_user = data_fixture.create_user(is_staff=True)

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://172.17.0.1:8001/api/saas/licenses/check/",
            json={
                VALID_ONE_SEAT_LICENSE.decode(): {
                    "type": "does_not_exist",
                    "detail": "",
                }
            },
            status=200,
        )

        with pytest.raises(InvalidPremiumLicenseError):
            register_license(admin_user, VALID_ONE_SEAT_LICENSE)


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_register_license_with_authority_check_instance_id_mismatch(data_fixture):
    data_fixture.update_settings(instance_id="1")
    admin_user = data_fixture.create_user(is_staff=True)

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://172.17.0.1:8001/api/saas/licenses/check/",
            json={
                VALID_ONE_SEAT_LICENSE.decode(): {
                    "type": "instance_id_mismatch",
                    "detail": "",
                }
            },
            status=200,
        )

        with pytest.raises(PremiumLicenseInstanceIdMismatchError):
            register_license(admin_user, VALID_ONE_SEAT_LICENSE)


@pytest.mark.django_db
@override_settings(DEBUG=True)
@responses.activate
def test_register_license_with_authority_check_invalid(data_fixture):
    data_fixture.update_settings(instance_id="1")
    admin_user = data_fixture.create_user(is_staff=True)

    with freeze_time("2021-07-01 12:00"):
        responses.add(
            responses.POST,
            "http://172.17.0.1:8001/api/saas/licenses/check/",
            json={
                VALID_ONE_SEAT_LICENSE.decode(): {
                    "type": "invalid",
                    "detail": "",
                }
            },
            status=200,
        )

        with pytest.raises(InvalidPremiumLicenseError):
            register_license(admin_user, VALID_ONE_SEAT_LICENSE)


@pytest.mark.django_db
@override_settings(DEBUG=True)
# We need to activate the responses here, so that the license authority check will
# fail and therefore be ignored. There is another test, that tests the authority
# responses.
@responses.activate
def test_register_license(data_fixture):
    data_fixture.update_settings(instance_id="1")
    normal_user = data_fixture.create_user()
    admin_user = data_fixture.create_user(is_staff=True)

    with pytest.raises(IsNotAdminError):
        register_license(normal_user, VALID_ONE_SEAT_LICENSE)

    with freeze_time("2021-10-01 12:00"):
        with pytest.raises(PremiumLicenseHasExpired):
            register_license(admin_user, VALID_ONE_SEAT_LICENSE)

    with freeze_time("2021-07-01 12:00"):
        license_1 = register_license(admin_user, VALID_ONE_SEAT_LICENSE)
        assert license_1.license == VALID_ONE_SEAT_LICENSE.decode()

        # Check if the license has actually been created.
        all_licenses = License.objects.all()
        assert len(all_licenses) == 1
        assert all_licenses[0].id == license_1.id

    with freeze_time("2021-09-01 12:00"):
        with pytest.raises(PremiumLicenseInstanceIdMismatchError):
            register_license(admin_user, VALID_INSTANCE_TWO_LICENSE)

        with pytest.raises(PremiumLicenseAlreadyExists):
            register_license(admin_user, VALID_ONE_SEAT_LICENSE)

        license_2 = register_license(admin_user, VALID_TWO_SEAT_LICENSE.decode())
        assert license_2.license == VALID_TWO_SEAT_LICENSE.decode()


@pytest.mark.django_db
@override_settings(DEBUG=True)
# We need to activate the responses here, so that the license authority check will
# fail and therefore be ignored. There is another test, that tests the authority
# responses.
@responses.activate
def test_upgrade_license_by_register(data_fixture):
    data_fixture.update_settings(instance_id="1")
    admin_user = data_fixture.create_user(is_staff=True)

    with freeze_time("2021-07-01 12:00"):
        first_license_1 = register_license(admin_user, VALID_ONE_SEAT_LICENSE)
        second_license_1 = register_license(admin_user, VALID_UPGRADED_TEN_SEAT_LICENSE)

        assert first_license_1.id == second_license_1.id
        assert License.objects.all().count() == 1
        assert second_license_1.license_id == "1"
        assert second_license_1.seats == 10


@pytest.mark.django_db
@override_settings(DEBUG=True)
# We need to activate the responses here, so that the license authority check will
# fail and therefore be ignored. There is another test, that tests the authority
# responses.
@responses.activate
def test_register_an_older_license(data_fixture):
    data_fixture.update_settings(instance_id="1")
    admin_user = data_fixture.create_user(is_staff=True)

    with freeze_time("2021-07-01 12:00"):
        register_license(admin_user, VALID_UPGRADED_TEN_SEAT_LICENSE)

        # The same license already exists.
        with pytest.raises(PremiumLicenseAlreadyExists):
            register_license(admin_user, VALID_UPGRADED_TEN_SEAT_LICENSE)

        # An older license already exists.
        with pytest.raises(PremiumLicenseAlreadyExists):
            register_license(admin_user, VALID_ONE_SEAT_LICENSE)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_remove_license(data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    admin_1 = data_fixture.create_user(is_staff=True)

    license_object = License.objects.create(license=VALID_TWO_SEAT_LICENSE.decode())
    LicenseUser.objects.create(license=license_object, user=user_1)
    license_object_2 = License.objects.create(license=VALID_TWO_SEAT_LICENSE.decode())
    LicenseUser.objects.create(license=license_object_2, user=user_1)
    LicenseUser.objects.create(license=license_object_2, user=user_2)

    with pytest.raises(IsNotAdminError):
        remove_license(user_1, license_object)

    remove_license(admin_1, license_object_2)
    licenses = License.objects.all()
    assert len(licenses) == 1
    assert licenses[0].id == license_object.id
    license_users = LicenseUser.objects.all()
    assert len(license_users) == 1
    assert license_users[0].user_id == user_1.id
    assert license_users[0].license_id == license_object.id


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
@patch("baserow_premium.license.handler.broadcast_to_users")
def test_add_user_to_license(mock_broadcast_to_users, data_fixture):
    with freeze_time("2021-09-01 12:00"):
        user_1 = data_fixture.create_user()
        user_2 = data_fixture.create_user()
        admin_1 = data_fixture.create_user(is_staff=True)
        license_object = License.objects.create(license=VALID_ONE_SEAT_LICENSE.decode())

        with pytest.raises(IsNotAdminError):
            add_user_to_license(user_1, license_object, user_1)

        license_user = add_user_to_license(admin_1, license_object, user_1)

        assert license_user.user_id == user_1.id
        assert license_user.license_id == license_object.id

        mock_broadcast_to_users.delay.assert_called_once()
        args = mock_broadcast_to_users.delay.call_args
        assert args[0][0] == [user_1.id]
        assert args[0][1]["type"] == "user_data_updated"
        assert args[0][1]["user_data"] == {"premium": {"valid_license": True}}

        with pytest.raises(UserAlreadyOnPremiumLicenseError):
            add_user_to_license(admin_1, license_object, user_1)

        with pytest.raises(NoSeatsLeftInPremiumLicenseError):
            add_user_to_license(admin_1, license_object, user_2)


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
@patch("baserow_premium.license.handler.broadcast_to_users")
def test_remove_user_from_license(mock_broadcast_to_users, data_fixture):
    with freeze_time("2021-09-01 12:00"):
        user_1 = data_fixture.create_user()
        admin_1 = data_fixture.create_user(is_staff=True)

        license_object = License.objects.create(license=VALID_ONE_SEAT_LICENSE.decode())
        LicenseUser.objects.create(license=license_object, user=user_1)

        with pytest.raises(IsNotAdminError):
            remove_user_from_license(user_1, license_object, user_1)

        with transaction.atomic():
            remove_user_from_license(admin_1, license_object, user_1)

        assert LicenseUser.objects.all().count() == 0

        mock_broadcast_to_users.delay.assert_called_once()
        args = mock_broadcast_to_users.delay.call_args
        assert args[0][0] == [user_1.id]
        assert args[0][1]["type"] == "user_data_updated"
        assert args[0][1]["user_data"] == {"premium": {"valid_license": False}}


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
@patch("baserow_premium.license.handler.broadcast_to_users")
def test_fill_remaining_seats_in_license(mock_broadcast_to_users, data_fixture):
    with freeze_time("2021-09-01 12:00"):
        user_1 = data_fixture.create_user()
        user_2 = data_fixture.create_user()
        data_fixture.create_user()
        admin_1 = data_fixture.create_user(is_staff=True)

        license_object = License.objects.create(license=VALID_TWO_SEAT_LICENSE.decode())
        LicenseUser.objects.create(license=license_object, user=user_1)

        with pytest.raises(IsNotAdminError):
            fill_remaining_seats_of_license(user_1, license_object)

        fill_remaining_seats_of_license(admin_1, license_object)
        license_users = LicenseUser.objects.filter(license=license_object).order_by(
            "user_id"
        )
        assert len(license_users) == 2
        assert license_users[0].license_id == license_object.id
        assert license_users[0].user_id == user_1.id
        assert license_users[1].license_id == license_object.id
        assert license_users[1].user_id == user_2.id

        mock_broadcast_to_users.delay.assert_called_once()
        args = mock_broadcast_to_users.delay.call_args
        assert len(args[0][0]) == 1
        assert args[0][0][0] == user_2.id
        assert args[0][1]["type"] == "user_data_updated"
        assert args[0][1]["user_data"] == {"premium": {"valid_license": True}}

        license_object_2 = License.objects.create(
            license=VALID_ONE_SEAT_LICENSE.decode()
        )
        created_license_users = fill_remaining_seats_of_license(
            admin_1, license_object_2
        )
        assert len(created_license_users) == 1
        assert created_license_users[0].license_id == license_object_2.id
        assert created_license_users[0].user_id == user_1.id
        assert LicenseUser.objects.all().count() == 3
        license_users = LicenseUser.objects.filter(license=license_object_2).order_by(
            "user_id"
        )
        assert len(license_users) == 1
        assert license_users[0].license_id == license_object_2.id
        assert license_users[0].user_id == user_1.id


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
@patch("baserow_premium.license.handler.broadcast_to_users")
def test_remove_all_users_from_license(mock_broadcast_to_users, data_fixture):
    with freeze_time("2021-09-01 12:00"):
        user_1 = data_fixture.create_user()
        user_2 = data_fixture.create_user()
        admin_1 = data_fixture.create_user(is_staff=True)

        license_object = License.objects.create(license=VALID_TWO_SEAT_LICENSE.decode())
        LicenseUser.objects.create(license=license_object, user=user_1)
        license_object_2 = License.objects.create(
            license=VALID_TWO_SEAT_LICENSE.decode()
        )
        LicenseUser.objects.create(license=license_object_2, user=user_1)
        LicenseUser.objects.create(license=license_object_2, user=user_2)

        with pytest.raises(IsNotAdminError):
            remove_all_users_from_license(user_1, license_object)

        remove_all_users_from_license(admin_1, license_object_2)
        license_users = LicenseUser.objects.all()
        assert len(license_users) == 1
        assert license_users[0].license_id == license_object.id
        assert license_users[0].user_id == user_1.id
        assert LicenseUser.objects.all().count() == 1

        mock_broadcast_to_users.delay.assert_called_once()
        args = mock_broadcast_to_users.delay.call_args
        assert len(args[0][0]) == 2
        assert user_1.id in args[0][0]
        assert user_2.id in args[0][0]
        assert args[0][1]["type"] == "user_data_updated"
        assert args[0][1]["user_data"] == {"premium": {"valid_license": False}}
