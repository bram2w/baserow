from io import BytesIO

import pytest

from baserow.contrib.builder.workflow_actions.models import (
    CoreHTTPRequestWorkflowAction,
    EventTypes,
)
from baserow.core.handler import CoreHandler
from baserow.core.registries import ImportExportConfig


@pytest.mark.django_db
@pytest.mark.parametrize("exclude_sensitive_data", [True, False])
def test_workspace_roundtrip_keeps_http_request_keys(
    data_fixture, exclude_sensitive_data
):
    """Workspace copies preserve request keys while honoring value redaction."""

    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    button = data_fixture.create_builder_button_element(page=page)
    service = data_fixture.create_core_http_request_service(
        integration=None, body_type="raw", body_content="'body-secret'"
    )
    request_rows = {
        "headers": [("Authorization", "'header-secret'"), ("api-version", "'1'")],
        "query_params": [("api_key", "'query-secret'")],
        "form_data": [("token", "'form-secret'")],
    }
    for prop_name, rows in request_rows.items():
        for key, formula in rows:
            getattr(service, prop_name).create(key=key, value=formula)
    data_fixture.create_core_http_request_workflow_action(
        page=page, element=button, event=EventTypes.CLICK, service=service
    )
    config = ImportExportConfig(
        include_permission_data=False, exclude_sensitive_data=exclude_sensitive_data
    )
    exported = CoreHandler().export_workspace_applications(
        page.builder.workspace, BytesIO(), config
    )
    exported_page = next(p for p in exported[0]["pages"] if p["id"] == page.id)
    exported_service = exported_page["workflow_actions"][0]["service"]
    for prop_name, rows in request_rows.items():
        if exclude_sensitive_data:
            assert exported_service[prop_name] == [
                {"key": key, "value": None} for key, _ in rows
            ]
        else:
            assert [
                (row["key"], row["value"]["formula"])
                for row in exported_service[prop_name]
            ] == rows
    if exclude_sensitive_data:
        assert exported_service["body_content"] is None

    applications, _ = CoreHandler().import_applications_to_workspace(
        data_fixture.create_workspace(user=user), exported, BytesIO(), config, None
    )
    imported_service = CoreHTTPRequestWorkflowAction.objects.get(
        page__builder=applications[0]
    ).service.specific
    assert imported_service.id != service.id
    for prop_name, rows in request_rows.items():
        assert [
            (row.key, row.value.get("formula"))
            for row in getattr(imported_service, prop_name).order_by("id")
        ] == [(key, "" if exclude_sensitive_data else formula) for key, formula in rows]
        assert [
            (row.key, row.value["formula"])
            for row in getattr(service, prop_name).order_by("id")
        ] == rows
    assert imported_service.body_content.get("formula") == (
        "" if exclude_sensitive_data else "'body-secret'"
    )
