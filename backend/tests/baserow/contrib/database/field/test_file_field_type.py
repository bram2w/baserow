import pytest
import json
from io import BytesIO

from zipfile import ZipFile, ZIP_DEFLATED

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from baserow.core.handler import CoreHandler
from baserow.core.user_files.models import UserFile
from baserow.core.user_files.exceptions import (
    InvalidUserFileNameError,
    UserFileDoesNotExist,
)
from baserow.core.user_files.handler import UserFileHandler
from baserow.contrib.database.fields.models import FileField
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_file_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    user_file_1 = data_fixture.create_user_file()
    user_file_2 = data_fixture.create_user_file()
    user_file_3 = data_fixture.create_user_file()

    field_handler = FieldHandler()
    row_handler = RowHandler()

    file = field_handler.create_field(
        user=user, table=table, type_name="file", name="File"
    )

    assert FileField.objects.all().count() == 1
    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user, table=table, values={"file": "not_a_json"}, model=model
        )

    with pytest.raises(ValidationError):
        row_handler.create_row(user=user, table=table, values={"file": {}}, model=model)

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user, table=table, values={"file": [{"no_name": "test"}]}, model=model
        )

    with pytest.raises(InvalidUserFileNameError):
        row_handler.create_row(
            user=user,
            table=table,
            values={"file": [{"name": "wrongfilename.jpg"}]},
            model=model,
        )

    with pytest.raises(UserFileDoesNotExist):
        row_handler.create_row(
            user=user,
            table=table,
            values={"file": [{"name": "file_name.jpg"}]},
            model=model,
        )

    row = row_handler.create_row(
        user=user,
        table=table,
        values={"file": [{"name": user_file_1.name}]},
        model=model,
    )
    assert row.file[0]["visible_name"] == user_file_1.original_name
    del row.file[0]["visible_name"]
    assert row.file[0] == user_file_1.serialize()

    row = row_handler.create_row(
        user=user,
        table=table,
        values={
            "file": [
                {"name": user_file_2.name},
                {"name": user_file_1.name},
                {"name": user_file_1.name},
            ]
        },
        model=model,
    )
    assert row.file[0]["visible_name"] == user_file_2.original_name
    assert row.file[1]["visible_name"] == user_file_1.original_name
    assert row.file[2]["visible_name"] == user_file_1.original_name
    del row.file[0]["visible_name"]
    del row.file[1]["visible_name"]
    del row.file[2]["visible_name"]
    assert row.file[0] == user_file_2.serialize()
    assert row.file[1] == user_file_1.serialize()
    assert row.file[2] == user_file_1.serialize()

    row = row_handler.create_row(
        user=user,
        table=table,
        values={
            "file": [
                {"name": user_file_1.name},
                {"name": user_file_3.name},
                {"name": user_file_2.name},
            ]
        },
        model=model,
    )
    assert row.file[0]["visible_name"] == user_file_1.original_name
    assert row.file[1]["visible_name"] == user_file_3.original_name
    assert row.file[2]["visible_name"] == user_file_2.original_name
    del row.file[0]["visible_name"]
    del row.file[1]["visible_name"]
    del row.file[2]["visible_name"]
    assert row.file[0] == user_file_1.serialize()
    assert row.file[1] == user_file_3.serialize()
    assert row.file[2] == user_file_2.serialize()

    row = row_handler.update_row(
        user=user,
        table=table,
        row_id=row.id,
        values={
            "file": [
                {"name": user_file_1.name, "visible_name": "not_original.jpg"},
            ]
        },
        model=model,
    )
    assert row.file[0]["visible_name"] == "not_original.jpg"
    del row.file[0]["visible_name"]
    assert row.file[0] == user_file_1.serialize()

    assert model.objects.all().count() == 3
    field_handler.delete_field(user=user, field=file)
    assert FileField.objects.all().count() == 0
    model.objects.all().delete()

    text = field_handler.create_field(
        user=user, table=table, type_name="text", name="Text"
    )
    model = table.get_model(attribute_names=True)

    row = row_handler.create_row(
        user=user, table=table, values={"text": "Some random text"}, model=model
    )
    row_handler.create_row(
        user=user, table=table, values={"text": '["Not compatible"]'}, model=model
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"text": json.dumps(user_file_1.serialize())},
        model=model,
    )

    file = field_handler.update_field(
        user=user, table=table, field=text, new_type_name="file", name="File"
    )
    model = table.get_model(attribute_names=True)
    results = model.objects.all()
    assert results[0].file == []
    assert results[1].file == []
    assert results[2].file == []

    row_handler.update_row(
        user=user,
        table=table,
        row_id=row.id,
        values={
            "file": [
                {"name": user_file_1.name, "visible_name": "not_original.jpg"},
            ]
        },
        model=model,
    )

    field_handler.update_field(
        user=user, table=table, field=file, new_type_name="text", name="text"
    )
    model = table.get_model(attribute_names=True)
    results = model.objects.all()
    assert results[0].text is None
    assert results[1].text is None
    assert results[2].text is None


