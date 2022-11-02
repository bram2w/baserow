import os
from xml.etree import ElementTree

from baserow_enterprise.sso.saml.models import SamlAuthProviderModel


def load_test_idp_metadata():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    idp_test_metadata = ElementTree.parse(
        os.path.join(dir_path, "idp_test_metadata.xml")
    )
    return ElementTree.tostring(idp_test_metadata.getroot()).decode("utf-8")


class SamlFixture:
    test_idp_metadata = load_test_idp_metadata()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_test_saml_idp_metadata(self):
        return self.test_idp_metadata

    def create_saml_auth_provider(self, **kwargs):
        if "domain" not in kwargs:
            kwargs["domain"] = self.fake.domain_name()

        if "metadata" not in kwargs:
            kwargs["metadata"] = self.get_test_saml_idp_metadata()

        if "enabled" not in kwargs:
            kwargs["enabled"] = True

        if "is_verified" not in kwargs:
            kwargs["is_verified"] = False

        return SamlAuthProviderModel.objects.create(**kwargs)
