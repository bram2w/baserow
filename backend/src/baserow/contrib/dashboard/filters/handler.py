from baserow.contrib.dashboard.data_sources.models import DashboardDataSource
from baserow.contrib.database.fields.models import Field
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceFilterGroup,
)
from baserow.core.models import TrashEntry
from baserow.core.utils import extract_allowed

from .exceptions import DashboardFilterDoesNotExist
from .models import DashboardFilter
from .operators import get_text_filter_operators
from .references import get_referenced_dashboard_filters


class DashboardFilterHandler:
    allowed_fields = (
        "label",
        "type",
        "operator",
        "mode",
        "multiple",
        "formula_name",
        "formula_value",
    )

    def get_filter(self, filter_id, for_update=False):
        queryset = DashboardFilter.objects.select_related("dashboard__workspace")
        if for_update:
            queryset = queryset.select_for_update(of=("self",))
        try:
            return queryset.get(
                id=filter_id,
                dashboard__trashed=False,
                dashboard__workspace__trashed=False,
            )
        except DashboardFilter.DoesNotExist as exc:
            raise DashboardFilterDoesNotExist() from exc

    def get_filters(self, dashboard):
        return DashboardFilter.objects.filter(dashboard=dashboard)

    def create_filter(self, dashboard, **values):
        self.validate_operator(values)
        dashboard_filter = DashboardFilter.objects.create(
            dashboard=dashboard, **extract_allowed(values, self.allowed_fields)
        )
        return dashboard_filter

    def delete_filter(self, dashboard_filter):
        dashboard_filter.delete()

    def filter_available_source_conditions(self, dashboard, conditions):
        """Discard deleted control references sent by a stale source editor."""

        available_filters = set(
            self.get_filters(dashboard).values_list("id", flat=True)
        )
        return [
            condition
            for condition in conditions
            if get_referenced_dashboard_filters(condition["value"]) <= available_filters
        ]

    def remove_source_conditions(self, dashboard_filter):
        """Remove linked conditions, retaining their configuration for trash restore."""

        service_ids = list(
            DashboardDataSource.objects_and_trash.select_for_update()
            .filter(dashboard_id=dashboard_filter.dashboard_id)
            .values_list("service_id", flat=True)
        )
        conditions = [
            condition
            for condition in LocalBaserowTableServiceFilter.objects.filter(
                service_id__in=service_ids
            ).values(
                "id",
                "service_id",
                "field_id",
                "type",
                "value",
                "value_is_formula",
                "order",
                "group_id",
            )
            if dashboard_filter.id
            in get_referenced_dashboard_filters(condition["value"])
        ]
        LocalBaserowTableServiceFilter.objects.filter(
            id__in=[condition["id"] for condition in conditions]
        ).delete()
        saved_conditions = [
            {key: value for key, value in condition.items() if key != "id"}
            for condition in conditions
        ]
        # Another deleted control may already have removed a shared condition.
        # Keep a copy here too so the last restored control can bring it back.
        restoration_data = TrashEntry.objects.filter(
            application_id=dashboard_filter.dashboard_id,
            trash_item_type="dashboard_filter",
        ).values_list("additional_restoration_data", flat=True)
        for data in restoration_data:
            for condition in (data or {}).get("source_conditions", []):
                if (
                    dashboard_filter.id
                    in get_referenced_dashboard_filters(condition["value"])
                    and condition not in saved_conditions
                ):
                    saved_conditions.append(condition)
        return saved_conditions

    def restore_source_conditions(self, dashboard_filter, conditions):
        if not conditions:
            return
        sources = (
            DashboardDataSource.objects_and_trash.select_for_update(of=("self",))
            .filter(
                dashboard_id=dashboard_filter.dashboard_id,
                service_id__in={condition["service_id"] for condition in conditions},
            )
            .select_related("service")
        )
        tables = {
            source.service_id: getattr(source.service.specific, "table_id", None)
            for source in sources
        }
        fields = dict(
            Field.objects_and_trash.filter(
                id__in={condition["field_id"] for condition in conditions}
            ).values_list("id", "table_id")
        )
        groups = dict(
            LocalBaserowTableServiceFilterGroup.objects.filter(
                service_id__in=tables
            ).values_list("id", "service_id")
        )
        available_filters = set(
            self.get_filters(dashboard_filter.dashboard).values_list("id", flat=True)
        )
        for condition in conditions:
            service_id = condition["service_id"]
            if (
                service_id not in tables
                or tables[service_id] is None
                or fields.get(condition["field_id"]) != tables[service_id]
            ):
                continue
            if (
                condition["group_id"] is not None
                and groups.get(condition["group_id"]) != service_id
            ):
                continue
            missing_filters = (
                get_referenced_dashboard_filters(condition["value"]) - available_filters
            )
            if missing_filters:
                # Every other deleted control retains its own copy in the trash.
                continue
            # Preserve edits made since deletion; restore only the removed rows.
            LocalBaserowTableServiceFilter.objects.get_or_create(**condition)

    def update_filter(self, dashboard_filter, **values):
        self.validate_operator(values)
        values = extract_allowed(values, self.allowed_fields)
        previous = {key: getattr(dashboard_filter, key) for key in values}
        for key, value in values.items():
            setattr(dashboard_filter, key, value)
        dashboard_filter.save()
        return previous, values

    def validate_operator(self, values):
        if (
            "operator" in values
            and values["operator"] not in get_text_filter_operators()
        ):
            raise ValueError("The operator is not compatible with text filters.")

    def export_filter(self, dashboard_filter):
        return {
            "id": dashboard_filter.id,
            **{key: getattr(dashboard_filter, key) for key in self.allowed_fields},
        }

    def import_filter(self, dashboard, values, id_mapping):
        dashboard_filter = self.create_filter(
            dashboard, **extract_allowed(values, self.allowed_fields)
        )
        id_mapping.setdefault("dashboard_filters", {})[values["id"]] = (
            dashboard_filter.id
        )
        return dashboard_filter
