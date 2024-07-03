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
# You must add --run-once-per-day-in-ci to execute this test
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


@pytest.mark.once_per_day_in_ci
# You must add --run-once-per-day-in-ci to execute this test
def test_0025_theme_config_block(migrator, teardown_table_metadata):
    migrate_from = [
        ("builder", "0024_element_role_type_element_roles"),
    ]
    migrate_to = [
        ("builder", "0025_buttonthemeconfigblock_colorthemeconfigblock_and_more"),
    ]

    old_state = migrator.migrate(migrate_from)

    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    Workspace = old_state.apps.get_model("core", "Workspace")
    Builder = old_state.apps.get_model("builder", "Builder")

    workspace = Workspace.objects.create(name="Workspace")
    builder = Builder.objects.create(
        order=2,
        name="Builder",
        workspace=workspace,
        content_type=ContentType.objects.get_for_model(Builder),
    )

    builder.mainthemeconfigblock.primary_color = "#f00000ff"
    builder.mainthemeconfigblock.secondary_color = "#0eaa42ff"
    builder.mainthemeconfigblock.heading_1_font_size = "#0eaa42ff"
    builder.mainthemeconfigblock.heading_1_font_size = 30
    builder.mainthemeconfigblock.heading_1_color = "#ff0000ff"
    builder.mainthemeconfigblock.heading_2_font_size = 20
    builder.mainthemeconfigblock.heading_2_color = "#070810ff"
    builder.mainthemeconfigblock.heading_3_font_size = 16
    builder.mainthemeconfigblock.heading_3_color = "#070810ff"

    builder.mainthemeconfigblock.save()

    new_state = migrator.migrate(migrate_to)

    Builder = new_state.apps.get_model("builder", "Builder")
    builder = Builder.objects.first()

    assert builder.colorthemeconfigblock.primary_color == "#f00000ff"
    assert builder.colorthemeconfigblock.secondary_color == "#0eaa42ff"
    assert builder.typographythemeconfigblock.heading_1_font_size == 30
    assert builder.typographythemeconfigblock.heading_1_text_color == "#ff0000ff"
    assert builder.typographythemeconfigblock.heading_2_font_size == 20
    assert builder.typographythemeconfigblock.heading_2_text_color == "#070810ff"
    assert builder.typographythemeconfigblock.heading_3_font_size == 16
    assert builder.typographythemeconfigblock.heading_3_text_color == "#070810ff"
    assert builder.buttonthemeconfigblock.button_background_color == "primary"


@pytest.mark.once_per_day_in_ci
# You must add --run-once-per-day-in-ci to execute this test
def test_0025_element_properties(migrator, teardown_table_metadata):
    migrate_from = [
        ("builder", "0024_element_role_type_element_roles"),
    ]
    migrate_to = [
        ("builder", "0025_buttonthemeconfigblock_colorthemeconfigblock_and_more"),
    ]

    old_state = migrator.migrate(migrate_from)

    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    Workspace = old_state.apps.get_model("core", "Workspace")
    Builder = old_state.apps.get_model("builder", "Builder")
    Page = old_state.apps.get_model("builder", "Page")

    TableElement = old_state.apps.get_model("builder", "TableElement")
    HeadingElement = old_state.apps.get_model("builder", "HeadingElement")
    ButtonElement = old_state.apps.get_model("builder", "ButtonElement")
    LinkElement = old_state.apps.get_model("builder", "LinkElement")
    FormContainerElement = old_state.apps.get_model("builder", "FormContainerElement")

    workspace = Workspace.objects.create(name="Workspace")
    builder = Builder.objects.create(
        order=2,
        name="Builder",
        workspace=workspace,
        content_type=ContentType.objects.get_for_model(Builder),
    )
    page = Page.objects.create(order=2, builder=builder, name="Page", path="page/")

    TableElement.objects.create(
        order=1,
        page=page,
        items_per_page=5,
        content_type=ContentType.objects.get_for_model(TableElement),
        button_color="#CCCCCCCC",
    )
    ButtonElement.objects.create(
        order=2,
        page=page,
        button_color="#CC00CCCC",
        content_type=ContentType.objects.get_for_model(ButtonElement),
    )
    LinkElement.objects.create(
        order=2,
        page=page,
        button_color="#CCCC00CC",
        content_type=ContentType.objects.get_for_model(LinkElement),
    )
    FormContainerElement.objects.create(
        order=2,
        page=page,
        button_color="#CCCCCC00",
        content_type=ContentType.objects.get_for_model(FormContainerElement),
    )
    HeadingElement.objects.create(
        order=2,
        page=page,
        font_color="#0000CCCC",
        content_type=ContentType.objects.get_for_model(HeadingElement),
    )

    new_state = migrator.migrate(migrate_to)

    ButtonElement = new_state.apps.get_model("builder", "ButtonElement")
    HeadingElement = new_state.apps.get_model("builder", "HeadingElement")
    LinkElement = new_state.apps.get_model("builder", "LinkElement")
    FormContainerElement = new_state.apps.get_model("builder", "FormContainerElement")
    TableElement = new_state.apps.get_model("builder", "TableElement")

    heading = HeadingElement.objects.first()
    button = ButtonElement.objects.first()
    link = LinkElement.objects.first()
    form = FormContainerElement.objects.first()
    table = TableElement.objects.first()

    assert table.styles == {
        "button": {
            "button_background_color": "#CCCCCCCC",
            "button_hover_background_color": "#dbdbdbcc",
        }
    }
    assert button.styles == {
        "button": {
            "button_background_color": "#CC00CCCC",
            "button_hover_background_color": "#db4cdbcc",
        }
    }
    assert link.styles == {
        "button": {
            "button_background_color": "#CCCC00CC",
            "button_hover_background_color": "#dbdb4ccc",
        }
    }
    assert form.styles == {
        "button": {
            "button_background_color": "#CCCCCC00",
            "button_hover_background_color": "#dbdbdb00",
        }
    }
    assert heading.styles == {
        "typography": {
            "heading_1_text_color": "#0000CCCC",
        }
    }
