import pytest

# noinspection PyUnresolvedReferences
from baserow.test_utils.pytest_conftest import *  # noqa: F403, F401


@pytest.fixture
def premium_data_fixture(data_fixture):
    from .fixtures import PremiumFixtures

    class PremiumFixtures(PremiumFixtures, data_fixture.__class__):
        pass

    return PremiumFixtures()
