from django.db import migrations


def add_link_collection_field_variant_property(apps, schema_editor):
    CollectionField = apps.get_model("builder", "collectionfield")
    fields = CollectionField.objects.filter(type="link")
    for field in fields:
        field.config["variant"] = "button"
        field.save()


def remove_link_collection_field_variant_property(apps, schema_editor):
    CollectionField = apps.get_model("builder", "collectionfield")
    fields = CollectionField.objects.filter(type="link")
    for field in fields:
        field.config.pop("variant", None)
        field.save()


class Migration(migrations.Migration):
    dependencies = [
        ("builder", "0035_collection_element_schema_property"),
    ]

    operations = [
        migrations.RunPython(
            add_link_collection_field_variant_property,
            reverse_code=remove_link_collection_field_variant_property,
        ),
    ]
