from collections import defaultdict
from typing import Dict, Generator, List, Set, Union

from django.contrib.auth.models import AbstractUser

# noinspection PyUnresolvedReferences
import pytest
from baserow_premium.license.license_types import PremiumLicenseType
from baserow_premium.license.plugin import LicensePlugin
from baserow_premium.license.registries import LicenseType, license_type_registry
from baserow_premium.plugins import PremiumPlugin

from baserow.test_utils.pytest_conftest import *  # noqa: F403, F401


@pytest.fixture
def premium_data_fixture(data_fixture):
    from .fixtures import PremiumFixtures

    class PremiumFixtures(PremiumFixtures, data_fixture.__class__):
        pass

    return PremiumFixtures()


@pytest.fixture
def mutable_plugin_registry():
    from baserow.core.registries import plugin_registry

    before = plugin_registry.registry.copy()
    yield plugin_registry
    plugin_registry.registry = before


class PerGroupLicensePlugin(LicensePlugin):
    def __init__(self):
        super().__init__()
        self.per_group_licenses = defaultdict(lambda: defaultdict(set))

    def get_active_instance_wide_licenses(
        self, user: AbstractUser
    ) -> Generator[LicenseType, None, None]:
        return
        yield

    def get_active_per_group_licenses(
        self, user: AbstractUser
    ) -> Dict[int, Set[LicenseType]]:
        return self.per_group_licenses[user.id]

    def restrict_user_premium_to(
        self, user: AbstractUser, group_ids_or_id: Union[int, List[int]]
    ):
        if isinstance(group_ids_or_id, int):
            group_ids_or_id = [group_ids_or_id]
        self.per_group_licenses[user.id] = defaultdict(set)
        for group_id in group_ids_or_id:
            self.per_group_licenses[user.id][group_id].add(
                license_type_registry.get(PremiumLicenseType.type)
            )


class PremiumPluginWithPerGroupLicensePlugin(PremiumPlugin):
    license_plugin = PerGroupLicensePlugin()

    def get_license_plugin(self) -> LicensePlugin:
        return self.license_plugin


@pytest.fixture
def alternative_per_group_license_service(
    mutable_plugin_registry,
) -> PerGroupLicensePlugin:
    """
    Overrides the existing license service with a test only stub version that
    allows configuring whether or not a user has premium features at a per group level.
    """

    stub_premium_plugin = PremiumPluginWithPerGroupLicensePlugin()
    mutable_plugin_registry.registry[PremiumPlugin.type] = stub_premium_plugin

    yield stub_premium_plugin.get_license_plugin()
