from django.db.models import F, TextField
from django.db.models.functions import Cast, Collate

from baserow.contrib.database.fields.models import Field
from baserow.core.utils import extract_allowed

from .exceptions import DashboardFilterDoesNotExist
from .field_types import text_field_expression
from .models import DashboardFilter, DashboardFilterBinding


class DashboardFilterHandler:
    allowed_fields = ("label", "type", "operator", "mode", "multiple")

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
        return DashboardFilter.objects.filter(dashboard=dashboard).prefetch_related(
            "bindings"
        )

    def create_filter(self, dashboard, **values):
        dashboard_filter = DashboardFilter.objects.create(
            dashboard=dashboard, **extract_allowed(values, self.allowed_fields)
        )
        if "bindings" in values:
            self.update_bindings(dashboard_filter, values["bindings"])
        return dashboard_filter

    def delete_filter(self, dashboard_filter):
        dashboard_filter.delete()

    def update_filter(self, dashboard_filter, **values):
        bindings = values.get("bindings")
        values = extract_allowed(values, self.allowed_fields)
        previous = {key: getattr(dashboard_filter, key) for key in values}
        for key, value in values.items():
            setattr(dashboard_filter, key, value)
        dashboard_filter.save()
        if bindings is not None:
            previous["bindings"] = list(
                dashboard_filter.bindings.values("widget_id", "field_id")
            )
            values["bindings"] = bindings
            self.update_bindings(dashboard_filter, bindings)
        return previous, values

    def update_bindings(self, dashboard_filter, bindings):
        dashboard_filter.bindings.all().delete()
        DashboardFilterBinding.objects.bulk_create(
            [
                DashboardFilterBinding(filter=dashboard_filter, **binding)
                for binding in bindings
            ]
        )

    def export_filter(self, dashboard_filter):
        return {
            "id": dashboard_filter.id,
            **{key: getattr(dashboard_filter, key) for key in self.allowed_fields},
            "bindings": list(
                dashboard_filter.bindings.filter(widget__trashed=False).values(
                    "widget_id", "field_id"
                )
            ),
        }

    def import_filter(self, dashboard, values, id_mapping):
        bindings = []
        for binding in values.get("bindings", []):
            field_id = binding["field_id"]
            if "database_fields" in id_mapping:
                field_id = id_mapping["database_fields"].get(field_id)
            if field_id and not Field.objects_and_trash.filter(id=field_id).exists():
                field_id = None
            bindings.append(
                {
                    "widget_id": id_mapping["dashboard_widgets"][binding["widget_id"]],
                    "field_id": field_id,
                }
            )
        dashboard_filter = self.create_filter(
            dashboard, **extract_allowed(values, self.allowed_fields), bindings=bindings
        )
        id_mapping.setdefault("dashboard_filters", {})[values["id"]] = (
            dashboard_filter.id
        )
        return dashboard_filter

    def get_options(self, querysets, *, search="", after=None, limit=50, selected=None):
        """Union options from authorized source querysets, independently of selections."""
        choices, available = [], []
        for queryset, field in querysets:
            queryset = (
                queryset.annotate(
                    dashboard_option_text=Cast(
                        text_field_expression(field), TextField()
                    ),
                )
                .annotate(dashboard_option=Collate(F("dashboard_option_text"), "C"))
                .exclude(dashboard_option__isnull=True)
                .exclude(dashboard_option__regex=r"^\s*$")
                .order_by()
            )
            if selected:
                available.append(
                    queryset.filter(dashboard_option__in=selected)
                    .values_list("dashboard_option", flat=True)
                    .distinct()
                )
            if search:
                queryset = queryset.filter(dashboard_option_text__icontains=search)
            if after is not None:
                queryset = queryset.filter(dashboard_option__gt=after)
            choices.append(
                queryset.values_list("dashboard_option", flat=True).distinct()
            )

        results = (
            list(
                choices[0].union(*choices[1:]).order_by("dashboard_option")[: limit + 1]
            )
            if choices
            else []
        )
        selected_available = (
            list(available[0].union(*available[1:]).order_by("dashboard_option"))
            if available
            else []
        )
        return {
            "results": results[:limit],
            "next": results[limit - 1] if len(results) > limit else None,
            "available": selected_available,
        }
