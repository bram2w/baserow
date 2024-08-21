from unittest.mock import patch

import pytest
from fakeredis import FakeRedis, FakeServer


@pytest.fixture(scope="function", autouse=True)
def mock_periodic_field_update_handler_redis_client():
    redis_client_fn = "baserow.contrib.database.fields.periodic_field_update_handler._get_redis_client"
    fake_redis_server = FakeServer()
    with patch(
        redis_client_fn, lambda: FakeRedis(server=fake_redis_server)
    ) as _fixture:
        yield _fixture
