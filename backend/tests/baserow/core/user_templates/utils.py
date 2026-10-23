import json
import zipfile
from contextlib import contextmanager
from unittest.mock import patch

from django.contrib.auth.hashers import make_password

from baserow.contrib.automation.nodes.node_types import (
    LocalBaserowFieldsUpdatedTriggerNodeType,
)
from baserow.contrib.builder.elements.models import ChoiceElement
from baserow.contrib.database.fields.models import PasswordField
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.models import ViewDefaultValue
from baserow.contrib.integrations.local_baserow.models import LocalBaserowAggregateRows
from baserow.core.cache import local_cache
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.tasks import run_async_job
from baserow.core.models import TemplateCategory
from baserow.core.storage import get_default_storage
from baserow.core.user_templates.job_types import CreateUserTemplateJobType
from baserow.core.user_templates.models import CreateUserTemplateJob
from baserow.core.user_templates.service import UserTemplateService

ICON = "iconoir-view-grid"

CLEARED_KEYS = {
    "table_id",
    "field_id",
    "view_id",
    "authorized_subject_type",
    "authorized_subject_id",
    "password",
}


def read_archive(archive_name):
    with get_default_storage().open(archive_name, "rb") as archive_file:
        with zipfile.ZipFile(archive_file) as zip_file:
            return {
                name: json.loads(zip_file.read(name))
                for name in zip_file.namelist()
                if name.endswith(".json") and not name.startswith("manifest")
            }


def find_values(data, keys):
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys:
                yield key, value
            yield from find_values(value, keys)
    elif isinstance(data, list):
        for item in data:
            yield from find_values(item, keys)


def start_job(user, workspace, applications, **kwargs):
    kwargs.setdefault("name", "My template")
    kwargs.setdefault("description", "What it does")
    kwargs.setdefault("icon", ICON)
    if "category_ids" not in kwargs:
        kwargs["category_ids"] = [TemplateCategory.objects.create(name="Cat").id]
    return JobHandler().create_and_start_job(
        user,
        CreateUserTemplateJobType.type,
        sync=True,
        workspace_id=workspace.id,
        application_ids=[application.id for application in applications],
        **kwargs,
    )


def create_source(data_fixture):
    """
    A workspace of two members with a database, a builder and an automation, each
    holding something the copy must not carry over.
    """

    user = data_fixture.create_user(email="owner@example.com")
    member = data_fixture.create_user(email="member@example.com")
    workspace = data_fixture.create_workspace(user=user, members=[member])

    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    text_field = data_fixture.create_text_field(table=table, primary=True)
    collaborators_field = data_fixture.create_multiple_collaborators_field(table=table)
    RowHandler().create_row(
        user,
        table,
        values={
            text_field.db_column: "Row",
            collaborators_field.db_column: [{"id": user.id}, {"id": member.id}],
        },
    )
    view = data_fixture.create_grid_view(table=table, name="Shared")
    for owner in [user, member]:
        data_fixture.create_grid_view(
            table=table,
            name=f"Personal of {owner.email}",
            ownership_type="personal",
            owned_by=owner,
        )

    builder = data_fixture.create_builder_application(workspace=workspace)
    page = data_fixture.create_builder_page(builder=builder)
    integration = data_fixture.create_local_baserow_integration(
        application=builder, user=user
    )
    list_rows = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page, integration=integration, table=table, view=view, name="List"
    )
    data_fixture.create_local_baserow_table_service_sort(
        service=list_rows.service, field=text_field, order_by="ASC", order=0
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=list_rows.service, field=text_field, value="Row"
    )
    data_fixture.create_builder_choice_element(
        page=page,
        option_type=ChoiceElement.OPTION_TYPE.FORMULAS,
        formula_value=(
            f"get('data_source_context.{list_rows.id}.{text_field.db_column}.*.value')"
        ),
    )
    data_fixture.create_builder_data_source(
        page=page,
        service_model_class=LocalBaserowAggregateRows,
        integration=integration,
        table=table,
        field=text_field,
        aggregation_type="empty_count",
        name="Aggregate",
    )

    dashboard = data_fixture.create_dashboard_application(workspace=workspace)
    data_fixture.create_dashboard_local_baserow_aggregate_rows_data_source(
        dashboard=dashboard,
        integration_args={"authorized_user": user},
        table=table,
        field=text_field,
        aggregation_type="empty_count",
    )

    automation = data_fixture.create_automation_application(workspace=workspace)
    workflow = data_fixture.create_automation_workflow(
        automation=automation, create_trigger=False
    )
    data_fixture.create_core_http_trigger_node(workflow=workflow)
    data_fixture.create_automation_node(
        workflow=data_fixture.create_automation_workflow(
            automation=automation, create_trigger=False
        ),
        type=LocalBaserowFieldsUpdatedTriggerNodeType.type,
        service=data_fixture.create_local_baserow_fields_updated_service(
            integration=data_fixture.create_local_baserow_integration(
                application=automation, user=user
            ),
            table=table,
            fields=[text_field],
        ),
    )
    data_fixture.create_smtp_integration(
        application=automation, username="smtp-user", password="smtp-secret"
    )

    return {
        "user": user,
        "workspace": workspace,
        "database": database,
        "table": table,
        "text_field": text_field,
        "builder": builder,
        "dashboard": dashboard,
        "automation": automation,
    }


