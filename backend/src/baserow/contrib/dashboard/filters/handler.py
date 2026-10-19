from baserow.core.utils import extract_allowed

from .exceptions import DashboardFilterDoesNotExist
from .models import DashboardFilter


class DashboardFilterHandler:
    allowed_fields = ("label", "type", "operator", "mode", "multiple")

    def get_filter(self, filter_id, for_update=False):
        queryset = DashboardFilter.objects.select_related("dashboard__workspace")
        if for_update:
            queryset = queryset.select_for_update(of=("self",))
        try:
            return queryset.get(id=filter_id, dashboard__trashed=False)
        except DashboardFilter.DoesNotExist as exc:
            raise DashboardFilterDoesNotExist() from exc

    def get_filters(self, dashboard):
        return DashboardFilter.objects.filter(dashboard=dashboard)

    def create_filter(self, dashboard, **values):
        return DashboardFilter.objects.create(
            dashboard=dashboard, **extract_allowed(values, self.allowed_fields)
        )

    def delete_filter(self, dashboard_filter):
        dashboard_filter.delete()

    def update_filter(self, dashboard_filter, **values):
        values = extract_allowed(values, self.allowed_fields)
        previous = {key: getattr(dashboard_filter, key) for key in values}
        for key, value in values.items():
            setattr(dashboard_filter, key, value)
        dashboard_filter.save()
        return previous, values
