import faker
from baserow_premium.license.handler import LicenseHandler

from baserow.core.models import Settings
from baserow.test_utils.fixtures import Fixtures

from .sso import SamlFixture

VALID_ONE_SEAT_ENTERPRISE_LICENSE = (
    # id: "1", instance_id: "1"
    b"eyJ2ZXJzaW9uIjogMSwgImlkIjogIjUzODczYmVkLWJlNTQtNDEwZS04N2EzLTE2OTM2ODY2YjBiNiIsICJ2YWxpZF9mcm9tIjogIjIwMjItMTAtMDFUMDA6MDA6MDAiLCAidmFsaWRfdGhyb3VnaCI6ICIyMDY5LTA4LTA5VDIzOjU5OjU5IiwgInByb2R1Y3RfY29kZSI6ICJlbnRlcnByaXNlIiwgInNlYXRzIjogMSwgImlzc3VlZF9vbiI6ICIyMDIyLTEwLTI2VDE0OjQ4OjU0LjI1OTQyMyIsICJpc3N1ZWRfdG9fZW1haWwiOiAidGVzdEB0ZXN0LmNvbSIsICJpc3N1ZWRfdG9fbmFtZSI6ICJ0ZXN0QHRlc3QuY29tIiwgImluc3RhbmNlX2lkIjogIjEifQ==.B7aPXR0R4Fxr28AL7B5oopa2Yiz_MmEBZGdzSEHHLt4wECpnzjd_SF440KNLEZYA6WL1rhNkZ5znbjYIp6KdCqLdcm1XqNYOIKQvNTOtl9tUAYj_Qvhq1jhqSja-n3HFBjIh9Ve7a6T1PuaPLF1DoxSRGFZFXliMeJRBSzfTsiHiO22xRQ4GwafscYfUIWvIJJHGHtYEd9rk0tG6mfGEaQGB4e6KOsN-zw-bgLDBOKmKTGrVOkZnaGHBVVhUdpBn25r3CFWqHIApzUCo81zAA96fECHPlx_fBHhvIJXLsN5i3LdeJlwysg5SBO15Vt-tsdPmdcsec-fOzik-k3ib0A== "
)


data_fixture = Fixtures()


class EnterpriseFixtures(SamlFixture):
    faker = faker.Faker()

    def create_enterprise_admin_user_and_token(self, **kwargs):
        Settings.objects.update_or_create(defaults={"instance_id": "1"})
        user, token = data_fixture.create_user_and_token(is_staff=True, **kwargs)
        LicenseHandler.register_license(user, VALID_ONE_SEAT_ENTERPRISE_LICENSE)
        return user, token