def copied_applications(template):
    return {
        application.get_type().type: application.specific
        for application in template.workspace.application_set.all()
    }


def run_again(job_id):
    # A worker clears the local cache before each task, see `config/celery.py`.
    local_cache.clear()
    run_async_job(job_id)
    return CreateUserTemplateJob.objects.get(id=job_id)


@contextmanager
def another_run_after_the_copy(error=None):
    """
    Runs the latest job again, like a redelivery of its task, right after the
    first run copied its content, and then raises `error` in the first run if
    given. Yields the list the other run is added to.
    """

    copy_applications = UserTemplateService.copy_applications
    calls, other_runs = [], []

    def copy_then_run_again(service, *args, **kwargs):
        content = copy_applications(service, *args, **kwargs)
        calls.append(content)
        if len(calls) == 1:
            other_runs.append(run_again(CreateUserTemplateJob.objects.latest("id").id))
            if error is not None:
                raise error
        return content

    with patch.object(UserTemplateService, "copy_applications", copy_then_run_again):
        yield other_runs


PASSWORD_DEFAULT = "default secret"
NOTE_DEFAULT = "keep me"


def add_password_data(data_fixture, table, view):
    """
    Adds a password field to the table with a hash in every row, and gives the view
    a default value for it and for the primary field.
    """

    password_field = data_fixture.create_password_field(table=table, name="Password")
    password = make_password("source secret")
    table.get_model().objects.update(**{password_field.db_column: password})
    primary_field = table.field_set.get(primary=True)
    ViewDefaultValue.objects.create(
        view=view, field=password_field, value=PASSWORD_DEFAULT, field_type="password"
    )
    ViewDefaultValue.objects.create(
        view=view, field=primary_field, value=NOTE_DEFAULT, field_type="text"
    )
    return password_field, password


def assert_password_data_left_out(table):
    """
    Asserts that the copied table kept its password field, with every cell empty,
    and that no view of it has a default value for that field.
    """

    password_field = table.field_set.get(name="Password").specific
    assert isinstance(password_field, PasswordField)
    values = list(
        table.get_model().objects.values_list(password_field.db_column, flat=True)
    )
    assert values and all(value is None for value in values)
    primary_field = table.field_set.get(primary=True)
    defaults = ViewDefaultValue.objects.filter(view__table=table)
    assert [(default.field_id, default.value) for default in defaults] == [
        (primary_field.id, NOTE_DEFAULT)
    ]


def assert_archive_has_no_password_data(template, password):
    """
    Asserts that the template's archive has no password hash and no default value
    for the copied password field. The archive is exported from the template
    workspace, so its field ids are the ids of the copied fields.
    """

    copied_password_field = (
        copied_applications(template)["database"]
        .table_set.get()
        .field_set.get(name="Password")
    )
    archive = read_archive(template.archive.name)
    for _, default_row_values in find_values(archive, {"default_row_values"}):
        assert all(
            entry["field_id"] != copied_password_field.id
            for entry in default_row_values.values()
        )
    archive_text = json.dumps(archive)
    assert password not in archive_text
    assert PASSWORD_DEFAULT not in archive_text
    assert NOTE_DEFAULT in archive_text
