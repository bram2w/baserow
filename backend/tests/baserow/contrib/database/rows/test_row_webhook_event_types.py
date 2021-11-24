import pytest

from baserow.contrib.database.webhooks.registries import webhook_event_type_registry


@pytest.mark.django_db()
def test_row_created_event_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, primary=True, name="Test 1")

    model = table.get_model()
    row = model.objects.create()
    webhook = data_fixture.create_table_webhook(
        table=table,
        request_method="POST",
        url="http://localhost",
        use_user_field_names=False,
    )
    payload = webhook_event_type_registry.get("row.created").get_payload(
        event_id="1", webhook=webhook, model=model, table=table, row=row
    )
    assert payload == {
        "table_id": table.id,
        "event_id": "1",
        "event_type": "row.created",
        "row_id": row.id,
        "values": {
            "id": 1,
            "order": "1.00000000000000000000",
            f"field_{field.id}": None,
        },
    }

    webhook.use_user_field_names = True
    webhook.save()
    payload = webhook_event_type_registry.get("row.created").get_payload(
        event_id="1", webhook=webhook, model=model, table=table, row=row
    )
    assert payload == {
        "table_id": table.id,
        "event_id": "1",
        "event_type": "row.created",
        "row_id": row.id,
        "values": {
            "id": 1,
            "order": "1.00000000000000000000",
            "Test 1": None,
        },
    }


@pytest.mark.django_db()
def test_row_updated_event_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, primary=True, name="Test 1")

    model = table.get_model()
    row = model.objects.create()
    webhook = data_fixture.create_table_webhook(
        table=table,
        request_method="POST",
        url="http://localhost",
        use_user_field_names=False,
    )
    payload = webhook_event_type_registry.get("row.updated").get_payload(
        event_id="1",
        webhook=webhook,
        model=model,
        table=table,
        row=row,
        before_return=row,
    )
    assert payload == {
        "table_id": table.id,
        "event_id": "1",
        "event_type": "row.updated",
        "row_id": row.id,
        "values": {
            "id": 1,
            "order": "1.00000000000000000000",
            f"field_{field.id}": None,
        },
        "old_values": {
            "id": 1,
            "order": "1.00000000000000000000",
            f"field_{field.id}": None,
        },
    }

    webhook.use_user_field_names = True
    webhook.save()
    payload = webhook_event_type_registry.get("row.updated").get_payload(
        event_id="1",
        webhook=webhook,
        model=model,
        table=table,
        row=row,
        before_return=row,
    )
    assert payload == {
        "table_id": table.id,
        "event_id": "1",
        "event_type": "row.updated",
        "row_id": row.id,
        "values": {
            "id": 1,
            "order": "1.00000000000000000000",
            f"Test 1": None,
        },
        "old_values": {
            "id": 1,
            "order": "1.00000000000000000000",
            f"Test 1": None,
        },
    }


@pytest.mark.django_db()
def test_row_deleted_event_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, primary=True, name="Test 1")

    model = table.get_model()
    row = model.objects.create()
    webhook = data_fixture.create_table_webhook(
        table=table,
        request_method="POST",
        url="http://localhost",
        use_user_field_names=False,
    )
    payload = webhook_event_type_registry.get("row.deleted").get_payload(
        event_id="1",
        webhook=webhook,
        model=model,
        table=table,
        row=row,
    )

    assert payload == {
        "table_id": table.id,
        "event_id": "1",
        "event_type": "row.deleted",
        "row_id": row.id,
    }
