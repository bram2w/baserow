from django.db.models import Q

from baserow.core.registry import (
    Instance,
    Registry,
    ModelInstanceMixin,
    ModelRegistryMixin,
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    MapAPIExceptionsInstanceMixin,
    APIUrlsRegistryMixin,
    APIUrlsInstanceMixin,
    ImportExportMixin,
)

from .exceptions import FieldTypeAlreadyRegistered, FieldTypeDoesNotExist
from .models import SelectOption


class FieldType(
    MapAPIExceptionsInstanceMixin,
    APIUrlsInstanceMixin,
    CustomFieldsInstanceMixin,
    ModelInstanceMixin,
    ImportExportMixin,
    Instance,
):
    """
    This abstract class represents a custom field type that can be added to the
    field type registry. It must be extended so customisation can be done. Each field
    type will have his own model that must extend the Field model, this is needed so
    that the user can set custom settings per field instance he has created.

    Example:
        from baserow.contrib.database.fields.models import Field
        from baserow.contrib.database.fields.registry import (
            FieldType, field_type_registry
        )

        class ExampleFieldModel(FieldType):
            pass

        class ExampleFieldType(FieldType):
            type = 'a-unique-field-type-name'
            model_class = ExampleFieldModel
            allowed_fields = ['text_default']
            serializer_field_names = ['text_default']
            serializer_field_overrides = {
                'text_default': serializers.CharField()
            }

        field_type_registry.register(ExampleFieldType())
    """

    can_order_by = True
    """Indicates whether it is possible to order by this field type."""

    can_be_primary_field = True
    """Some field types cannot be the primary field."""

    can_have_select_options = False
    """Indicates whether the field can have select options."""

    def prepare_value_for_db(self, instance, value):
        """
        When a row is created or updated all the values are going to be prepared for the
        database. The value for this field type will run through this method and the
        returned value will be used. It is also possible to raise validation errors if
        the value is incorrect.

        :param instance: The field instance.
        :type instance: Field
        :param value: The value that needs to be inserted or updated.
        :type value: str
        :return: The modified value that is going to be saved in the database.
        :rtype: str
        """

        return value

    def enhance_queryset(self, queryset, field, name):
        """
        This hook can be used to enhance a queryset when fetching multiple rows of a
        table. This is for example used by the grid view endpoint. Many rows can be
        requested there and if the table has a `link_row` field it can become slow
        because the .all() method of the ManyToMany field is called for every row.
        In case of the `link_row` field we could enhance the queryset by using the
        `prefetch_related` function in order to prevent many queries.

        Note that the enhance_queryset will be called for each field in the table. So
        this hook should only optimise the queryset for the provided field.

        :param queryset: The queryset that can be enhanced.
        :type: QuerySet
        :param field: The related field's instance. The queryset can optionally be
            enhanced based on the properties of the field.
        :type field: Field
        :param name: The name of the field.
        :type name: str
        :return: The enhanced queryset.
        :rtype: QuerySet
        """

        return queryset

    def contains_query(self, field_name, value, model_field, field):
        """
        Returns a Q or AnnotatedQ filter which performs a contains filter over the
        provided field for this specific type of field.

        :param field_name: The name of the field.
        :type field_name: str
        :param value: The value to check if this field contains or not.
        :type value: str
        :param model_field: The field's actual django field model instance.
        :type model_field: models.Field
        :param field: The related field's instance.
        :type field: Field
        :return: A Q or AnnotatedQ filter.
            given value.
        :rtype: OptionallyAnnotatedQ
        """

        return Q()

    def get_serializer_field(self, instance, **kwargs):
        """
        Should return the serializer field based on the custom model instance
        attributes. It is common that the field is not required so that a user
        doesn't have to update the field each time another field in the same row
        changes.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The serializer field that represents the field instance attributes.
        :rtype: serializer.Field
        """

        raise NotImplementedError("Each must have his own get_serializer_field method.")

    def get_response_serializer_field(self, instance, **kwargs):
        """
        The response serializer field can be overridden if the field's value should be
        represented in a different way when the value is included in a response. This
        will for example happen with a user lists all the rows in the grid view,
        but also in the response after creating a row. By default the serializer that
        also handles the validation and input is returned here.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The serializer field that represents the field instance attributes.
        :rtype: serializer.Field
        """

        return self.get_serializer_field(instance, **kwargs)

    def get_serializer_help_text(self, instance):
        """
        If some additional information in the documentation related to the field's type
        is required then that can be returned here. It will be added to the
        `create_database_table_row` part.

        :param instance:
        :type: Struct
        :return: The additional field documentation.
        :rtype: str
        """

        return ""

    def get_model_field(self, instance, **kwargs):
        """
        Should return the model field based on the custom model instance attributes. It
        is common that the field can be blank because people are going to create a row
        without any data in it.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The model field that represents the field instance attributes.
        :rtype: model.Field
        """

        raise NotImplementedError("Each must have his own get_model_field method.")

    def after_model_generation(self, instance, model, field_name, manytomany_models):
        """
        After the model is generated the after_model_generation method of each field
        is also called to make some additional changes when whole model is available.
        This is for example used by the LinkRow field so that the ManyToMany field
        can be added later.

        :param instance: The field instance object.
        :type instance: Field
        :param model: The generated model containing all fields.
        :type model: Model
        :param field_name: The given name of the field in the model.
        :type field_name: str
        :param manytomany_models: A dict containing cached related manytomany models in
            order to prevent model generation loop.
        :type manytomany_models: dict
        """

    def random_value(self, instance, fake, cache):
        """
        Should return a random value that can be used as value for the field. This is
        used by the fill_table management command which will add an N amount of rows
        to the a table with random data.

        :param instance: The field instance for which to get the random value for.
        :type instance: Field
        :param fake: An instance of the Faker package.
        :type fake: Faker
        :param cache: A small in memory cache dict that can be used to store data
            that is needed for to generate a random value.
        :type dict: dict
        :return: The randomly generated value.
        :rtype: any
        """

        return None

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        """
        Can return an SQL statement to convert the `p_in` variable to a readable text
        format for the new field.
        This SQL will not be run when converting between two fields of the same
        baserow type which share the same underlying database column type.
        If you require this then implement force_same_type_alter_column.

        Example: return "p_in = lower(p_in);"

        :param connection: The used connection. This can for example be used to check
            the database engine type.
        :type connection: DatabaseWrapper
        :param from_field: The old field instance.
        :type to_field: Field
        :param to_field: The new field instance.
        :type to_field: Field
        :return: The SQL statement converting the value to text for the next field. The
            can for example be used to convert a select option to plain text.
        :rtype: None or str
        """

        return None

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        """
        Can return a SQL statement to convert the `p_in` variable from text to a
        desired format for the new field.
        This SQL will not be run when converting between two fields of the same
        baserow type which share the same underlying database column type.
        If you require this then implement force_same_type_alter_column.

        Example: when a string is converted to a number, to statement could be:
        `REGEXP_REPLACE(p_in, '[^0-9]', '', 'g')` which would remove all non numeric
        characters. The p_in variable is the old value as a string.

        :param connection: The used connection. This can for example be used to check
            the database engine type.
        :type connection: DatabaseWrapper
        :param from_field: The old field instance.
        :type to_field: Field
        :param to_field: The new field instance.
        :type to_field: Field
        :return: The SQL statement converting the old text value into the correct
            format.
        :rtype: None or str
        """

        return None

    def prepare_values(self, values, user):
        """
        The prepare_values hook gives the possibility to change the provided values
        that just before they are going to be used to create or update the instance. For
        example if an ID is provided it can be converted to a model instance. Or to
        convert a certain date string to a date object.

        :param values: The provided values.
        :type values: dict
        :param user: The user on whose behalf the change is made.
        :type user: User
        :return: The updates values.
        :type: dict
        """

        return values

    def before_create(self, table, primary, values, order, user):
        """
        This cook is called just before the fields instance is created. Here some
        additional checks can be done based on the provided values.

        :param table: The table where the field is going to be added to.
        :type table: Table
        :param primary: Indicates whether the field is going to be a primary field.
        :type primary: bool
        :param values: The new values that are going to be passed when creating the
            field instance.
        :type values: dict
        :param order: The order that the field is going to get in the database.
        :type order: int
        :param user: The user on whose behalf the change is made.
        :type user: User
        """

    def after_create(self, field, model, user, connection, before):
        """
        This hook is called right after the has been created. The schema change has
        also been done so the provided model could optionally be used.

        :param field: The created field instance.
        :type field: Field
        :param model: The Django model that contains the newly created field.
        :type model: Model
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        :param before: The value returned by the before_created method.
        :type before: any
        """

    def before_update(self, from_field, to_field_values, user):
        """
        This hook is called just before updating the field instance. It is called on
        the to (new) field type if it changes. Here some additional checks can be
        done based on the provided values.

        :param from_field: The old field instance.
        :type from_field: Field
        :param to_field_values: The values that are going to be updated.
        :type to_field_values: dict
        :param user: The user on whose behalf the change is made.
        :type user: User
        """

    def before_schema_change(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        from_model_field,
        to_model_field,
        user,
    ):
        """
        This hook is called just before the database's schema change. In some cases
        some additional cleanup or creation of related instances has to happen if the
        field type changes. That can happen here.

        :param from_field: The old field instance. It is not recommended to call the
            save function as this will undo part of the changes that have been made.
            This is just for comparing values.
        :type from_field: Field
        :param to_field: The updated field instance.
        :type: to_field: Field
        :param from_model: The old generated model containing only the old field.
        :type from_model: Model
        :param to_model: The generated model containing only the new field.
        :type to_model: Model
        :param from_model_field: The old field extracted from the old model.
        :type from_model_field: models.Field
        :param to_model_field: The new field extracted from the new model.
        :type to_model_field: models.Field
        :param user: The user on whose behalf the change is made.
        :type user: User
        """

    def after_update(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        user,
        connection,
        altered_column,
        before,
    ):
        """
        This hook is called right after a field has been updated. In some cases data
        mutation still has to be done in order to maintain data integrity. For example
        when the only the allowing of negative values has been changed for the number
        field.

        :param from_field: The old field instance. It is not recommended to call the
            save function as this will undo part of the changes that have been made.
            This is just for comparing values.
        :type from_field: Field
        :param to_field: The updated field instance.
        :type: to_field: Field
        :param from_model: The old generated model containing only the old field.
        :type from_model: Model
        :param to_model: The generated model containing only the new field.
        :type to_model: Model
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        :param altered_column: Indicates whether the column has been altered in the
            table. Sometimes data has to be updated if the column hasn't been altered.
        :type altered_column: bool
        :param before: The value returned by the before_update method.
        :type before: any
        """

    def after_delete(self, field, model, user, connection):
        """
        This hook is called right after the field has been deleted and the schema
        change has been done.

        :param field: The deleted field instance.
        :type field: Field
        :param model: The Django model that contains the deleted field.
        :type model: Model
        :param user: The user on whose behalf the delete is done.
        :type user: User
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        """

    def get_order(self, field, field_name, view_sort):
        """
        This hook can be called to generate a different order by expression. By default
        None is returned which means the normal field sorting will be applied.
        Optionally a different expression can be generated. This is for example used
        by the single select field generates a mapping achieve the correct sorting
        based on the select option value.

        :param field: The related field object instance.
        :type field: Field
        :param field_name: The name of the field.
        :type field_name: str
        :param view_sort: The view sort that must be applied.
        :type view_sort: ViewSort
        :return: The expression that is added directly to the model.objects.order().
        :rtype: Expression or None
        """

        return None

    def force_same_type_alter_column(self, from_field, to_field):
        """
        Defines whether the sql provided by the get_alter_column_prepare_{old,new}_value
        hooks should be forced to run when converting between two fields of this field
        type which have the same database column type.
        You only need to implement this when when you have validation and/or data
        manipulation running as part of your alter_column_prepare SQL which must be
        run even when from_field and to_field are the same Baserow field type and sql
        column type. If your field has the same baserow type but will convert into
        different sql column types then the alter sql will be run automatically and you
        do not need to use this override.

        :param from_field: The old field instance. It is not recommended to call the
            save function as this will undo part of the changes that have been made.
            This is just for comparing values.
        :type from_field: Field
        :param to_field: The updated field instance.
        :type: to_field: Field
        :return: Whether the alter column sql should be forced to run.
        :rtype: bool
        """

        return False

    def export_serialized(self, field, include_allowed_fields=True):
        """
        Exports the field to a serialized dict that can be imported by the
        `import_serialized` method. This dict is also JSON serializable.

        :param field: The field instance that must be exported.
        :type field: Field
        :param include_allowed_fields: Indicates whether or not the allowed fields
            should automatically be added to the serialized object.
        :type include_allowed_fields: bool
        :return: The exported field in as serialized dict.
        :rtype: dict
        """

        serialized = {
            "id": field.id,
            "type": self.type,
            "name": field.name,
            "order": field.order,
            "primary": field.primary,
        }

        if include_allowed_fields:
            for field_name in self.allowed_fields:
                serialized[field_name] = getattr(field, field_name)

        if self.can_have_select_options:
            serialized["select_options"] = [
                {
                    "id": select_option.id,
                    "value": select_option.value,
                    "color": select_option.color,
                    "order": select_option.order,
                }
                for select_option in field.select_options.all()
            ]

        return serialized

    def import_serialized(self, table, serialized_values, id_mapping):
        """
        Imported an exported serialized field dict that was exported via the
        `export_serialized` method.

        :param table: The table where the field should be added to.
        :type table: Table
        :param serialized_values: The exported serialized field values that need to
            be imported.
        :type serialized_values: dict
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :type id_mapping: dict
        :return: The newly created field instance.
        :rtype: Field
        """

        if "database_fields" not in id_mapping:
            id_mapping["database_fields"] = {}
            id_mapping["database_field_select_options"] = {}

        serialized_copy = serialized_values.copy()
        field_id = serialized_copy.pop("id")
        serialized_copy.pop("type")
        select_options = (
            serialized_copy.pop("select_options")
            if self.can_have_select_options
            else []
        )
        field = self.model_class.objects.create(table=table, **serialized_copy)

        id_mapping["database_fields"][field_id] = field.id

        if self.can_have_select_options:
            for select_option in select_options:
                select_option_copy = select_option.copy()
                select_option_id = select_option_copy.pop("id")
                select_option_object = SelectOption.objects.create(
                    field=field, **select_option_copy
                )
                id_mapping["database_field_select_options"][
                    select_option_id
                ] = select_option_object.id

        return field

    def get_export_serialized_value(self, row, field_name, cache):
        """
        Exports the value to a the value of a row to serialized value that is also JSON
        serializable.

        :param row: The row instance that the value must be exported from.
        :type row: Object
        :param field_name: The name of the field that must be exported.
        :type field_name: str
        :param cache: An in memory dictionary that is shared between all fields while
            exporting the table. This is for example used by the link row field type
            to prefetch all relations.
        :type cache: dict
        :return: The exported value.
        :rtype: Object
        """

        return getattr(row, field_name)

    def set_import_serialized_value(self, row, field_name, value, id_mapping):
        """
        Sets an imported and serialized value on a row instance.

        :param row: The row instance where the value be set on.
        :type row: Object
        :param field_name: The name of the field that must be set.
        :type field_name: str
        :param value: The value that must be set.
        :type value: Object
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :type id_mapping: dict
        """

        setattr(row, field_name, value)


