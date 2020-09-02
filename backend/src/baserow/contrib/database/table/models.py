from django.db import models

from baserow.core.mixins import OrderableMixin
from baserow.contrib.database.fields.registries import field_type_registry


class TableModelQuerySet(models.QuerySet):
    def enhance_by_fields(self):
        """
        Enhances the queryset based on the `enhance_queryset` for each field in the
        table. For example the `link_row` field adds the `prefetch_related` to prevent
        N queries per row. This helper should only be used when multiple rows are going
        to be fetched.

        :return: The enhanced queryset.
        :rtype: QuerySet
        """

        for field_object in self.model._field_objects.values():
            self = field_object['type'].enhance_queryset(
                self,
                field_object['field'],
                field_object['name']
            )
        return self

    def search_all_fields(self, search):
        """
        Searches very broad in all supported fields with the given search query. If the
        primary key value matches then that result would be returned and if a char/text
        field contains the search query then that result would be returned.

        :param search: The search query.
        :type search: str
        :return: The queryset containing the search queries.
        :rtype: QuerySet
        """

        search_queries = models.Q()

        for field in self.model._meta.get_fields():
            if (
                isinstance(field, models.CharField) or
                isinstance(field, models.TextField)
            ):
                search_queries = search_queries | models.Q(**{
                    f'{field.name}__icontains': search
                })
            elif (
                isinstance(field, models.AutoField) or
                isinstance(field, models.IntegerField)
            ):
                try:
                    search_queries = search_queries | models.Q(**{
                        f'{field.name}': int(search)
                    })
                except ValueError:
                    pass

        return self.filter(search_queries) if len(search_queries) > 0 else self


class TableModelManager(models.Manager):
    def get_queryset(self):
        return TableModelQuerySet(self.model, using=self._db)


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

    def get_model(self, fields=None, field_ids=None, attribute_names=False,
                  manytomany_models=None):
        """
        Generates a temporary Django model based on available fields that belong to
        this table. Note that the model will not be registered with the apps because
        of the `DatabaseConfig.prevent_generated_model_for_registering` hack. We do
        not want to the model cached because models with the same name can differ.

        :param fields: Extra table field instances that need to be added the model.
        :type fields: list
        :param field_ids: If provided only the fields with the ids in the list will be
            added to the model. This can be done to improve speed if for example only a
            single field needs to be mutated.
        :type field_ids: None or list
        :param attribute_names: If True, the the model attributes will be based on the
            field name instead of the field id.
        :type attribute_names: bool
        :param manytomany_models: In some cases with related fields a model has to be
            generated in order to generate that model. In order to prevent a
            recursion loop we cache the generated models and pass those along.
        :type manytomany_models: dict
        :return: The generated model.
        :rtype: Model
        """

        if not fields:
            fields = []

        if not manytomany_models:
            manytomany_models = {}

        app_label = 'database_table'
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
            '_table_id': self.id,
            # An object containing the table fields, field types and the chosen names
            # with the table field id as key.
            '_field_objects': {},
            # We are using our own table model manager to implement some queryset
            # helpers.
            'objects': TableModelManager()
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
                field, db_column=field.db_column, verbose_name=field.name
            )

        # Create the model class.
        model = type(
            str(f'Table{self.pk}Model'),
            (models.Model,),
            attrs
        )

        # In some situations the field can only be added once the model class has been
        # generated. So for each field we will call the after_model_generation with
        # the generated model as argument in order to do this. This is for example used
        # by the link row field. It can also be used to make other changes to the
        # class.
        for field_id, field_object in attrs['_field_objects'].items():
            field_object['type'].after_model_generation(
                field_object['field'],
                model,
                field_object['name'],
                manytomany_models
            )

        return model
