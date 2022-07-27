import contextlib
from collections import defaultdict
from typing import Iterable, Optional, Tuple, List, Any

from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS, transaction
from django.db.models import QuerySet, Model
from django.db.transaction import Atomic, get_connection
from psycopg2 import sql


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


def specific_iterator(queryset: QuerySet) -> Iterable[Model]:
    """
    Iterates over the given queryset and finds the specific objects with the least
    amount of queries. It respects the annotations, select related and prefetch
    related of the provided query. This function is only compatible with models
    having the `PolymorphicContentTypeMixin` and `content_type property.`

    Can be used like:

    for specific_object in specific_iterator(Application.objects.all()):
        print(type(specific_object))  # Database

    :param queryset: The queryset to the base model of which we want to select the
        specific types from.
    """

    # Figure out beforehand what the annotation keys and select related keys are.
    # This way, we can later set those properties on the specific objects.
    annotation_keys = queryset.query.annotations.keys()
    select_related = queryset.query.select_related

    if isinstance(select_related, bool):
        select_related_keys = []
    else:
        select_related_keys = select_related.keys()

    # The original queryset must resolved because we need the pk, content type,
    # annotated data and selected related data. By forcing it to resolve early on,
    # we prevent accidentally resolving it multiple times.
    base_model = queryset.model
    resolved_queryset = list(queryset)

    types_and_pks = defaultdict(list)
    for item in resolved_queryset:
        content_type = ContentType.objects.get_for_id(item.content_type_id)
        types_and_pks[content_type].append(item.id)

    # Fetch the specific objects by executing a single query for each unique content
    # type and construct a mapping containing them by id.
    specific_objects = {}
    for content_type, pks in types_and_pks.items():
        model = content_type.model_class() or queryset.model
        # We deliberately want to use the `_base_manager` here so it's works exactly
        # the same as the `.specific` property and so that trashed objects will still
        # be fetched.
        objects = model._base_manager.filter(pk__in=pks)

        for object in objects:
            specific_objects[object.id] = object

    # Create an array with specific objects in the right order.
    ordered_specific_objects = []
    for item in resolved_queryset:
        # If the specific object is not found, but the base object is, it means that
        # there is a data integrity error. In that case, we want to fail hard.
        try:
            specific_object = specific_objects[item.id]
        except KeyError:
            raise base_model.DoesNotExist(
                f"The specific object with id {item.id} does not exist."
            )

        # If there are annotation keys, we must extract them from the original item
        # because they should exist there and set them on the specific object so they
        # can be used from there.
        if annotation_keys:
            for annotation_key in annotation_keys:
                if hasattr(item, annotation_key):
                    setattr(
                        specific_object, annotation_key, getattr(item, annotation_key)
                    )

        if select_related_keys:
            for select_related_key in select_related_keys:
                if hasattr(item, select_related_key):
                    setattr(
                        specific_object,
                        select_related_key,
                        getattr(item, select_related_key),
                    )

        # If the original item has the `_prefetched_objects_cache`, it means that the
        # `prefetch_related`. By setting it on the specific object, we move that
        # prefetched data over so that we don't have to execute the same query again.
        if hasattr(item, "_prefetched_objects_cache"):
            specific_object._prefetched_objects_cache = item._prefetched_objects_cache

        ordered_specific_objects.append(specific_object)

    return ordered_specific_objects


class IsolationLevel:
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


@contextlib.contextmanager
def transaction_atomic(
    using=None,
    savepoint=True,
    durable=False,
    isolation_level: Optional[str] = None,
    first_sql_to_run_in_transaction_with_args: Optional[
        Tuple[sql.SQL, List[Any]]
    ] = None,
):
    with transaction.atomic(using, savepoint, durable) as a:
        if isolation_level or first_sql_to_run_in_transaction_with_args:
            cursor = get_connection(using).cursor()

            if isolation_level:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL %s" % isolation_level)

            if first_sql_to_run_in_transaction_with_args:
                first_sql, first_args = first_sql_to_run_in_transaction_with_args
                cursor.execute(first_sql, first_args)
        yield a
