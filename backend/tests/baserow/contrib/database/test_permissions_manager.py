from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

import pytest

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.operations import ListFieldsOperationType
from baserow.contrib.database.operations import ListTablesDatabaseTableOperationType
from baserow.contrib.database.rows.operations import ReadDatabaseRowOperationType
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, ViewDecoration
from baserow.contrib.database.views.operations import (
    ListAggregationsViewOperationType,
    ListViewDecorationOperationType,
    ListViewsOperationType,
    ReadViewOperationType,
)
from baserow.core.handler import CoreHandler
from baserow.core.types import PermissionCheck


@pytest.mark.django_db
@pytest.mark.django_db
@override_settings(
    PERMISSION_MANAGERS=[
        "core",
        "setting_operation",
        "staff",
        "allow_if_template",
        "member",
        "token",
        "role",
        "basic",
    ]
)
def test_allow_if_template_permission_manager(data_fixture):
    buser = data_fixture.create_user(username="Auth user")

    workspace_0 = data_fixture.create_workspace(user=buser)

    workspace_1 = data_fixture.create_workspace()
    application_1 = data_fixture.create_database_application(workspace=workspace_1)
    table_1, (field_1,), (row_1,) = data_fixture.build_table(
        user=buser,
        database=application_1,
        columns=[
            ("Name", "number"),
        ],
        rows=[
            [1],
        ],
    )
    view_1 = data_fixture.create_grid_view(table=table_1)
    decoration_1 = data_fixture.create_view_decoration(view=view_1)
    ViewHandler().update_field_options(
        view=view_1,
        field_options={
            field_1.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )

    workspace_2 = data_fixture.create_workspace()
    data_fixture.create_template(workspace=workspace_2)
    application_2 = data_fixture.create_database_application(workspace=workspace_2)
    table_2, (field_2,), (row_2,) = data_fixture.build_table(
        user=buser,
        database=application_2,
        columns=[
            ("Name", "number"),
        ],
        rows=[
            [1],
        ],
    )
    view_2 = data_fixture.create_grid_view(table=table_2)
    decoration_2 = data_fixture.create_view_decoration(view=view_2)
    ViewHandler().update_field_options(
        view=view_2,
        field_options={
            field_2.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )

    template = [
        workspace_2,
        application_2,
        table_2,
        field_2,
        row_2,
        view_2,
    ]

    checks = []
    for user in [
        buser,
        AnonymousUser(),
    ]:
        for perm_type, scope in [
            (ListTablesDatabaseTableOperationType.type, application_1),
            (ListFieldsOperationType.type, table_1),
            (ListRowsDatabaseTableOperationType.type, table_1),
            (ListViewsOperationType.type, table_1),
            (ReadDatabaseRowOperationType.type, row_1),
            (ReadViewOperationType.type, view_1),
            (ListViewDecorationOperationType.type, view_1),
            (ListAggregationsViewOperationType.type, view_1),
        ]:
            checks.append(PermissionCheck(user, perm_type, scope))

    result_1 = CoreHandler().check_multiple_permissions(checks, workspace_1)

    list_result_1 = [
        (
            c.actor.username or "Anonymous",
            c.operation_name,
            "template" if c.context in template else "Not a template",
            result_1.get(c, None),
        )
        for c in checks
    ]

    checks = []
    for user in [
        buser,
        AnonymousUser(),
    ]:
        for perm_type, scope in [
            (ListTablesDatabaseTableOperationType.type, application_1),
            (ListFieldsOperationType.type, table_2),
            (ListRowsDatabaseTableOperationType.type, table_2),
            (ListViewsOperationType.type, table_2),
            (ReadDatabaseRowOperationType.type, row_2),
            (ReadViewOperationType.type, view_2),
            (ListViewDecorationOperationType.type, view_2),
            (ListAggregationsViewOperationType.type, view_2),
        ]:
            checks.append(PermissionCheck(user, perm_type, scope))

    result_2 = CoreHandler().check_multiple_permissions(checks, workspace_2)

    list_result_2 = [
        (
            c.actor.username or "Anonymous",
            c.operation_name,
            "template" if c.context in template else "Not a template",
            result_2.get(c, None),
        )
        for c in checks
    ]

    list_result = list_result_1 + list_result_2

    assert list_result == [
        ("Auth user", "database.list_tables", "Not a template", False),
        ("Auth user", "database.table.list_fields", "Not a template", False),
        ("Auth user", "database.table.list_rows", "Not a template", False),
        ("Auth user", "database.table.list_views", "Not a template", False),
        ("Auth user", "database.table.read_row", "Not a template", False),
        ("Auth user", "database.table.view.read", "Not a template", False),
        ("Auth user", "database.table.view.list_decoration", "Not a template", False),
        ("Auth user", "database.table.view.list_aggregations", "Not a template", False),
        ("Anonymous", "database.list_tables", "Not a template", False),
        ("Anonymous", "database.table.list_fields", "Not a template", False),
        ("Anonymous", "database.table.list_rows", "Not a template", False),
        ("Anonymous", "database.table.list_views", "Not a template", False),
        ("Anonymous", "database.table.read_row", "Not a template", False),
        ("Anonymous", "database.table.view.read", "Not a template", False),
        ("Anonymous", "database.table.view.list_decoration", "Not a template", False),
        ("Anonymous", "database.table.view.list_aggregations", "Not a template", False),
        ("Auth user", "database.list_tables", "Not a template", True),
        ("Auth user", "database.table.list_fields", "template", True),
        ("Auth user", "database.table.list_rows", "template", True),
        ("Auth user", "database.table.list_views", "template", True),
        ("Auth user", "database.table.read_row", "template", True),
        ("Auth user", "database.table.view.read", "template", True),
        ("Auth user", "database.table.view.list_decoration", "template", True),
        ("Auth user", "database.table.view.list_aggregations", "template", True),
        ("Anonymous", "database.list_tables", "Not a template", True),
        ("Anonymous", "database.table.list_fields", "template", True),
        ("Anonymous", "database.table.list_rows", "template", True),
        ("Anonymous", "database.table.list_views", "template", True),
        ("Anonymous", "database.table.read_row", "template", True),
        ("Anonymous", "database.table.view.read", "template", True),
        ("Anonymous", "database.table.view.list_decoration", "template", True),
        ("Anonymous", "database.table.view.list_aggregations", "template", True),
    ]


@pytest.mark.django_db
@pytest.mark.django_db
@override_settings(
    PERMISSION_MANAGERS=[
        "core",
        "setting_operation",
        "staff",
        "allow_if_template",
        "member",
        "token",
        "role",
        "basic",
    ]
)
def test_allow_if_template_permission_manager_filter_queryset(data_fixture):
    user = data_fixture.create_user(username="Auth user")

    workspace_0 = data_fixture.create_workspace(user=user)

    workspace_1 = data_fixture.create_workspace()
    application_1 = data_fixture.create_database_application(workspace=workspace_1)
    table_1, (field_1,), (row_1,) = data_fixture.build_table(
        user=user,
        database=application_1,
        columns=[
            ("Name", "number"),
        ],
        rows=[
            [1],
        ],
    )
    view_1 = data_fixture.create_grid_view(table=table_1)
    decoration_1 = data_fixture.create_view_decoration(view=view_1)
    ViewHandler().update_field_options(
        view=view_1,
        field_options={
            field_1.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )

    workspace_2 = data_fixture.create_workspace()
    data_fixture.create_template(workspace=workspace_2)
    application_2 = data_fixture.create_database_application(workspace=workspace_2)
    table_2, (field_2,), (row_2,) = data_fixture.build_table(
        user=user,
        database=application_2,
        columns=[
            ("Name", "number"),
        ],
        rows=[
            [1],
        ],
    )
    view_2 = data_fixture.create_grid_view(table=table_2)
    decoration_2 = data_fixture.create_view_decoration(view=view_2)
    ViewHandler().update_field_options(
        view=view_2,
        field_options={
            field_2.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )

    model_1 = table_1.get_model()
    model_2 = table_2.get_model()

    tests_w1 = [
        (
            ListTablesDatabaseTableOperationType.type,
            Table.objects.filter(database__workspace=workspace_1),
        ),
        (
            ListFieldsOperationType.type,
            Field.objects.filter(table__database__workspace=workspace_1),
        ),
        (
            ListRowsDatabaseTableOperationType.type,
            model_1.objects.all(),
        ),
        (
            ListViewsOperationType.type,
            View.objects.filter(table__database__workspace=workspace_1),
        ),
        (
            ListViewDecorationOperationType.type,
            ViewDecoration.objects.filter(view__table__database__workspace=workspace_1),
        ),
    ]

    for operation_name, queryset in tests_w1:
        assert (
            sorted(
                [
                    a.id
                    for a in CoreHandler().filter_queryset(
                        user,
                        operation_name,
                        queryset,
                        workspace=workspace_1,
                    )
                ]
            )
            == []
        )

    tests_w1 = [
        (
            ListTablesDatabaseTableOperationType.type,
            Table.objects.filter(database__workspace=workspace_2),
            [table_2.id],
        ),
        (
            ListFieldsOperationType.type,
            Field.objects.filter(table__database__workspace=workspace_2),
            [field_2.id],
        ),
        (ListRowsDatabaseTableOperationType.type, model_2.objects.all(), [row_2.id]),
        (
            ListViewsOperationType.type,
            View.objects.filter(table__database__workspace=workspace_2),
            [view_2.id],
        ),
        (
            ListViewDecorationOperationType.type,
            ViewDecoration.objects.filter(view__table__database__workspace=workspace_2),
            [decoration_2.id],
        ),
    ]

    for operation_name, queryset, expected in tests_w1:
        assert (
            sorted(
                [
                    a.id
                    for a in CoreHandler().filter_queryset(
                        user,
                        operation_name,
                        queryset,
                        workspace=workspace_2,
                    )
                ]
            )
            == expected
        ), operation_name
