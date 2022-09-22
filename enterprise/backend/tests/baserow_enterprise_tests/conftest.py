import pytest

# noinspection PyUnresolvedReferences
from baserow.test_utils.pytest_conftest import *  # noqa: F403, F401


@pytest.fixture
def enterprise_data_fixture(data_fixture):
    from .fixtures import EnterpriseFixtures

    class EnterpriseFixtures(EnterpriseFixtures, data_fixture.__class__):
        pass

    return EnterpriseFixtures()
