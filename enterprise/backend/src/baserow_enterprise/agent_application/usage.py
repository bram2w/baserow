from datetime import datetime, timedelta, tzinfo
from datetime import timezone as dt_timezone
from decimal import Decimal
from typing import Optional

from django.db import connection
from django.db.models import Q, Sum
from django.utils import timezone

from .models import AgentUsage

PERIODS = ("today", "week", "month", "lifetime")


class AgentUsageHandler:
    def record(
        self,
        application_id: int,
        input_tokens: int,
        output_tokens: int,
        cost: Optional[Decimal],
        at: Optional[datetime] = None,
    ) -> None:
        """
        Adds one turn to the hour it happened in. A single upsert that adds to
        the stored values, so concurrent runs of the same agent never
        overwrite each other.

        :param cost: The cost in USD, or None when the model has no known
            price, which counts the turn as unpriced.
        """

        hour = (at or timezone.now()).astimezone(dt_timezone.utc)
        hour = hour.replace(minute=0, second=0, microsecond=0)
        table = AgentUsage._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {table}
                    (application_id, hour, input_tokens, output_tokens, cost,
                     turns, unpriced_turns)
                VALUES (%s, %s, %s, %s, %s, 1, %s)
                ON CONFLICT (application_id, hour) DO UPDATE SET
                    input_tokens = {table}.input_tokens + EXCLUDED.input_tokens,
                    output_tokens = {table}.output_tokens + EXCLUDED.output_tokens,
                    cost = {table}.cost + EXCLUDED.cost,
                    turns = {table}.turns + 1,
                    unpriced_turns = {table}.unpriced_turns
                        + EXCLUDED.unpriced_turns
                """,  # noqa: S608
                [
                    application_id,
                    hour,
                    input_tokens or 0,
                    output_tokens or 0,
                    cost or 0,
                    0 if cost is not None else 1,
                ],
            )

    def get_period_starts(self, now: datetime, viewer_timezone: tzinfo) -> dict:
        """
        Where today, this week (starting on Monday) and this month begin for
        someone in the given timezone, in UTC.
        """

        local_now = now.astimezone(viewer_timezone)
        day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        return {
            "today": day,
            "week": day - timedelta(days=day.weekday()),
            "month": day.replace(day=1),
        }

    def get_usage(self, application, viewer_timezone: tzinfo) -> dict:
        """
        The usage of today, this week, this month and the lifetime of the
        agent, in a single query over its hourly rows.
        """

        starts = self.get_period_starts(timezone.now(), viewer_timezone)
        aggregates = {}
        for period in PERIODS:
            period_filter = Q(hour__gte=starts[period]) if period in starts else Q()
            aggregates.update(
                {
                    f"{period}_input_tokens": Sum(
                        "input_tokens", filter=period_filter, default=0
                    ),
                    f"{period}_output_tokens": Sum(
                        "output_tokens", filter=period_filter, default=0
                    ),
                    f"{period}_cost": Sum("cost", filter=period_filter, default=0),
                    f"{period}_turns": Sum("turns", filter=period_filter, default=0),
                    f"{period}_unpriced_turns": Sum(
                        "unpriced_turns", filter=period_filter, default=0
                    ),
                }
            )
        totals = AgentUsage.objects.filter(application=application).aggregate(
            **aggregates
        )
        return {
            period: {
                key: totals[f"{period}_{key}"]
                for key in (
                    "input_tokens",
                    "output_tokens",
                    "cost",
                    "turns",
                    "unpriced_turns",
                )
            }
            for period in PERIODS
        }
