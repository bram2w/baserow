import abc
from typing import Generic, List, Optional, TypeVar

from django.contrib.auth.models import AbstractUser

import pytest

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import GalleryView, GridView, View
from baserow.contrib.database.views.registries import view_type_registry

T = TypeVar("T", bound=View)


class PublicWebsocketTester(Generic[T], abc.ABC):
    def __init__(self, data_fixture):
        self.data_fixture = data_fixture

    @property
    @abc.abstractmethod
    def newly_created_field_visible_by_default(self):
        pass

    @abc.abstractmethod
    def create_public_view(
        self,
        user: AbstractUser,
        table: Table,
        visible_fields: Optional[List[Field]] = None,
        hidden_fields: Optional[List[Field]] = None,
        **kwargs,
    ) -> T:
        pass

    def create_other_views_that_should_not_get_realtime_signals(
        self, user: AbstractUser, table: Table, mock_broadcast_to_channel_group
    ):
        for view_type in view_type_registry.get_all():
            ViewHandler().create_view(user, table, view_type.type, public=False)
            if not view_type.when_shared_publicly_requires_realtime_events:
                ViewHandler().create_view(user, table, view_type.type, public=True)
        # Reset away all the signals we just triggered by creating these other
        # views.
        mock_broadcast_to_channel_group.reset_mock()


class GridViewPublicWebsocketTester(PublicWebsocketTester[GridView]):
    newly_created_field_visible_by_default = False

    def create_public_view(
        self,
        user: AbstractUser,
        table: Table,
        visible_fields: Optional[List[Field]] = None,
        hidden_fields: Optional[List[Field]] = None,
        **kwargs,
    ) -> GridView:
        view = self.data_fixture.create_grid_view(
            user,
            table=table,
            public=True,
            create_options=False,
            **kwargs,
        )
        for f in visible_fields or []:
            self.data_fixture.create_grid_view_field_option(view, f, hidden=False)

        # In a shared grid view all fields are hidden by default when they don't have a
        # grid view option so no need make explicit options for the hidden_fields list.

        return view


class GalleryViewPublicWebsocketTester(PublicWebsocketTester[GalleryView]):
    newly_created_field_visible_by_default = False

    def create_public_view(
        self,
        user: AbstractUser,
        table: Table,
        visible_fields: Optional[List[Field]] = None,
        hidden_fields: Optional[List[Field]] = None,
        **kwargs,
    ) -> GalleryView:
        view = self.data_fixture.create_gallery_view(
            user, table=table, public=True, create_options=False, **kwargs
        )
        for f in visible_fields or []:
            self.data_fixture.create_gallery_view_field_option(view, f, hidden=False)

        # In a gallery view all fields are hidden by default when they don't have a
        # grid view option so no need make explicit options for the hidden_fields list.

        return view


@pytest.fixture(
    params=[
        t.type
        for t in view_type_registry.get_all()
        # premium view types must not be tested here.
        if t.when_shared_publicly_requires_realtime_events
        and t.type not in ["kanban", "calendar", "timeline"]
        and t.can_share
    ]
)
def public_realtime_view_tester(request, data_fixture):
    """
    A fixture used by the public websocket test suite.

    It is parameterized so every test that imports this fixture will get run N times,
    once per view_type which has when_shared_publicly_requires_realtime_events=True.

    It will return an instance of the PublicWebsocketTester interface which then
    can be used to test any generic view that can be publicly shared with realtime
    socket events.

    If you add a new view type which requires the special public view realtime events
    then you should implement a specific instance of PublicWebsocketTester and make
    sure it is returned from this function in the if below.
    """

    if request.param == "grid":
        return GridViewPublicWebsocketTester(data_fixture)
    elif request.param == "gallery":
        if request.node.get_closest_marker("once_per_day_in_ci"):
            return GalleryViewPublicWebsocketTester(data_fixture)
        else:
            pytest.skip("Skipping tests without the once_per_day_in_ci marker.")
    else:
        raise Exception(
            "You need to implement the `ViewTester` class and add a clause "
            "in this test fixture to return it for your new view type. "
            "This will allow you to test its public WebSocket signals."
        )
