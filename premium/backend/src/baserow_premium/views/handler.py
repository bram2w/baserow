from collections import defaultdict
from typing import Dict, Optional, Union

from django.db.models import Count, Q, QuerySet

from baserow_premium.views.models import OWNERSHIP_TYPE_PERSONAL

from baserow.contrib.database.fields.models import SingleSelectField
from baserow.contrib.database.table.models import GeneratedTableModel
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View


def get_rows_grouped_by_single_select_field(
    view: View,
    single_select_field: SingleSelectField,
    option_settings: Dict[str, Dict[str, int]] = None,
    default_limit: int = 40,
    default_offset: int = 0,
    model: Optional[GeneratedTableModel] = None,
    base_queryset: Optional[QuerySet] = None,
) -> Dict[str, Dict[str, Union[int, list]]]:
    """
    This method fetches the rows grouped by a single select field in a query
    efficient manner. Optionally `limit` and `offset` settings can be provided per
    option. If the option settings not provided, then rows for all the select options
    will be fetched. If one or more options have been provided, then only the rows
    for those will be fetched.

    Example:

    get_rows_grouped_by_single_select_field(
        ...
        options_settings={
            "1": {"limit": 10, "offset": 10},
            "2": {"limit": 10, "offset": 20}
        }
    )

    :param view: The view where to fetch the fields from.
    :param single_select_field: The single select field where the rows must be
        grouped by.
    :param option_settings: Optionally, additional `limit` and `offset`
        configurations per field option can be provided.
    :param default_limit: The default limit that applies to all options if no
        specific settings for that field have been provided.
    :param default_offset: The default offset that applies to all options if no
        specific settings for that field have been provided.
    :param model: Additionally, an existing model can be provided so that it doesn't
        have to be generated again.
    :param base_queryset: Optionally an alternative base queryset can be provided
        that will be used to fetch the rows. This should be provided if additional
        filters and/or sorts must be added.
    :return: The fetched rows including the total count.
    """

    table = view.table

    if option_settings is None:
        option_settings = {}

    if model is None:
        model = table.get_model()

    if base_queryset is None:
        base_queryset = model.objects.all().enhance_by_fields().order_by("order", "id")

    base_option_queryset = ViewHandler().apply_filters(view, base_queryset)
    all_filters = Q()
    count_aggregates = {}
    all_options = list(single_select_field.select_options.all())
    all_option_ids = [option.id for option in all_options]

    def get_id_and_string(option):
        return (
            option.id if option else None,
            str(option.id) if option else "null",
        )

    for select_option in [None] + all_options:
        option_id, option_string = get_id_and_string(select_option)

        # If option settings have been provided, we only want to return rows for
        # those options, otherwise we will include all options.
        if len(option_settings) > 0 and option_string not in option_settings:
            continue

        option_setting = option_settings.get(option_string, {})
        limit = option_setting.get("limit", default_limit)
        offset = option_setting.get("offset", default_offset)

        if option_id is None:
            # Somehow the `Count` aggregate doesn't support an empty `__in` lookup.
            # That's why we always add the `-1` value that never exists to make sure
            # there is always a value in there.
            filters = ~Q(
                **{f"field_{single_select_field.id}_id__in": all_option_ids + [-1]}
            )
        else:
            filters = Q(**{f"field_{single_select_field.id}_id": option_id})

        # We don't want to execute a single query for each select option,
        # so we create a subquery that finds the ids of the rows related to the
        # option group. After the single query has been executed we can group the rows.
        sub_queryset = base_option_queryset.filter(filters).values_list(
            "id", flat=True
        )[offset : offset + limit]
        all_filters |= Q(id__in=sub_queryset)

        # Same goes for fetching the total count. We will construct a single query,
        # that calculates to total amount of rows per option.
        count_aggregates[option_string] = Count(
            "pk",
            filter=filters,
        )

    queryset = list(base_queryset.filter(all_filters))
    counts = base_option_queryset.aggregate(**count_aggregates)

    rows = defaultdict(lambda: {"count": 0, "results": []})

    for row in queryset:
        option_id = getattr(row, f"field_{single_select_field.id}_id")
        option_string = str(option_id) if option_id in all_option_ids else "null"
        rows[option_string]["results"].append(row)

    for key, value in counts.items():
        rows[key]["count"] = value

    return rows


def delete_personal_views(user_id: int):
    """
    Deletes all personal views associated with the provided user.

    :param user_id: The id of the user for whom to delete personal views.
    """

    View.objects.filter(ownership_type=OWNERSHIP_TYPE_PERSONAL).filter(
        created_by__id=user_id
    ).delete()
