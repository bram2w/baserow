from collections import defaultdict
from typing import Any, Dict, List, Union

from django.contrib.auth.models import AbstractUser

# noinspection PyUnresolvedReferences
import pytest
from baserow_premium.license.license_types import PremiumLicenseType
from baserow_premium.license.registries import LicenseType

from baserow.test_utils.pytest_conftest import *  # noqa: F403, F401


@pytest.fixture
def premium_data_fixture(data_fixture):
    from .fixtures import PremiumFixtures

    class PremiumFixtures(PremiumFixtures, data_fixture.__class__):
        pass

    return PremiumFixtures()


@pytest.fixture
def mutable_license_type_registry():
    from baserow_premium.license.registries import license_type_registry

    before = license_type_registry.registry.copy()
    yield license_type_registry
    license_type_registry.registry = before


class PerGroupPremiumLicenseType(LicenseType):
    type = PremiumLicenseType.type

    def __init__(self):
        super().__init__()
        self.per_user_id_license_object_lists = defaultdict(list)

    def has_global_prem_or_specific_groups(
        self, user: AbstractUser
    ) -> Union[bool, List[Dict[str, Any]]]:
        return self.per_user_id_license_object_lists[user.id]

    def restrict_user_premium_to(
        self, user: AbstractUser, group_ids_to_restrict_premium_to: List[int]
    ):
        self.per_user_id_license_object_lists[user.id] = [
            {"type": "group", "id": group_id}
            for group_id in group_ids_to_restrict_premium_to
        ]


@pytest.fixture
def alternative_per_group_premium_license_type(mutable_license_type_registry):
    """
    Overrides the existing premium license type with a test only stub version that
    allows configuring whether or not a user has premium at a per group level.
    """

    stub_license_type = PerGroupPremiumLicenseType()
    mutable_license_type_registry.registry[
        PerGroupPremiumLicenseType.type
    ] = stub_license_type

    yield stub_license_type
