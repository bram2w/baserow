import contextlib
from collections import defaultdict
from decimal import Decimal
from math import ceil
from typing import Any, Callable, Iterable, List, Optional, Tuple, TypeVar

from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS, connection, transaction
from django.db.models import Max, Model, QuerySet
from django.db.models.sql.query import LOOKUP_SEP
from django.db.transaction import Atomic, get_connection

from psycopg2 import sql

from .utils import find_intermediate_order


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


T = TypeVar("T", bound=Model)


def specific_iterator(
    queryset: QuerySet[T],
    per_content_type_queryset_hook: Callable = None,
) -> Iterable[T]:
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
    :param per_content_type_queryset_hook: If provided, it will be called for every
        specific queryset to allow extending it.
    """

    # Figure out beforehand what the annotation keys and select related keys are.
    # This way, we can later set those properties on the specific objects.
    annotation_keys = queryset.query.annotations.keys()
    select_related = queryset.query.select_related

    if isinstance(select_related, bool):
        select_related_keys = []
    else:
        select_related_keys = select_related.keys()

    # Nested prefetch result in cached objects to avoid additional queries. If
    # they're present, they must be added to the `select_related_keys` to make sure
    # they're correctly set on the specific objects.
    for lookup in queryset._prefetch_related_lookups:
        split_lookup = lookup.split(LOOKUP_SEP)[:-1]
        if split_lookup and split_lookup[0] not in select_related_keys:
            select_related_keys.append(split_lookup[0])

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

        if per_content_type_queryset_hook is not None:
            objects = per_content_type_queryset_hook(model, objects)

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

        # If the original item has the `_prefetched_objects_cache` object, it means that
        # the `prefetch_related` was used and fetched on the base queryset. By
        # setting it on the specific object, we move that prefetched data over so
        # that we don't have to execute the same query again.
        if hasattr(item, "_prefetched_objects_cache"):
            specific_prefetched_objects_cache = getattr(
                specific_object, "_prefetched_objects_cache", {}
            )
            specific_object._prefetched_objects_cache = {
                **item._prefetched_objects_cache,
                **specific_prefetched_objects_cache,
            }

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
                cursor.execute(first_sql.format(*first_args))
        yield a


def get_unique_orders_before_item(
    before: Model,
    queryset: QuerySet,
    amount: int = 1,
    field: str = "order",
) -> List[Decimal]:
    """
    Calculates a list of unique decimal orders that can safely be used before the
    provided `before`.

    :param before: The model instance where the before orders must be
        calculated for.
    :param queryset: The base queryset used to compute the value.
    :param amount: The number of orders that must be requested. Can be higher if
        multiple items are inserted or moved.
    :raises CannotCalculateIntermediateOrder: If it's not possible to recalculate an
        intermediate order. The full order of the items must be recalculated in this
        case before calling this function again.
    :return: A list of decimals containing safe to use orders in order.
    """

    # In order to find the intermediate order, we need to figure out what the
    # order of the before adjacent row is. This queryset finds it in an
    # efficient way.
    adjacent_order = (
        queryset.filter(order__lt=before.order).aggregate(max=Max(field)).get("max")
    ) or Decimal("0")
    new_orders = []
    new_order = adjacent_order
    for i in range(0, amount):
        float_order = find_intermediate_order(new_order, before.order)
        # Row orders "only" store 20 decimal places. We're already rounding it,
        # so that the `order` will be set immediately.
        new_order = round(Decimal(float_order), 20)
        new_orders.append(new_order)
    return new_orders


def get_highest_order_of_queryset(
    queryset: QuerySet,
    amount: int = 1,
    field: str = "order",
) -> List[Decimal]:
    """
    Returns the highest existing values of the provided order field.

    :param queryset: The queryset containing the field to check.
    :param amount: The amount of order to return.
    :param field: The field name containing the value.
    :return: A list of highest order value in the queryset.
    """

    step = Decimal("1.00000000000000000000")
    last_order = ceil(queryset.aggregate(max=Max(field)).get("max") or Decimal("0"))
    return [last_order + (step * i) for i in range(1, amount + 1)]


def recalculate_full_orders(
    model: Optional[Model] = None,
    field="order",
    queryset: Optional[QuerySet] = None,
):
    """
    Recalculates the order to whole numbers of all instances based on the existing
    position.

    id     old_order    new_order
    1      1.5000       2.0000
    2      1.7500       3.0000
    3      0.7500       1.0000

    :param model: The model we want to reorder the instance for.
    :param field: The order field name.
    :param queryset: An optional queryset to filter the item orders that are
        recalculated. This queryset must select all the item to recalculate.
    """

    table_name = model.objects.model._meta.db_table
    ordering = model._meta.ordering

    if queryset:
        item_ids = queryset.values_list("id", flat=True)
        where_clause = sql.SQL("where c2.id in ({id_list})").format(
            id_list=sql.SQL(", ").join([sql.Literal(item_id) for item_id in item_ids])
        )
    else:
        where_clause = sql.SQL("")

    # Unfortunately, it's not possible to do this via the Django ORM. I've
    # tried various ways, but ran into "Window expressions are not allowed" or
    # 'NoneType' object has no attribute 'get_source_expressions' errors.
    # More information can be found here:
    # https://stackoverflow.com/questions/66022483/update-django-model-based-on-the-row-number-of-rows-produced-by-a-subquery-on-th
    #
    # model.objects_and_trash.annotate(
    #     row_number=Window(
    #         expression=RowNumber(),
    #         order_by=[F(order) for order in model._meta.ordering],
    #         )
    #     ).update(order=F('row_number')
    # )
    raw_query = """
        update {table_name} c1
            set {order_field} = c2.seqnum from (
            select c2.*, row_number() over (
                ORDER BY {order_params}
            ) as seqnum from {table_name} c2 {where_clause}
            ) c2
        where c2.id = c1.id"""
    with connection.cursor() as cursor:
        sql_query = sql.SQL(raw_query).format(
            order_field=sql.Identifier(field),
            table_name=sql.Identifier(table_name),
            order_params=sql.SQL(", ").join(
                [
                    sql.SQL(".").join([sql.Identifier("c2"), sql.Identifier(o)])
                    for o in ordering
                ]
            ),
            where_clause=where_clause,
        )
        cursor.execute(sql_query)
