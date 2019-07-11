import pytest


@pytest.fixture
def data_fixture():
    from .fixtures import Fixtures
    return Fixtures()
