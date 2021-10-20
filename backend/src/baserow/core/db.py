from django.db import DEFAULT_DB_ALIAS
from django.db.transaction import Atomic, get_connection


class LockedAtomicTransaction(Atomic):
    """
    Does a atomic transaction, but also locks the entire table for any transactions,
    for the duration of this transaction. Although this is the only way to avoid
    concurrency issues in certain situations, it should be used with caution,
    since it has impacts on performance, for obvious reasons...
    """

    def __init__(self, model, using=None, savepoint=True, durable=False):
        if using is None:
            using = DEFAULT_DB_ALIAS

        super().__init__(using, savepoint, durable)
        self.model = model

    def __enter__(self):
        super(LockedAtomicTransaction, self).__enter__()

        cursor = None
        try:
            cursor = get_connection(self.using).cursor()
            cursor.execute(
                "LOCK TABLE {db_table_name}".format(
                    db_table_name=self.model._meta.db_table
                )
            )
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def __exit__(self, *args, **kwargs):
        return super().__exit__(*args, **kwargs)
