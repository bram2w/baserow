import pytest

from unittest.mock import patch

from baserow_premium.license.tasks import license_check


@pytest.mark.django_db
@patch("baserow_premium.license.handler.check_licenses")
def test_license_check(mock_check_licenses, premium_data_fixture):
    license_check()

    assert not mock_check_licenses.called

    premium_data_fixture.create_premium_license()
    license_check()

    assert mock_check_licenses.called
