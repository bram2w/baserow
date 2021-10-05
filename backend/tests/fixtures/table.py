from django.db import connection

from baserow.contrib.database.table.models import Table


class TableFixtures:
    def create_database_table(self, user=None, create_table=True, **kwargs):
        if "database" not in kwargs:
            kwargs["database"] = self.create_database_application(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        table = Table.objects.create(**kwargs)

        if create_table:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(table.get_model())

        return table

    def build_table(self, columns, rows, user=None, **kwargs):
        table = self.create_database_table(user=user, create_table=True, **kwargs)
        fields = []
        for name, field_type in columns:
            kwargs = {}
            if isinstance(field_type, dict):
                kwargs = field_type
                field_type = kwargs.pop("type")
            fields.append(
                getattr(self, f"create_{field_type}_field")(
                    name=name, table=table, **kwargs
                )
            )

        model = table.get_model()

        created_rows = []
        for row in rows:
            kwargs = {}
            i = 0
            for field in fields:
                kwargs[f"field_{field.id}"] = row[i]
                i += 1
            created_rows.append(model.objects.create(**kwargs))

        return table, fields, created_rows
