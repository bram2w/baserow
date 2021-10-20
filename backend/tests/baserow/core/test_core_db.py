import pytest

from django.db import connection
from django.test.utils import override_settings

from baserow.core.db import LockedAtomicTransaction
from baserow.core.models import Settings


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_locked_atomic_transaction(api_client, data_fixture):
    def is_locked(model):
        with connection.cursor() as cursor:
            table_name = model._meta.db_table
            cursor.execute(
                "select count(*) from pg_locks l join pg_class t on l.relation = "
                "t.oid WHERE relname = %(table_name)s;",
                {"table_name": table_name},
            )
            return cursor.fetchone()[0] > 0

    assert not is_locked(Settings)

    with LockedAtomicTransaction(Settings):
        assert is_locked(Settings)