class FieldTypeRegistry(
    APIUrlsRegistryMixin, CustomFieldsRegistryMixin, ModelRegistryMixin, Registry
):
    """
    With the field type registry it is possible to register new field types.  A field
    type is an abstraction made specifically for Baserow. If added to the registry a
    user can create new fields based on this type.
    """

    name = "field"
    does_not_exist_exception_class = FieldTypeDoesNotExist
    already_registered_exception_class = FieldTypeAlreadyRegistered


class FieldConverter(Instance):
    """
    By default when changing a field the lenient schema editor is used to alter the
    field to make the schema changes. If for whatever reason this does not suffice
    then a converter can be used to change field and the related data. This is for
    example used by the link_row field because it is not possible to change a
    ManyToManyField to another field.

    Example:
        from baserow.contrib.database.fields.field_types import (
            TextFieldType, DateFieldType
        )
        from baserow.contrib.database.fields.registries import (
            FieldConverter, field_converter_registry
        )

        class TextToDateFieldConverter(FieldConverter):
            type = 'text-to-date'

            def is_applicable(self, from_model, from_field, to_field):
                return (
                    isinstance(from_field, TextFieldType) and
                    isinstance(to_field, DateFieldType)
                )

            def alter_field(self, from_field, to_field, from_model, to_model,
                            from_model_field, to_model_field, user, connection):
                # This is just for example purposes, but it will delete the old text
                # field field and create a new date field. You can be very creative
                # here in how you want to convert field and the data. It is for example
                # possible to load all the old data in memory, convert it and then
                # update the new data. Performance should always be kept in mind
                # though.
                with connection.schema_editor() as schema_editor:
                    schema_editor.remove_field(from_model, from_model_field)
                    schema_editor.add_field(to_model, to_model_field)


        field_converter_registry.register(TextToDateFieldConverter())
    """

    def is_applicable(self, from_model, from_field, to_field):
        """
        Decides whether the converter is applicable for the alteration of the provided
        fields. Before conversion all converters are checked to see if they are
        applicable. The first one that is will be used.

        :param from_model: The old model containing only the old field.
        :type from_model: Model
        :param from_field: The old field instance. It should only be used for type and
            property comparison with the the to_field because else things might break.
        :type from_field: Field
        :param to_field: The new field instance. It should only be used for type and
            property comparison with the the from_field because else things might
            break.
        :type to_field: Field
        :return: If True then the alter_field method of this converter will be used
            to alter the field instead of the lenient schema editor.
        :rtype: bool
        """

        raise NotImplementedError(
            "Each field converter must have an is_applicable " "method."
        )

    def alter_field(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        from_model_field,
        to_model_field,
        user,
        connection,
    ):
        """
        Should perform the schema change and changes related to the field change. It
        must bring the field's schema into the desired state.

        :param from_field: The old field's instance. This should be used for getting
            the type and properties. Making changes can override things.
        :type from_field: Field
        :param to_field: The new field's instance. This should be used for getting the
            type and properties. It already is in a correct state.
        :type to_field: Field
        :param from_model: The old generated model containing only the old field.
        :type from_model: Model
        :param to_model: The generated model containing only the new field.
        :type to_model: Model
        :param from_model_field: The old field extracted from the old model.
        :type from_model_field: models.Field
        :param to_model_field: The new field extracted from the new model.
        :type to_model_field: models.Field
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        """

        raise NotImplementedError(
            "Each field converter must have an alter_field " "method."
        )


class FieldConverterRegistry(Registry):
    """
    The registry that holds all the available field converters. A field converter can
    be used to convert a field to another type in a custom way. It can also be used the
    data related to the field needs a specific conversion. It should be used when the
    default lenient schema editor does not work.
    """

    name = "field_converter"

    def find_applicable_converter(self, *args, **kwargs):
        """
        Finds the first applicable converter that is in the register based on the
        provided arguments. Note that is might be possible for other converters to be
        applicable also. This only returns the first match, not the best match. Might
        be an idea to implement something with a priority system once we have lots of
        converters.

        :return: The applicable field converter or None if no converter has been found.
        :rtype: None or FieldConverter
        """

        for converter in self.registry.values():
            if converter.is_applicable(*args, **kwargs):
                return converter
        return None


# A default field type registry is created here, this is the one that is used
# throughout the whole Baserow application to add a new field type.
field_type_registry = FieldTypeRegistry()
field_converter_registry = FieldConverterRegistry()
