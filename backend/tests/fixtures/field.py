from baserow.contrib.database.fields.models import TextField, NumberField, BooleanField


class FieldFixtures:
    def create_text_field(self, user=None, **kwargs):
        if 'table' not in kwargs:
            kwargs['table'] = self.create_database_table(user=user)

        if 'name' not in kwargs:
            kwargs['name'] = self.fake.name()

        if 'order' not in kwargs:
            kwargs['order'] = 0

        return TextField.objects.create(**kwargs)

    def create_number_field(self, user=None, **kwargs):
        if 'table' not in kwargs:
            kwargs['table'] = self.create_database_table(user=user)

        if 'name' not in kwargs:
            kwargs['name'] = self.fake.name()

        if 'order' not in kwargs:
            kwargs['order'] = 0

        return NumberField.objects.create(**kwargs)

    def create_boolean_field(self, user=None, **kwargs):
        if 'table' not in kwargs:
            kwargs['table'] = self.create_database_table(user=user)

        if 'name' not in kwargs:
            kwargs['name'] = self.fake.name()

        if 'order' not in kwargs:
            kwargs['order'] = 0

        return BooleanField.objects.create(**kwargs)
