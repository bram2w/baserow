from django.db import models

from baserow.core.mixins import OrderableMixin
from baserow.core.utils import to_pascal_case, remove_special_characters
from baserow.contrib.database.config import DatabaseConfig
from baserow.contrib.database.fields.registries import field_type_registry


class Table(OrderableMixin, models.Model):
    database = models.ForeignKey('database.Database', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, database):
        queryset = Table.objects.filter(database=database)
        return cls.get_highest_order_of_queryset(queryset) + 1

    @property
    def model_class_name(self):
        """
        Generates a pascal case based class name based on the table name.

        :return: The generated model class name.
        :rtype: str
        """

        name = remove_special_characters(self.name, False)
        name = to_pascal_case(name)

        if name[0].isnumeric():
            name = f'Table{name}'

        return name

    def get_model(self, fields=None, field_ids=None, attribute_names=False):
        """
        Generates a django model based on available fields that belong to this table.

        :param fields: Extra table field instances that need to be added the model.
        :type fields: list
        :param field_ids: If provided only the fields with the ids in the list will be
            added to the model. This can be done to improve speed if for example only a
            single field needs to be mutated.
        :type field_ids: None or list
        :param attribute_names: If True, the the model attributes will be based on the
            field name instead of the field id.
        :type attribute_names: bool
        :return: The generated model.
        :rtype: Model
        """

        if not fields:
            fields = []

        app_label = f'{DatabaseConfig.name}_tables'
        meta = type('Meta', (), {
            'managed': False,
            'db_table': f'database_table_{self.id}',
            'app_label': app_label
        })

        attrs = {
            'Meta': meta,
            '__module__': 'database.models',
            # An indication that the model is a generated table model.
            '_generated_table_model': True,
            # An object containing the table fields, field types and the chosen names
            # with the table field id as key.
            '_field_objects': {}
        }

        # Construct a query to fetch all the fields of that table.
        fields_query = self.field_set.all()

        # If the field ids are provided we must only fetch the fields of which the ids
        # are in that list.
        if isinstance(field_ids, list):
            if len(field_ids) == 0:
                fields_query = []
            else:
                fields_query = fields_query.filter(pk__in=field_ids)

        # Create a combined list of fields that must be added and belong to the this
        # table.
        fields = fields + [field for field in fields_query]

        # If there are duplicate field names we have to store them in a list so we know
        # later which ones are duplicate.
        duplicate_field_names = []

        # We will have to add each field to with the correct field name and model field
        # to the attribute list in order for the model to work.
        for field in fields:
            field = field.specific
            field_type = field_type_registry.get_by_model(field)
            field_name = field.db_column
            # If attribute_names is True we will not use 'field_{id}' as attribute name,
            # but we will rather use a name the user provided.
            if attribute_names:
                field_name = field.model_attribute_name
                # If the field name already exists we will append '_field_{id}' to each
                # entry that is a duplicate.
                if field_name in attrs:
                    duplicate_field_names.append(field_name)
                    replaced_field_name = f'{field_name}_{attrs[field_name].db_column}'
                    attrs[replaced_field_name] = attrs.pop(field_name)
                if field_name in duplicate_field_names:
                    field_name = f'{field_name}_{field.db_column}'

            # Add the generated objects and information to the dict that optionally can
            # be returned.
            attrs['_field_objects'][field.id] = {
                'field': field,
                'type': field_type,
                'name': field_name
            }

            # Add the field to the attribute dict that is used to generate the model.
            # All the kwargs that are passed to the `get_model_field` method are going
            # to be passed along to the model field.
            attrs[field_name] = field_type.get_model_field(
                field, db_column=field.db_column, verbose_name=field.name)

        # Create the model class.
        model = type(
            str(f'{self.model_class_name}TableModel'),
            (models.Model,),
            attrs
        )

        # Immediately remove the model from the cache because it is used only once.
        model_name = model._meta.model_name
        all_models = model._meta.apps.all_models
        del all_models[app_label][model_name]

        return model
