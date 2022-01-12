from django.conf import settings
from rest_framework.exceptions import NotAuthenticated

from baserow.contrib.database.views.exceptions import ViewDoesNotExist
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import view_type_registry
from baserow.ws.registries import PageType

from baserow.core.exceptions import UserNotInGroup
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist


class TablePageType(PageType):
    type = "table"
    parameters = ["table_id"]

    def can_add(self, user, web_socket_id, table_id, **kwargs):
        """
        The user should only have access to this page if the table exists and if he
        has access to the table.
        """

        if not table_id:
            return False

        try:
            handler = TableHandler()
            table = handler.get_table(table_id)
            table.database.group.has_user(user, raise_error=True)
        except (UserNotInGroup, TableDoesNotExist, NotAuthenticated):
            return False

        return True

    def get_group_name(self, table_id, **kwargs):
        return f"table-{table_id}"


class PublicViewPageType(PageType):
    type = "view"
    parameters = ["slug"]

    def can_add(self, user, web_socket_id, slug, **kwargs):
        """
        The user should only have access to this page if the view exists and it is
        public or they have access to the group.
        """

        if settings.DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS:
            return False

        if not slug:
            return False

        try:
            handler = ViewHandler()
            view = handler.get_public_view_by_slug(user, slug)
            view_type = view_type_registry.get_by_model(view.specific_class)
            if not view_type.when_shared_publicly_requires_realtime_events:
                return False
        except ViewDoesNotExist:
            return False

        return True

    def get_group_name(self, slug, **kwargs):
        return f"view-{slug}"

    def broadcast_to_views(self, payload, view_slugs):
        for view_slug in view_slugs:
            self.broadcast(payload, ignore_web_socket_id=None, slug=view_slug)
