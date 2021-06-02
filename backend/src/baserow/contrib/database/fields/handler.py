import logging
from copy import deepcopy

from django.conf import settings
from django.db import connections
from django.db.utils import ProgrammingError, DataError

from baserow.contrib.database.db.schema import lenient_schema_editor
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.utils import extract_allowed, set_allowed_attrs
from .exceptions import (
    PrimaryFieldAlreadyExists,
    CannotDeletePrimaryField,
    CannotChangeFieldType,
    FieldDoesNotExist,
    IncompatiblePrimaryFieldTypeError,
    MaxFieldLimitExceeded,
)
from .models import Field, SelectOption
from .registries import field_type_registry, field_converter_registry
from .signals import field_created, field_updated, field_deleted

logger = logging.getLogger(__name__)


class FieldHandler:
    def get_field(self, field_id, field_model=None, base_queryset=None):
        """
        Selects a field with a given id from the database.

        :param field_id: The identifier of the field that must be returned.
        :type field_id: int
        :param field_model: If provided that model's objects are used to select the
            field. This can for example be useful when you want to select a TextField or
            other child of the Field model.
        :type field_model: Field
        :param base_queryset: The base queryset from where to select the field.
            object. This can for example be used to do a `select_related`. Note that
            if this is used the `field_model` parameter doesn't work anymore.
        :type base_queryset: Queryset
        :raises FieldDoesNotExist: When the field with the provided id does not exist.
        :return: The requested field instance of the provided id.
        :rtype: Field
        """

        if not field_model:
            field_model = Field

        if not base_queryset:
            base_queryset = field_model.objects

        try:
            field = base_queryset.select_related("table__database__group").get(
                id=field_id
            )
        except Field.DoesNotExist:
            raise FieldDoesNotExist(f"The field with id {field_id} does not exist.")

        return field

    def create_field(
        self, user, table, type_name, primary=False, do_schema_change=True, **kwargs
    ):
        """
        Creates a new field with the given type for a table.

        :param user: The user on whose behalf the field is created.
        :type user: User
        :param table: The table that the field belongs to.
        :type table: Table
        :param type_name: The type name of the field. Available types can be found in
            the field_type_registry.
        :type type_name: str
        :param primary: Every table needs at least a primary field which cannot be
            deleted and is a representation of the whole row.
        :type primary: bool
        :param do_schema_change: Indicates whether or not he actual database schema
            change has be made.
        :type do_schema_change: bool
        :param kwargs: The field values that need to be set upon creation.
        :type kwargs: object
        :raises PrimaryFieldAlreadyExists: When we try to create a primary field,
            but one already exists.
        :raises MaxFieldLimitExceeded: When we try to create a field,
            but exceeds the field limit.
        :return: The created field instance.
        :rtype: Field
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        # Because only one primary field per table can exist and we have to check if one
        # already exists. If so the field cannot be created and an exception is raised.
        if primary and Field.objects.filter(table=table, primary=True).exists():
            raise PrimaryFieldAlreadyExists(
                f"A primary field already exists for the " f"table {table}."
            )

        # Figure out which model to use and which field types are allowed for the given
        # field type.
        field_type = field_type_registry.get(type_name)
        model_class = field_type.model_class
        allowed_fields = ["name"] + field_type.allowed_fields
        field_values = extract_allowed(kwargs, allowed_fields)
        last_order = model_class.get_last_order(table)

        num_fields = table.field_set.count()
        if (num_fields + 1) > settings.MAX_FIELD_LIMIT:
            raise MaxFieldLimitExceeded(
                f"Fields count exceeds the limit of {settings.MAX_FIELD_LIMIT}"
            )

        field_values = field_type.prepare_values(field_values, user)
        before = field_type.before_create(
            table, primary, field_values, last_order, user
        )

        instance = model_class.objects.create(
            table=table, order=last_order, primary=primary, **field_values
        )

        # Add the field to the table schema.
        connection = connections[settings.USER_TABLE_DATABASE]
        with connection.schema_editor() as schema_editor:
            to_model = table.get_model(field_ids=[], fields=[instance])
            model_field = to_model._meta.get_field(instance.db_column)

            if do_schema_change:
                schema_editor.add_field(to_model, model_field)

        field_type.after_create(instance, to_model, user, connection, before)

        field_created.send(self, field=instance, user=user, type_name=type_name)

        return instance

    def update_field(self, user, field, new_type_name=None, **kwargs):
        """
        Updates the values of the given field, if provided it is also possible to change
        the type.

        :param user: The user on whose behalf the table is updated.
        :type user: User
        :param field: The field instance that needs to be updated.
        :type field: Field
        :param new_type_name: If the type needs to be changed it can be provided here.
        :type new_type_name: str
        :param kwargs: The field values that need to be updated
        :type kwargs: object
        :raises ValueError: When the provided field is not an instance of Field.
        :raises CannotChangeFieldType: When the database server responds with an
            error while trying to change the field type. This should rarely happen
            because of the lenient schema editor, which replaces the value with null
            if it could not be converted.
        :return: The updated field instance.
        :rtype: Field
        """

        if not isinstance(field, Field):
            raise ValueError("The field is not an instance of Field.")

        group = field.table.database.group
        group.has_user(user, raise_error=True)

        old_field = deepcopy(field)
        field_type = field_type_registry.get_by_model(field)
        old_field_type = field_type
        from_model = field.table.get_model(field_ids=[], fields=[field])
        from_field_type = field_type.type

        # If the provided field type does not match with the current one we need to
        # migrate the field to the new type. Because the type has changed we also need
        # to remove all view filters.
        baserow_field_type_changed = new_type_name and field_type.type != new_type_name
        if baserow_field_type_changed:
            field_type = field_type_registry.get(new_type_name)

            if field.primary and not field_type.can_be_primary_field:
                raise IncompatiblePrimaryFieldTypeError(new_type_name)

            new_model_class = field_type.model_class
            field.change_polymorphic_type_to(new_model_class)

            # If the field type changes it could be that some dependencies,
            # like filters or sortings need to be changed.
            ViewHandler().field_type_changed(field)

        allowed_fields = ["name"] + field_type.allowed_fields
        field_values = extract_allowed(kwargs, allowed_fields)

        field_values = field_type.prepare_values(field_values, user)
        before = field_type.before_update(old_field, field_values, user)

        field = set_allowed_attrs(field_values, allowed_fields, field)
        field.save()

        connection = connections[settings.USER_TABLE_DATABASE]

        # If no converter is found we are going to convert to field using the
        # lenient schema editor which will alter the field's type and set the data
        # value to null if it can't be converted.
        to_model = field.table.get_model(field_ids=[], fields=[field])
        from_model_field = from_model._meta.get_field(field.db_column)
        to_model_field = to_model._meta.get_field(field.db_column)

        # Before a field is updated we are going to call the before_schema_change
        # method of the old field because some cleanup of related instances might
        # need to happen.
        old_field_type.before_schema_change(
            old_field,
            field,
            from_model,
            to_model,
            from_model_field,
            to_model_field,
            user,
        )

        # Try to find a data converter that can be applied.
        converter = field_converter_registry.find_applicable_converter(
            from_model, old_field, field
        )

        if converter:
            # If a field data converter is found we are going to use that one to alter
            # the field and maybe do some data conversion.
            converter.alter_field(
                old_field,
                field,
                from_model,
                to_model,
                from_model_field,
                to_model_field,
                user,
                connection,
            )
        else:
            if baserow_field_type_changed:
                # If the baserow type has changed we always want to force run any alter
                # column SQL as otherwise it might not run if the two baserow fields
                # share the same underlying database column type.
                force_alter_column = True
            else:
                force_alter_column = field_type.force_same_type_alter_column(
                    old_field, field
                )

            # If no field converter is found we are going to alter the field using the
            # the lenient schema editor.
            with lenient_schema_editor(
                connection,
                old_field_type.get_alter_column_prepare_old_value(
                    connection, old_field, field
                ),
                field_type.get_alter_column_prepare_new_value(
                    connection, old_field, field
                ),
                force_alter_column,
            ) as schema_editor:
                try:
                    schema_editor.alter_field(
                        from_model, from_model_field, to_model_field
                    )
                except (ProgrammingError, DataError) as e:
                    # If something is going wrong while changing the schema we will
                    # just raise a specific exception. In the future we want to have
                    # some sort of converter abstraction where the values of certain
                    # types can be converted to another value.
                    logger.error(str(e))
                    message = (
                        f"Could not alter field when changing field type "
                        f"{from_field_type} to {new_type_name}."
                    )
                    raise CannotChangeFieldType(message)

        from_model_field_type = from_model_field.db_parameters(connection)["type"]
        to_model_field_type = to_model_field.db_parameters(connection)["type"]
        altered_column = from_model_field_type != to_model_field_type

        # If the new field doesn't support select options we can delete those
        # relations.
        if (
            old_field_type.can_have_select_options
            and not field_type.can_have_select_options
        ):
            old_field.select_options.all().delete()

        field_type.after_update(
            old_field,
            field,
            from_model,
            to_model,
            user,
            connection,
            altered_column,
            before,
        )

        field_updated.send(self, field=field, user=user)

        return field

    def delete_field(self, user, field):
        """
        Deletes an existing field if it is not a primary field.

        :param user: The user on whose behalf the table is created.
        :type user: User
        :param field: The field instance that needs to be deleted.
        :type field: Field
        :raises ValueError: When the provided field is not an instance of Field.
        :raises CannotDeletePrimaryField: When we try to delete the primary field
            which cannot be deleted.
        """

        if not isinstance(field, Field):
            raise ValueError("The field is not an instance of Field")

        group = field.table.database.group
        group.has_user(user, raise_error=True)

        if field.primary:
            raise CannotDeletePrimaryField(
                "Cannot delete the primary field of a " "table."
            )

        field = field.specific
        field_type = field_type_registry.get_by_model(field)

        # Remove the field from the table schema.
        connection = connections[settings.USER_TABLE_DATABASE]
        with connection.schema_editor() as schema_editor:
            from_model = field.table.get_model(field_ids=[], fields=[field])
            model_field = from_model._meta.get_field(field.db_column)
            schema_editor.remove_field(from_model, model_field)

        field_id = field.id
        field.delete()

        # After the field is deleted we are going to to call the after_delete method of
        # the field type because some instance cleanup might need to happen.
        field_type.after_delete(field, from_model, user, connection)

        field_deleted.send(self, field_id=field_id, field=field, user=user)

    def update_field_select_options(self, user, field, select_options):
        """
        Brings the select options in the desired provided state in a query efficient
        manner.

        Example: select_options = [
            {'id': 1, 'value': 'Option 1', 'color': 'blue'},
            {'value': 'Option 2', 'color': 'red'}
        ]

        :param user: The user on whose behalf the change is made.
        :type user: User
        :param field: The field of which the select options must be updated.
        :type field: Field
        :param select_options: A list containing dicts with the desired select options.
        :type select_options: list
        """

        group = field.table.database.group
        group.has_user(user, raise_error=True)

        existing_select_options = field.select_options.all()

        # Checks which option ids must be selected by comparing the existing ids with
        # the provided ids.
        to_delete = [
            existing.id
            for existing in existing_select_options
            if existing.id
            not in [desired["id"] for desired in select_options if "id" in desired]
        ]

        if len(to_delete) > 0:
            SelectOption.objects.filter(field=field, id__in=to_delete).delete()

        # Checks which existing instances must be fetched using a single query.
        to_select = [
            select_option["id"]
            for select_option in select_options
            if "id" in select_option
        ]

        if len(to_select) > 0:
            for existing in field.select_options.filter(id__in=to_select):
                for select_option in select_options:
                    if select_option.get("id") == existing.id:
                        select_option["instance"] = existing

        to_create = []

        for order, select_option in enumerate(select_options):
            if "instance" in select_option:
                instance = select_option["instance"]
                instance.order = order
                instance.value = select_option["value"]
                instance.color = select_option["color"]
                instance.save()
            else:
                to_create.append(
                    SelectOption(
                        field=field,
                        order=order,
                        value=select_option["value"],
                        color=select_option["color"],
                    )
                )

        if len(to_create) > 0:
            SelectOption.objects.bulk_create(to_create)
