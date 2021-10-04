from django.db import connection

from baserow.contrib.database.fields.models import (
    MultipleSelectField,
    TextField,
    LongTextField,
    NumberField,
    BooleanField,
    DateField,
    LinkRowField,
    FileField,
    SingleSelectField,
    SelectOption,
    URLField,
    EmailField,
    PhoneNumberField,
    LastModifiedField,
    CreatedOnField,
)


class FieldFixtures:
    def create_model_field(self, table, field):
        with connection.schema_editor() as schema_editor:
            to_model = table.get_model(field_ids=[field.id])
            model_field = to_model._meta.get_field(field.db_column)
            schema_editor.add_field(to_model, model_field)

    def create_select_option(self, user=None, **kwargs):
        if "value" not in kwargs:
            kwargs["value"] = self.fake.name()

        if "color" not in kwargs:
            kwargs["color"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        if "field" not in kwargs:
            kwargs["field"] = self.create_single_select_field(user=user)

        return SelectOption.objects.create(**kwargs)

    def create_text_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = TextField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_long_text_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = LongTextField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_number_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = NumberField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_boolean_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = BooleanField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_date_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = DateField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_link_row_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        if "link_row_table" not in kwargs:
            kwargs["link_row_table"] = self.create_database_table(user=user)

        field = LinkRowField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_file_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = FileField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_single_select_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = SingleSelectField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_multiple_select_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = MultipleSelectField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_url_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.url()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = URLField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_email_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.email()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = EmailField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_phone_number_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.phone_number()

        if "order" not in kwargs:
            kwargs["order"] = 0

        field = PhoneNumberField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_last_modified_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        if "date_include_time" not in kwargs:
            kwargs["date_include_time"] = False

        if "timezone" not in kwargs:
            kwargs["timezone"] = "Europe/Berlin"

        field = LastModifiedField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field

    def create_created_on_field(self, user=None, create_field=True, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        if "date_include_time" not in kwargs:
            kwargs["date_include_time"] = False

        if "timezone" not in kwargs:
            kwargs["timezone"] = "Europe/Berlin"

        field = CreatedOnField.objects.create(**kwargs)

        if create_field:
            self.create_model_field(kwargs["table"], field)

        return field
