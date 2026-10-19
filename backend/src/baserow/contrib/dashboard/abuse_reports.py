from urllib.parse import urljoin

from django.conf import settings

from rest_framework.request import Request

from baserow.contrib.dashboard.api.errors import (
    ERROR_DASHBOARD_DOES_NOT_EXIST,
    ERROR_NO_AUTHORIZATION_TO_PUBLIC_DASHBOARD,
)
from baserow.contrib.dashboard.api.public.utils import (
    get_public_dashboard_authorization_token,
)
from baserow.contrib.dashboard.exceptions import (
    DashboardDoesNotExist,
    NoAuthorizationToPublicDashboard,
)
from baserow.contrib.dashboard.handler import DashboardHandler
from baserow.contrib.dashboard.models import Dashboard
from baserow.core.abuse_reports.registries import (
    AbuseReportResourceType,
    ReportedResource,
)


class DashboardAbuseReportResourceType(AbuseReportResourceType):
    """
    Lets the visitors of a publicly shared dashboard report it for abuse.
    """

    type = "dashboard"
    api_exceptions_map = {
        DashboardDoesNotExist: ERROR_DASHBOARD_DOES_NOT_EXIST,
        NoAuthorizationToPublicDashboard: ERROR_NO_AUTHORIZATION_TO_PUBLIC_DASHBOARD,
    }

    def resolve(self, request: Request, identifier: str) -> ReportedResource:
        dashboard = DashboardHandler().get_public_dashboard_by_slug(
            request.user,
            identifier,
            authorization_token=get_public_dashboard_authorization_token(request),
        )
        # `get_public_dashboard_by_slug` also returns private dashboards to
        # workspace members who can read them, but only publicly shared dashboards
        # can be reported.
        if not dashboard.public:
            raise DashboardDoesNotExist("The dashboard is not publicly shared.")
        return ReportedResource(
            resource_id=dashboard.id,
            name=dashboard.name,
            workspace=dashboard.workspace,
            public_url=self._get_public_url(dashboard),
        )

    def _get_public_url(self, dashboard: Dashboard) -> str:
        return urljoin(
            settings.BASEROW_EMBEDDED_SHARE_URL, f"/public/dashboard/{dashboard.slug}"
        )
