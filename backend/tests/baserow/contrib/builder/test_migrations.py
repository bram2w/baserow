import pytest


@pytest.mark.once_per_day_in_ci
def test_0010_remove_orphan_collection_fields_forwards(
    migrator, teardown_table_metadata
):
    migrate_from = [
        ("builder", "0009_element_visibility"),
    ]
    migrate_to = [
        ("builder", "0010_remove_orphan_collection_fields"),
    ]

    old_state = migrator.migrate(migrate_from)

    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    Workspace = old_state.apps.get_model("core", "Workspace")
    Builder = old_state.apps.get_model("builder", "Builder")
    Page = old_state.apps.get_model("builder", "Page")
    TableElement = old_state.apps.get_model("builder", "TableElement")
    CollectionField = old_state.apps.get_model("builder", "CollectionField")

    workspace = Workspace.objects.create(name="Workspace")
    builder = Builder.objects.create(
        order=2,
        name="Builder",
        workspace=workspace,
        content_type=ContentType.objects.get_for_model(Builder),
    )
    page = Page.objects.create(order=2, builder=builder, name="Page", path="page/")
    collection_field1 = CollectionField.objects.create(
        order=1, name="test1", type="text", config={}
    )
    # This orphan collection field should be deleted
    CollectionField.objects.create(order=1, name="test2", type="text", config={})
    table_element = TableElement.objects.create(
        order=1,
        page=page,
        items_per_page=5,
        content_type=ContentType.objects.get_for_model(TableElement),
    )
    table_element.fields.add(collection_field1)

    new_state = migrator.migrate(migrate_to)

    CollectionField = new_state.apps.get_model("builder", "CollectionField")

    assert CollectionField.objects.count() == 1
    assert CollectionField.objects.first().name == "test1"


@pytest.mark.once_per_day_in_ci
def test_0018_resolve_collection_field_configs(migrator, teardown_table_metadata):
    migrate_from = [
        ("builder", "0017_repeatelement"),
    ]
    migrate_to = [
        ("builder", "0018_resolve_collection_field_configs"),
    ]

    old_state = migrator.migrate(migrate_from)

    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    Workspace = old_state.apps.get_model("core", "Workspace")
    Builder = old_state.apps.get_model("builder", "Builder")
    Page = old_state.apps.get_model("builder", "Page")
    TableElement = old_state.apps.get_model("builder", "TableElement")
    CollectionField = old_state.apps.get_model("builder", "CollectionField")

    workspace = Workspace.objects.create(name="Workspace")
    builder = Builder.objects.create(
        order=2,
        name="Builder",
        workspace=workspace,
        content_type=ContentType.objects.get_for_model(Builder),
    )
    page = Page.objects.create(order=2, builder=builder, name="Page", path="page/")

    field_without_target = CollectionField.objects.create(
        order=1,
        name="test1",
        type="link",
        config={
            "link_name": "My link",
            "navigate_to_page_id": 2,
            "navigate_to_url": "",
            "navigation_type": "page",
            "page_parameters": [],
        },
    )

    field_without_page_parameters = CollectionField.objects.create(
        order=2,
        name="test2",
        type="link",
        config={
            "link_name": "badger",
            "navigate_to_page_id": 2,
            "navigate_to_url": "",
            "navigation_type": "page",
            "target": "self",
        },
    )

    table_element = TableElement.objects.create(
        order=1,
        page=page,
        items_per_page=5,
        content_type=ContentType.objects.get_for_model(TableElement),
    )
    table_element.fields.add(field_without_target)
    table_element.fields.add(field_without_page_parameters)

    migrator.migrate(migrate_to)

    field_without_target.refresh_from_db()
    assert field_without_target.config["target"] == "self"

    field_without_page_parameters.refresh_from_db()
    assert field_without_page_parameters.config["page_parameters"] == []
