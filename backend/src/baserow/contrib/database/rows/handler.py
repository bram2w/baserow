import re
from collections import defaultdict
from decimal import Decimal
from math import floor, ceil

from django.db import transaction
from django.db.models import Max, F
from django.db.models.fields.related import ManyToManyField

from baserow.core.trash.handler import TrashHandler
from .exceptions import RowDoesNotExist, RowIdsNotUnique
from .signals import (
    before_row_update,
    before_row_delete,
    row_created,
    row_updated,
    rows_updated,
    row_deleted,
)
from baserow.contrib.database.fields.dependencies.update_collector import (
    CachingFieldUpdateCollector,
)
from baserow.core.utils import get_non_unique_values


class RowHandler:
    def prepare_values(self, fields, values):
        """
        Prepares a set of values so that they can be created or updated in the database.
        It will check if the value can actually be set and prepares the value based on
        the field type.

        :param fields: The returned fields object from the get_model method.
        :type fields: dict
        :param values: The values that need to be prepared with the field id or the
            string 'field_{id}' as key.
        :type values: dict
        :return: The prepared values with the field name as key.
        :rtype: dict
        """

        return {
            field["name"]: field["type"].prepare_value_for_db(
                field["field"],
                values[field_id] if field_id in values else values[field["name"]],
            )
            for field_id, field in fields.items()
            if field_id in values or field["name"] in values
        }

    def prepare_rows_in_bulk(self, fields, rows):
        """
        Prepares a set of values in bulk for all rows so that they can be created or
        updated in the database. It will check if the values can actually be set and
        prepares them based on their field type.

        :param fields: The returned fields object from the get_model method.
        :type fields: dict
        :param values: The rows and their values that need to be prepared.
        :type values: dict
        :return: The prepared values for all rows in the same structure as it was
            passed in.
        :rtype: dict
        """

        field_ids = {}
        prepared_values_by_field = defaultdict(dict)

        # organize values by field name
        for index, row in enumerate(rows):
            for field_id, field in fields.items():
                field_name = field["name"]
                field_ids[field_name] = field_id
                if field_name in row:
                    prepared_values_by_field[field_name][index] = row[field_name]

        # bulk-prepare values per field
        for field_name, batch_values in prepared_values_by_field.items():
            field = fields[field_ids[field_name]]
            field_type = field["type"]
            prepared_values_by_field[
                field_name
            ] = field_type.prepare_value_for_db_in_bulk(
                field["field"],
                batch_values,
            )

        # replace original values to keep ordering
        prepared_rows = []
        for index, row in enumerate(rows):
            new_values = row
            for field_id, field in fields.items():
                field_name = field["name"]
                if field_name in row:
                    new_values[field_name] = prepared_values_by_field[field_name][index]
            prepared_rows.append(new_values)

        return prepared_rows

    def extract_field_ids_from_dict(self, values):
        """
        Extracts the field ids from a dict containing the values that need to be
        updated. For example keys like 'field_2', '3', 4 will be seen ass field ids.

        :param values: The values where to extract the fields ids from.
        :type values: dict
        :return: A list containing the field ids as integers.
        :rtype: list
        """

        field_pattern = re.compile("^field_([0-9]+)$")
        # @TODO improve this function
        return [
            int(re.sub("[^0-9]", "", str(key)))
            for key in values.keys()
            if str(key).isnumeric() or field_pattern.match(str(key))
        ]

    def extract_manytomany_values(self, values, model):
        """
        Extracts the ManyToMany values out of the values because they need to be
        created and updated in a different way compared to a regular value.

        :param values: The values where to extract the manytomany values from.
        :type values: dict
        :param model: The model containing the fields. The key, which is also the
            field name, is used to check in the model if the value is a ManyToMany
            value.
        :type model: Model
        :return: The values without the manytomany values and the manytomany values
            in another dict.
        :rtype: dict, dict
        """

        manytomany_values = {}

        for name, value in values.items():
            model_field = model._meta.get_field(name)
            if isinstance(model_field, ManyToManyField):
                manytomany_values[name] = values[name]

        for name in manytomany_values.keys():
            del values[name]

        return values, manytomany_values

    def get_order_before_row(self, before, model):
        """
        Calculates a new unique order which will be before the provided before row
        order. This order can be used by an existing or new row. Several other rows
        could be updated as their order might need to change.

        :param before: The row instance where the before order must be calculated for.
        :type before: Table
        :param model: The model of the related table
        :type model: Model
        :return: The new order.
        :rtype: Decimal
        """

        if before:
            # Here we calculate the order value, which indicates the position of the
            # row, by subtracting a fraction of the row that it must be placed
            # before. The same fraction is also going to be subtracted from the other
            # rows that have been placed before. By using these fractions we don't
            # have to re-order every row in the table.
            change = Decimal("0.00000000000000000001")
            order = before.order - change
            model.objects.filter(order__gt=floor(order), order__lte=order).update(
                order=F("order") - change
            )
        else:
            # Because the row is by default added as last, we have to figure out what
            # the highest order is and increase that by one. Because the order of new
            # rows should always be a whole number we round it up.
            order = (
                ceil(
                    model.objects.aggregate(max=Max("order")).get("max") or Decimal("0")
                )
                + 1
            )

        return order

    def get_row(self, user, table, row_id, model=None):
        """
        Fetches a single row from the provided table.

        :param user: The user of whose behalf the row is requested.
        :type user: User
        :param table: The table where the row must be fetched from.
        :type table: Table
        :param row_id: The id of the row that must be fetched.
        :type row_id: int
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :type model: Model
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        :return: The requested row instance.
        :rtype: Model
        """

        if not model:
            model = table.get_model()

        group = table.database.group
        group.has_user(user, raise_error=True)

        try:
            row = model.objects.get(id=row_id)
        except model.DoesNotExist:
            raise RowDoesNotExist(row_id)

        return row

    # noinspection PyMethodMayBeStatic
    def has_row(self, user, table, row_id, raise_error=False, model=None):
        """
        Checks if a row with the given id exists and is not trashed in the table.

        This method is preferred over using get_row when you do not actually need to
        access any values of the row as it will not construct a full model but instead
        do a much more effecient query to check only if the row exists or not.

        :param user: The user of whose behalf the row is being checked.
        :type user: User
        :param table: The table where the row must be checked in.
        :type table: Table
        :param row_id: The id of the row that must be checked.
        :type row_id: int
        :param raise_error: Whether or not to raise an Exception if the row does not
            exist or just return a boolean instead.
        :type raise_error: bool
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :type model: Model
        :raises RowDoesNotExist: When the row with the provided id does not exist
            and raise_error is set to True.
        :raises UserNotInGroup: If the user does not belong to the group.
        :return: If raise_error is False then a boolean indicating if the row does or
            does not exist.
        :rtype: bool
        """

        if not model:
            model = table.get_model(field_ids=[])

        group = table.database.group
        group.has_user(user, raise_error=True)

        row_exists = model.objects.filter(id=row_id).exists()
        if not row_exists and raise_error:
            raise RowDoesNotExist(row_id)
        else:
            return row_exists

    def create_row(
        self, user, table, values=None, model=None, before=None, user_field_names=False
    ):
        """
        Creates a new row for a given table with the provided values if the user
        belongs to the related group. It also calls the row_created signal.

        :param user: The user of whose behalf the row is created.
        :type user: User
        :param table: The table for which to create a row for.
        :type table: Table
        :param values: The values that must be set upon creating the row. The keys must
            be the field ids.
        :type values: dict
        :param model: If a model is already generated it can be provided here to avoid
            having to generate the model again.
        :type model: Model
        :param before: If provided the new row will be placed right before that row
            instance.
        :type before: Table
        :param user_field_names: Whether or not the values are keyed by the internal
            Baserow field name (field_1,field_2 etc) or by the user field names.
        :type user_field_names: True
        :return: The created row instance.
        :rtype: Model
        """

        if not model:
            model = table.get_model()

        group = table.database.group
        group.has_user(user, raise_error=True)

        instance = self.force_create_row(table, values, model, before, user_field_names)

        row_created.send(
            self, row=instance, before=before, user=user, table=table, model=model
        )

        return instance

    def force_create_row(
        self, table, values=None, model=None, before=None, user_field_names=False
    ):
        """
        Creates a new row for a given table with the provided values.

        :param table: The table for which to create a row for.
        :type table: Table
        :param values: The values that must be set upon creating the row. The keys must
            be the field ids.
        :type values: dict
        :param model: If a model is already generated it can be provided here to avoid
            having to generate the model again.
        :type model: Model
        :param before: If provided the new row will be placed right before that row
            instance.
        :type before: Table
        :param user_field_names: Whether or not the values are keyed by the internal
            Baserow field name (field_1,field_2 etc) or by the user field names.
        :type user_field_names: True
        :return: The created row instance.
        :rtype: Model
        """

        if not values:
            values = {}

        if not model:
            model = table.get_model()

        if user_field_names:
            values = self.map_user_field_name_dict_to_internal(
                model._field_objects, values
            )

        values = self.prepare_values(model._field_objects, values)
        values, manytomany_values = self.extract_manytomany_values(values, model)
        values["order"] = self.get_order_before_row(before, model)
        instance = model.objects.create(**values)

        for name, value in manytomany_values.items():
            getattr(instance, name).set(value)

        if model.fields_requiring_refresh_after_insert():
            instance.save()
            instance.refresh_from_db(
                fields=model.fields_requiring_refresh_after_insert()
            )

        updated_fields = [field["field"] for field in model._field_objects.values()]
        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=instance.id, existing_model=model
        )
        for field in updated_fields:
            for (
                dependant_field,
                dependant_field_type,
                path_to_starting_table,
            ) in field.dependant_fields_with_types(update_collector):
                dependant_field_type.row_of_dependency_created(
                    dependant_field, instance, update_collector, path_to_starting_table
                )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        ViewHandler().field_value_updated(updated_fields)

        return instance

    # noinspection PyMethodMayBeStatic
    def map_user_field_name_dict_to_internal(
        self,
        field_objects,
        values,
    ):
        """
        Takes the field objects for a model and a dictionary keyed by user specified
        field names for that model. Then will convert the keys from the user names to
        the internal Baserow field names which look like field_1, field_2 and
        correspond to the actual database column names.

        :param field_objects: The field objects for a model.
        :param values: A dictionary keyed by user field names to values.
        :return: A dictionary with the same values but the keys converted to the
            corresponding internal baserow field name (field_1,field_2 etc)
        """

        to_internal_name = {}
        for field_object in field_objects.values():
            to_internal_name[field_object["field"].name] = field_object["name"]

        mapped_back_to_internal_field_names = {}
        for user_field_name, value in values.items():
            internal_name = to_internal_name[user_field_name]
            mapped_back_to_internal_field_names[internal_name] = value
        values = mapped_back_to_internal_field_names
        return values

    def update_row(
        self, user, table, row_id, values, model=None, user_field_names=False
    ):
        """
        Updates one or more values of the provided row_id.

        :param user: The user of whose behalf the change is made.
        :type user: User
        :param table: The table for which the row must be updated.
        :type table: Table
        :param row_id: The id of the row that must be updated.
        :type row_id: int
        :param values: The values that must be updated. The keys must be the field ids.
        :type values: dict
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :type model: Model
        :param user_field_names: Whether or not the values are keyed by the internal
            Baserow field name (field_1,field_2 etc) or by the user field names.
        :type user_field_names: True
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        :return: The updated row instance.
        :rtype: Model
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if not model:
            model = table.get_model()

        with transaction.atomic():
            try:
                row = (
                    model.objects.select_for_update().enhance_by_fields().get(id=row_id)
                )
            except model.DoesNotExist:
                raise RowDoesNotExist(row_id)

            updated_fields = []
            updated_field_ids = set()
            for field_id, field in model._field_objects.items():
                if field_id in values or field["name"] in values:
                    updated_field_ids.add(field_id)
                    updated_fields.append(field["field"])

            before_return = before_row_update.send(
                self,
                row=row,
                user=user,
                table=table,
                model=model,
                updated_field_ids=updated_field_ids,
            )
            if user_field_names:
                values = self.map_user_field_name_dict_to_internal(
                    model._field_objects, values
                )
            values = self.prepare_values(model._field_objects, values)
            values, manytomany_values = self.extract_manytomany_values(values, model)

            for name, value in values.items():
                setattr(row, name, value)

            for name, value in manytomany_values.items():
                getattr(row, name).set(value)

            row.save()

            update_collector = CachingFieldUpdateCollector(
                table, starting_row_id=row.id, existing_model=model
            )
            for field in updated_fields:
                for (
                    dependant_field,
                    dependant_field_type,
                    path_to_starting_table,
                ) in field.dependant_fields_with_types(update_collector):
                    dependant_field_type.row_of_dependency_updated(
                        dependant_field, row, update_collector, path_to_starting_table
                    )
            update_collector.apply_updates_and_get_updated_fields()
            # We need to refresh here as ExpressionFields might have had their values
            # updated. Django does not support UPDATE .... RETURNING and so we need to
            # query for the rows updated values instead.
            row.refresh_from_db(fields=model.fields_requiring_refresh_after_update())

        from baserow.contrib.database.views.handler import ViewHandler

        ViewHandler().field_value_updated(updated_fields)

        row_updated.send(
            self,
            row=row,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
            updated_field_ids=updated_field_ids,
        )

        return row

    def update_rows(self, user, table, rows, model=None):
        """
        Updates field values in batch based on provided rows with the new values.

        :param user: The user of whose behalf the change is made.
        :type user: User
        :param table: The table for which the row must be updated.
        :type table: Table
        :param rows: The list of rows with new values that should be set.
        :type rows: list
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :type model: Model
        :raises RowIdsNotUnique: When trying to update the same row multiple times.
        :raises RowDoesNotExist: When any of the rows don't exist.
        :return: The updated row instances.
        :rtype: list[Model]
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if not model:
            model = table.get_model()

        rows = self.prepare_rows_in_bulk(model._field_objects, rows)
        row_ids = [row["id"] for row in rows]

        non_unique_ids = get_non_unique_values(row_ids)
        if len(non_unique_ids) > 0:
            raise RowIdsNotUnique(non_unique_ids)

        rows_by_id = {}
        for row in rows:
            row_id = row.pop("id")
            rows_by_id[row_id] = row

        rows_to_update = model.objects.select_for_update().filter(id__in=row_ids)

        if len(rows_to_update) != len(rows):
            db_rows_ids = [db_row.id for db_row in rows_to_update]
            raise RowDoesNotExist(sorted(list(set(row_ids) - set(db_rows_ids))))

        updated_field_ids = set()
        for obj in rows_to_update:
            row_values = rows_by_id[obj.id]
            for field_id, field in model._field_objects.items():
                if field_id in row_values or field["name"] in row_values:
                    updated_field_ids.add(field_id)

        before_return = before_row_update.send(
            self,
            row=list(rows_to_update),
            user=user,
            table=table,
            model=model,
            updated_field_ids=updated_field_ids,
        )

        for obj in rows_to_update:
            row_values = rows_by_id[obj.id]
            values, manytomany_values = self.extract_manytomany_values(
                row_values, model
            )

            for name, value in values.items():
                setattr(obj, name, value)

            for name, value in manytomany_values.items():
                getattr(obj, name).set(value)

            fields_with_pre_save = model.fields_requiring_refresh_after_update()
            for field_name in fields_with_pre_save:
                setattr(
                    obj,
                    field_name,
                    model._meta.get_field(field_name).pre_save(obj, add=False),
                )

        # For now all fields that don't represent a relationship will be used in
        # the bulk_update() call. This could be optimized in the future if we can
        # select just fields that need to be updated (fields that are passed in +
        # read only fields that need updating too)
        bulk_update_fields = [
            field["name"]
            for field in model._field_objects.values()
            if not isinstance(model._meta.get_field(field["name"]), ManyToManyField)
        ]
        if len(bulk_update_fields) > 0:
            model.objects.bulk_update(rows_to_update, bulk_update_fields)

        updated_fields = [field["field"] for field in model._field_objects.values()]
        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=row_ids, existing_model=model
        )
        for field in updated_fields:
            for (
                dependant_field,
                dependant_field_type,
                path_to_starting_table,
            ) in field.dependant_fields_with_types(update_collector):
                dependant_field_type.row_of_dependency_updated(
                    dependant_field,
                    rows_to_update[0],
                    update_collector,
                    path_to_starting_table,
                )
        update_collector.apply_updates_and_get_updated_fields()

        rows_to_return = list(
            model.objects.all().enhance_by_fields().filter(id__in=row_ids)
        )
        rows_updated.send(
            self,
            rows=rows_to_return,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
            updated_field_ids=updated_field_ids,
        )

        return rows_to_return

    def move_row(self, user, table, row_id, before=None, model=None):
        """
        Moves the row related to the row_id before another row or to the end if no
        before row is provided. This moving is done by updating the `order` value of
        the order.

        :param user: The user of whose behalf the row is moved
        :type user: User
        :param table: The table that contains the row that needs to be moved.
        :type table: Table
        :param row_id: The row id that needs to be moved.
        :type row_id: int
        :param before: If provided the new row will be placed right before that row
            instance. Otherwise the row will be moved to the end.
        :type before: Table
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        :type model: Model
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if not model:
            model = table.get_model()

        try:
            row = model.objects.select_for_update().get(id=row_id)
        except model.DoesNotExist:
            raise RowDoesNotExist(row_id)

        before_return = before_row_update.send(
            self, row=row, user=user, table=table, model=model, updated_field_ids=[]
        )

        row.order = self.get_order_before_row(before, model)
        row.save()

        updated_fields = [
            field["field"] for field_id, field in model._field_objects.items()
        ]
        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=row.id, existing_model=model
        )
        for field in updated_fields:
            for (
                dependant_field,
                dependant_field_type,
                path_to_starting_table,
            ) in field.dependant_fields_with_types(update_collector):
                dependant_field_type.row_of_dependency_moved(
                    dependant_field, row, update_collector, path_to_starting_table
                )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        ViewHandler().field_value_updated(updated_fields)

        row_updated.send(
            self,
            row=row,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
            updated_field_ids=[],
        )

        return row

    def delete_row(self, user, table, row_id, model=None):
        """
        Deletes an existing row of the given table and with row_id.

        :param user: The user of whose behalf the change is made.
        :type user: User
        :param table: The table for which the row must be deleted.
        :type table: Table
        :param row_id: The id of the row that must be deleted.
        :type row_id: int
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if not model:
            model = table.get_model()

        try:
            row = model.objects.get(id=row_id)
        except model.DoesNotExist:
            raise RowDoesNotExist(row_id)

        before_return = before_row_delete.send(
            self, row=row, user=user, table=table, model=model
        )

        row_id = row.id

        TrashHandler.trash(user, group, table.database, row, parent_id=table.id)
        updated_fields = [field["field"] for field in model._field_objects.values()]
        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=row.id, existing_model=model
        )
        for field in updated_fields:
            for (
                dependant_field,
                dependant_field_type,
                path_to_starting_table,
            ) in field.dependant_fields_with_types(update_collector):
                dependant_field_type.row_of_dependency_deleted(
                    dependant_field, row, update_collector, path_to_starting_table
                )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        ViewHandler().field_value_updated(updated_fields)

        row_deleted.send(
            self,
            row_id=row_id,
            row=row,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
        )
