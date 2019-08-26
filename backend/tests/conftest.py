import pytest


@pytest.fixture
def data_fixture():
    from .fixtures import Fixtures
    return Fixtures()


@pytest.fixture()
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