@pytest.mark.django_db
def test_import_export_file_field(data_fixture, tmpdir):
    user = data_fixture.create_user()
    imported_group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_file_field(table=table, name="File")

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    handler = UserFileHandler()
    user_file = handler.upload_user_file(
        user, "test.txt", ContentFile(b"Hello World"), storage=storage
    )

    core_handler = CoreHandler()
    row_handler = RowHandler()
    model = table.get_model()

    row_1 = row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{field.id}": [{"name": user_file.name, "visible_name": "a.txt"}]
        },
        model=model,
    )
    row_2 = row_handler.create_row(
        user=user,
        table=table,
        values={},
        model=model,
    )
    row_3 = row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{field.id}": [{"name": user_file.name}]},
        model=model,
    )

    files_buffer = BytesIO()
    exported_applications = core_handler.export_group_applications(
        database.group, files_buffer=files_buffer, storage=storage
    )

    # We expect that the exported zip file contains the user file used in the created
    # rows.
    with ZipFile(files_buffer, "r", ZIP_DEFLATED, False) as zip_file:
        assert zip_file.read(user_file.name) == b"Hello World"

    assert (
        exported_applications[0]["tables"][0]["rows"][0][f"field_{field.id}"][0]["name"]
        == user_file.name
    )
    assert (
        exported_applications[0]["tables"][0]["rows"][0][f"field_{field.id}"][0][
            "original_name"
        ]
        == user_file.original_name
    )
    assert exported_applications[0]["tables"][0]["rows"][1][f"field_{field.id}"] == []
    assert (
        exported_applications[0]["tables"][0]["rows"][2][f"field_{field.id}"][0]["name"]
        == user_file.name
    )

    # Change the original name for enforce that the file is re-uploaded when saved.
    exported_applications[0]["tables"][0]["rows"][0][f"field_{field.id}"][0][
        "original_name"
    ] = "test2.txt"
    exported_applications[0]["tables"][0]["rows"][2][f"field_{field.id}"][0][
        "original_name"
    ] = "test2.txt"

    imported_applications, id_mapping = core_handler.import_applications_to_group(
        imported_group, exported_applications, files_buffer, storage
    )
    imported_database = imported_applications[0]
    imported_tables = imported_database.table_set.all()
    imported_table = imported_tables[0]
    imported_field = imported_table.field_set.all().first().specific
    imported_user_file = UserFile.objects.all()[1]

    import_row_1 = row_handler.get_row(user=user, table=imported_table, row_id=row_1.id)
    import_row_2 = row_handler.get_row(user=user, table=imported_table, row_id=row_2.id)
    import_row_3 = row_handler.get_row(user=user, table=imported_table, row_id=row_3.id)

    assert len(getattr(import_row_1, f"field_{imported_field.id}")) == 1
    assert (
        getattr(import_row_1, f"field_{imported_field.id}")[0]["name"]
        == imported_user_file.name
    )
    assert (
        getattr(import_row_1, f"field_{imported_field.id}")[0]["visible_name"]
        == "a.txt"
    )
    assert len(getattr(import_row_2, f"field_{imported_field.id}")) == 0
    assert len(getattr(import_row_3, f"field_{imported_field.id}")) == 1
    assert (
        getattr(import_row_3, f"field_{imported_field.id}")[0]["name"]
        == imported_user_file.name
    )
    assert (
        getattr(import_row_3, f"field_{imported_field.id}")[0]["visible_name"]
        == "test.txt"
    )

    assert UserFile.objects.all().count() == 2
    assert user_file.name != imported_user_file.name
    file_path = tmpdir.join("user_files", imported_user_file.name)
    assert file_path.isfile()
    assert file_path.open().read() == "Hello World"
