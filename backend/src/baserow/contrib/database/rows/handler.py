import re
from collections import defaultdict
from decimal import Decimal
from math import floor, ceil
from typing import cast, Any, Dict, List, NewType, Optional, Type

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Max, F, QuerySet
from django.db.models.fields.related import ManyToManyField, ForeignKey

from baserow.contrib.database.table.models import Table, GeneratedTableModel
from baserow.core.trash.handler import TrashHandler
from baserow.contrib.database.trash.models import TrashedRows
from .exceptions import RowDoesNotExist, RowIdsNotUnique
from .signals import (
    before_row_update,
    before_row_delete,
    before_rows_update,
    before_rows_delete,
    row_created,
    rows_created,
    row_updated,
    rows_updated,
    row_deleted,
    rows_deleted,
)
from baserow.contrib.database.fields.dependencies.update_collector import (
    CachingFieldUpdateCollector,
)
from baserow.contrib.database.fields.dependencies.handler import FieldDependencyHandler
from baserow.core.utils import get_non_unique_values


GeneratedTableModelForUpdate = NewType(
    "GeneratedTableModelForUpdate", GeneratedTableModel
)

RowsForUpdate = NewType("RowsForUpdate", QuerySet)


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

    def extract_field_ids_from_keys(self, keys: List[str]) -> List[int]:
        """
        Extracts the field ids from a list of field names.
        For example keys like 'field_2', '3', 4 will be seen ass field ids.

        :param keys: The list of field names.
        :return: A list containing the field ids as integers.
        """

        field_pattern = re.compile("^field_([0-9]+)$")
        # @TODO improve this function
        return [
            int(re.sub("[^0-9]", "", str(key)))
            for key in keys
            if str(key).isnumeric() or field_pattern.match(str(key))
        ]

    def extract_field_ids_from_dict(self, values: Dict[str, Any]) -> List[int]:
        """
        Extracts the field ids from a dict containing the values that need to
        updated. For example keys like 'field_2', '3', 4 will be seen ass field ids.

        :param values: The values where to extract the fields ids from.
        :return: A list containing the field ids as integers.
        """

        return self.extract_field_ids_from_keys(values.keys())

    def get_internal_values_for_fields(
        self,
        row: GeneratedTableModel,
        fields_keys: List[str],
    ) -> Dict[str, Any]:
        """
        Gets the current values of the row before the update.

        :param row: The row instance.
        :param fields_keys: The fields keys that need to be exported.
        :return: The current values of the row before the update.
        """

        values = {}
        for field_id in self.extract_field_ids_from_keys(fields_keys):
            field = row._field_objects[field_id]
            field_type = field["type"]
            if field_type.read_only:
                continue
            field_name = f"field_{field_id}"
            field_value = field_type.get_internal_value_from_db(row, field_name)
            values[field_name] = field_value
        return values

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

    def get_order_before_row(self, before, model, amount=1):
        """
        Calculates a new unique order lower than the provided before row
        order and a step representing the change needed between multiple rows if
        multiple rows are being placed at once.
        This order can be used by existing or new rows. Several other rows
        could be updated as their order might need to change.

        :param before: The row instance where the before order must be calculated for.
        :type before: Table
        :param model: The model of the related table
        :type model: Model
        :param amount: The number of rows being placed.
        :type amount: int
        :return: The order for the last inserted row and the
            step (change) that should be used between all new rows.
        :rtype: tuple(Decimal, Decimal)
        """

        if before:
            # When the rows are being inserted before an existing row, the order
            # of the last new row is calculated by subtracting a fraction of
            # the "before" row order.
            # The same fraction is also going to be subtracted from the other
            # rows that have been placed before. By using these fractions we don't
            # have to re-order every row in the table.
            step = Decimal("0.00000000000000000001")
            order_last_row = before.order - step
            model.objects.filter(
                order__gt=floor(order_last_row), order__lte=order_last_row
            ).update(order=F("order") - (step * amount))
        else:
            # Because the rows are by default added as last, we have to figure out
            # what the highest order in the table is currently and increase that by
            # the number of rows being inserted.
            # The order of new rows should always be a whole number so the number is
            # rounded up.
            step = Decimal("1.00000000000000000000")
            order_last_row = ceil(
                model.objects.aggregate(max=Max("order")).get("max") or Decimal("0")
            ) + (step * amount)

        return order_last_row, step

    def get_row(
        self,
        user: AbstractUser,
        table: Table,
        row_id: int,
        model: Optional[Type[GeneratedTableModel]] = None,
        base_queryset: Optional[QuerySet] = None,
    ) -> GeneratedTableModel:
        """
        Fetches a single row from the provided table.

        :param user: The user of whose behalf the row is requested.
        :param table: The table where the row must be fetched from.
        :param row_id: The id of the row that must be fetched.
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        :return: The requested row instance.
        """

        if model is None:
            model = table.get_model()

        if base_queryset is None:
            base_queryset = model.objects

        group = table.database.group
        group.has_user(user, raise_error=True)

        try:
            row = base_queryset.get(id=row_id)
        except model.DoesNotExist:
            raise RowDoesNotExist(f"The row with id {row_id} does not exist.")

        return row

    def get_row_for_update(
        self,
        user: AbstractUser,
        table: Table,
        row_id: int,
        enhance_by_fields: bool = False,
        model: Optional[Type[GeneratedTableModel]] = None,
    ) -> GeneratedTableModelForUpdate:
        """
        Fetches a single row from the provided table and lock it for update.

        :param user: The user of whose behalf the row is requested.
        :param table: The table where the row must be fetched from.
        :param row_id: The id of the row that must be fetched.
        :param enhance_by_fields: Enhances the queryset based on the
            `enhance_queryset` for each field in the table.
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        :return: The requested row instance.
        """

        if model is None:
            model = table.get_model()

        base_queryset = model.objects.select_for_update(of=("self",))
        if enhance_by_fields:
            base_queryset = base_queryset.enhance_by_fields()

        row = self.get_row(
            user,
            table,
            row_id,
            model=model,
            base_queryset=base_queryset,
        )

        return cast(GeneratedTableModelForUpdate, row)

    def get_row_names(
        self, table: "Table", row_ids: List[int], model: "GeneratedTableModel" = None
    ) -> Dict[str, int]:
        """
        Returns the row names for all row ids specified in `row_ids` parameter from
        the given table.

        :param table: The table where the rows must be fetched from.
        :param row_ids: The id of the rows that must be fetched.
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :return: A dict of the requested rows names. The key are the row ids and the
            values are the row names.
        """

        if not model:
            primary_field = table.field_set.get(primary=True)
            model = table.get_model(
                field_ids=[], fields=[primary_field], add_dependencies=False
            )

        queryset = model.objects.filter(pk__in=row_ids)

        return {row.id: str(row) for row in queryset}

    # noinspection PyMethodMayBeStatic
    def has_row(self, user, table, row_id, raise_error=False, model=None):
        """
        Checks if a row with the given id exists and is not trashed in the table.

        This method is preferred over using get_row when you do not actually need to
        access any values of the row as it will not construct a full model but instead
        do a much more efficient query to check only if the row exists or not.

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

        if model is None:
            model = table.get_model(field_ids=[])

        group = table.database.group
        group.has_user(user, raise_error=True)

        row_exists = model.objects.filter(id=row_id).exists()
        if not row_exists and raise_error:
            raise RowDoesNotExist(row_id)
        else:
            return row_exists

    def create_row(
        self,
        user: AbstractUser,
        table: Table,
        values: Optional[Dict[str, Any]] = None,
        model: Optional[Type[GeneratedTableModel]] = None,
        before_row: Optional[GeneratedTableModel] = None,
        user_field_names: bool = False,
    ) -> GeneratedTableModel:
        """
        Creates a new row for a given table with the provided values if the user
        belongs to the related group. It also calls the row_created signal.

        :param user: The user of whose behalf the row is created.
        :param table: The table for which to create a row for.
        :param values: The values that must be set upon creating the row. The keys must
            be the field ids.
        :param model: If a model is already generated it can be provided here to avoid
            having to generate the model again.
        :param before_row: If provided the new row will be placed right before that row
            instance.
        :param user_field_names: Whether or not the values are keyed by the internal
            Baserow field name (field_1,field_2 etc) or by the user field names.
        :return: The created row instance.
        """

        if model is None:
            model = table.get_model()

        group = table.database.group
        group.has_user(user, raise_error=True)

        instance = self.force_create_row(
            table, values, model, before_row, user_field_names
        )

        row_created.send(
            self, row=instance, before=before_row, user=user, table=table, model=model
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

        if model is None:
            model = table.get_model()

        if user_field_names:
            values = self.map_user_field_name_dict_to_internal(
                model._field_objects, values
            )

        values = self.prepare_values(model._field_objects, values)
        values, manytomany_values = self.extract_manytomany_values(values, model)
        values["order"] = self.get_order_before_row(before, model)[0]
        instance = model.objects.create(**values)

        for name, value in manytomany_values.items():
            getattr(instance, name).set(value)

        fields = []
        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=instance.id, existing_model=model
        )
        field_ids = []
        for field_object in model._field_objects.values():
            field_type = field_object["type"]
            field = field_object["field"]
            fields.append(field)
            field_ids.append(field.id)

            field_type.after_rows_created(
                field,
                [instance],
                update_collector,
            )

        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in FieldDependencyHandler.get_dependant_fields_with_type(
            field_ids, update_collector
        ):
            dependant_field_type.row_of_dependency_created(
                dependant_field, instance, update_collector, path_to_starting_table
            )
        update_collector.apply_updates_and_get_updated_fields()

        if model.fields_requiring_refresh_after_insert():
            instance.refresh_from_db(
                fields=model.fields_requiring_refresh_after_insert()
            )

        from baserow.contrib.database.views.handler import ViewHandler

        ViewHandler().field_value_updated(fields)

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

    def update_row_by_id(
        self,
        user: AbstractUser,
        table: Table,
        row_id: int,
        values: Dict[str, Any],
        model: Optional[Type[GeneratedTableModel]] = None,
        user_field_names: bool = False,
    ) -> GeneratedTableModelForUpdate:
        """
        Updates one or more values of the provided row_id.

        :param user: The user of whose behalf the change is made.
        :param table: The table for which the row must be updated.
        :param row_id: The id of the row that must be updated.
        :param values: The values that must be updated. The keys must be the field ids.
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :param user_field_names: Whether or not the values are keyed by the internal
            Baserow field name (field_1,field_2 etc) or by the user field names.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        :return: The updated row instance.
        """

        if model is None:
            model = table.get_model()

        with transaction.atomic():
            row = self.get_row_for_update(
                user, table, row_id, enhance_by_fields=True, model=model
            )
            return self.update_row(user, table, row, values, model=model)

    def update_row(
        self,
        user: AbstractUser,
        table: Table,
        row: GeneratedTableModelForUpdate,
        values: Dict[str, Any],
        model: Optional[Type[GeneratedTableModel]] = None,
    ) -> GeneratedTableModelForUpdate:
        """
        Updates one or more values of the provided row_id.

        :param user: The user of whose behalf the change is made.
        :param table: The table for which the row must be updated.
        :param row: The the row that must be updated.
        :param values: The values that must be updated. The keys must be the field ids.
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        :return: The updated row instance.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if model is None:
            model = table.get_model()

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
        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in FieldDependencyHandler.get_dependant_fields_with_type(
            updated_field_ids, update_collector
        ):
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

    def create_rows(
        self,
        user: AbstractUser,
        table: Table,
        rows_values: List[Dict[str, Any]],
        before_row: Optional[GeneratedTableModel] = None,
        model: Optional[Type[GeneratedTableModel]] = None,
    ) -> List[GeneratedTableModel]:
        """
        Creates new rows for a given table if the user
        belongs to the related group. It also calls the rows_created signal.

        :param user: The user of whose behalf the rows are created.
        :param table: The table for which the rows should be created.
        :param rows_values: List of rows values for rows that need to be created.
        :param before_row: If provided the new rows will be placed right before
            the before_row.
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :return: The created row instances.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if model is None:
            model = table.get_model()

        highest_order, step = self.get_order_before_row(
            before_row, model, amount=len(rows_values)
        )

        rows = self.prepare_rows_in_bulk(model._field_objects, rows_values)

        rows_relationships = []
        for index, row in enumerate(rows, start=-len(rows)):
            values, manytomany_values = self.extract_manytomany_values(row, model)
            values["order"] = highest_order - (step * (abs(index + 1)))
            instance = model(**values)
            relations = {
                field_name: value
                for field_name, value in manytomany_values.items()
                if value and len(value) > 0
            }
            rows_relationships.append((instance, relations))

        inserted_rows = model.objects.bulk_create(
            [row for (row, relations) in rows_relationships]
        )

        many_to_many = defaultdict(list)
        for index, row in enumerate(inserted_rows):
            manytomany_values = rows_relationships[index][1]
            for field_name, value in manytomany_values.items():
                through = getattr(model, field_name).through
                through_fields = through._meta.get_fields()
                value_column = None
                row_column = None

                # Figure out which field in the many to many through table holds the row
                # value and which on contains the value.
                for field in through_fields:
                    if type(field) is not ForeignKey:
                        continue

                    if field.remote_field.model == model:
                        row_column = field.get_attname_column()[1]
                    else:
                        value_column = field.get_attname_column()[1]

                for i in value:
                    many_to_many[field_name].append(
                        getattr(model, field_name).through(
                            **{
                                row_column: row.id,
                                value_column: i,
                            }
                        )
                    )

        for field_name, values in many_to_many.items():
            through = getattr(model, field_name).through
            through.objects.bulk_create(values)

        update_collector = CachingFieldUpdateCollector(
            table,
            starting_row_id=[row.id for row in inserted_rows],
            existing_model=model,
        )
        field_ids = []
        for field_object in model._field_objects.values():
            field_type = field_object["type"]
            field = field_object["field"]
            field_ids.append(field.id)

            field_type.after_rows_created(
                field,
                inserted_rows,
                update_collector,
            )

        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in FieldDependencyHandler.get_dependant_fields_with_type(
            field_ids, update_collector
        ):
            dependant_field_type.row_of_dependency_created(
                dependant_field,
                inserted_rows,
                update_collector,
                path_to_starting_table,
            )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        updated_fields = [o["field"] for o in model._field_objects.values()]
        ViewHandler().field_value_updated(updated_fields)

        rows_to_return = list(
            model.objects.all()
            .enhance_by_fields()
            .filter(id__in=[row.id for row in inserted_rows])
        )

        rows_created.send(
            self,
            rows=rows_to_return,
            before=before_row,
            user=user,
            table=table,
            model=model,
        )

        return rows_to_return

    def update_rows(
        self,
        user: AbstractUser,
        table: Table,
        rows: List,
        model: Optional[Type[GeneratedTableModel]] = None,
        rows_to_update: Optional[RowsForUpdate] = None,
    ) -> List[GeneratedTableModelForUpdate]:
        """
        Updates field values in batch based on provided rows with the new values.

        :param user: The user of whose behalf the change is made.
        :param table: The table for which the row must be updated.
        :param rows: The list of rows with new values that should be set.
        :param model: If the correct model has already been generated it can be
            provided so that it does not have to be generated for a second time.
        :param rows_to_update: If the rows to update have already been generated
            it can be provided so that it does not have to be generated for a
            second time.
        :raises RowIdsNotUnique: When trying to update the same row multiple times.
        :raises RowDoesNotExist: When any of the rows don't exist.
        :return: The updated row instances.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if model is None:
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

        if rows_to_update is None:
            rows_to_update = self.get_rows_for_update(model, row_ids)

        if len(rows_to_update) != len(rows):
            db_rows_ids = [db_row.id for db_row in rows_to_update]
            raise RowDoesNotExist(sorted(list(set(row_ids) - set(db_rows_ids))))

        updated_field_ids = set()
        for obj in rows_to_update:
            row_values = rows_by_id[obj.id]
            for field_id, field in model._field_objects.items():
                if field_id in row_values or field["name"] in row_values:
                    updated_field_ids.add(field_id)

        before_return = before_rows_update.send(
            self,
            rows=list(rows_to_update),
            user=user,
            table=table,
            model=model,
            updated_field_ids=updated_field_ids,
        )

        rows_relationships = []
        for obj in rows_to_update:
            # The `updated_on` field is not updated with `bulk_update`,
            # so we manually set the value here.
            obj.updated_on = model._meta.get_field("updated_on").pre_save(
                obj, add=False
            )
            row_values = rows_by_id[obj.id]
            values, manytomany_values = self.extract_manytomany_values(
                row_values, model
            )

            for name, value in values.items():
                setattr(obj, name, value)

            relations = {
                field_name: value
                for field_name, value in manytomany_values.items()
                if value or isinstance(value, list)
            }
            rows_relationships.append(relations)

            fields_with_pre_save = model.fields_requiring_refresh_after_update()
            for field_name in fields_with_pre_save:
                setattr(
                    obj,
                    field_name,
                    model._meta.get_field(field_name).pre_save(obj, add=False),
                )

        many_to_many = defaultdict(list)
        row_column_name = None
        row_ids_change_m2m_per_field = defaultdict(set)
        for index, row in enumerate(rows_to_update):
            manytomany_values = rows_relationships[index]
            for field_name, value in manytomany_values.items():
                through = getattr(model, field_name).through
                through_fields = through._meta.get_fields()
                value_column = None
                row_column = None

                # Figure out which field in the many to many through table holds the row
                # value and which one contains the value.
                for field in through_fields:
                    if type(field) is not ForeignKey:
                        continue

                    row_ids_change_m2m_per_field[field_name].add(row.id)

                    if field.remote_field.model == model:
                        row_column = field.get_attname_column()[1]
                        row_column_name = row_column
                    else:
                        value_column = field.get_attname_column()[1]

                if len(value) == 0:
                    many_to_many[field_name].append(None)
                else:
                    for i in value:
                        many_to_many[field_name].append(
                            getattr(model, field_name).through(
                                **{
                                    row_column: row.id,
                                    value_column: i,
                                }
                            )
                        )

        # The many to many relations need to be updated first because they need to
        # exist when the rows are updated in bulk. Otherwise, the formula and lookup
        # fields can't see the relations.
        for field_name, values in many_to_many.items():
            through = getattr(model, field_name).through
            filter = {
                f"{row_column_name}__in": row_ids_change_m2m_per_field[field_name]
            }
            delete_qs = through.objects.all().filter(**filter)
            delete_qs._raw_delete(delete_qs.db)
            through.objects.bulk_create([v for v in values if v is not None])

        # For now all fields that don't represent a relationship will be used in
        # the bulk_update() call. This could be optimized in the future if we can
        # select just fields that need to be updated (fields that are passed in +
        # read only fields that need updating too)
        bulk_update_fields = [
            field["name"]
            for field in model._field_objects.values()
            if not isinstance(model._meta.get_field(field["name"]), ManyToManyField)
        ] + ["updated_on"]
        if len(bulk_update_fields) > 0:
            model.objects.bulk_update(rows_to_update, bulk_update_fields)

        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=row_ids, existing_model=model
        )
        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in FieldDependencyHandler.get_dependant_fields_with_type(
            updated_field_ids, update_collector
        ):
            dependant_field_type.row_of_dependency_updated(
                dependant_field,
                rows_to_update,
                update_collector,
                path_to_starting_table,
            )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        updated_fields = [o["field"] for o in model._field_objects.values()]
        ViewHandler().field_value_updated(updated_fields)

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

    def get_rows_for_update(
        self, model: GeneratedTableModel, row_ids: List[int]
    ) -> RowsForUpdate:
        """
        Get the rows to update.
        """

        return cast(
            RowsForUpdate,
            model.objects.select_for_update(of=("self",))
            .enhance_by_fields()
            .filter(id__in=row_ids),
        )

    def move_row_by_id(
        self,
        user: AbstractUser,
        table: Table,
        row_id: int,
        before_row: Optional[GeneratedTableModel] = None,
        model: Optional[Type[GeneratedTableModel]] = None,
    ) -> GeneratedTableModelForUpdate:
        """
        Updates the row order value.

        :param user: The user of whose behalf the row is moved
        :param table: The table that contains the row that needs to be moved.
        :param row_id: The row id that needs to be moved.
        :param before_row: If provided the new row will be placed right before that row
            instance. Otherwise the row will be moved to the end.
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        """

        if model is None:
            model = table.get_model()

        with transaction.atomic():
            row = self.get_row_for_update(user, table, row_id, model=model)
            return self.move_row(user, table, row, before_row=before_row, model=model)

    def move_row(
        self,
        user: AbstractUser,
        table: Table,
        row: GeneratedTableModelForUpdate,
        before_row: Optional[GeneratedTableModel] = None,
        model: Optional[Type[GeneratedTableModel]] = None,
    ) -> GeneratedTableModelForUpdate:
        """
        Updates the row order value.

        :param user: The user of whose behalf the row is moved
        :param table: The table that contains the row that needs to be moved.
        :param row: The row that needs to be moved.
        :param before_row: If provided the new row will be placed right before that row
            instance. Otherwise the row will be moved to the end.
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if model is None:
            model = table.get_model()

        before_return = before_row_update.send(
            self, row=row, user=user, table=table, model=model, updated_field_ids=[]
        )

        row.order = self.get_order_before_row(before_row, model)[0]
        row.save()

        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=row.id, existing_model=model
        )
        updated_field_ids = [field_id for field_id in model._field_objects.keys()]
        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in FieldDependencyHandler.get_dependant_fields_with_type(
            updated_field_ids, update_collector
        ):
            dependant_field_type.row_of_dependency_moved(
                dependant_field, row, update_collector, path_to_starting_table
            )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        updated_fields = [o["field"] for o in model._field_objects.values()]
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

    def delete_row_by_id(
        self,
        user: AbstractUser,
        table: Table,
        row_id: int,
        model: Optional[Type[GeneratedTableModel]] = None,
    ):
        """
        Deletes an existing row of the given table and with row_id.

        :param user: The user of whose behalf the change is made.
        :param table: The table for which the row must be deleted.
        :param row_id: The id of the row that must be deleted.
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        """

        if model is None:
            model = table.get_model()

        with transaction.atomic():
            row = self.get_row(user, table, row_id, model=model)
            self.delete_row(user, table, row, model=model)

    def delete_row(
        self,
        user: AbstractUser,
        table: Table,
        row: GeneratedTableModelForUpdate,
        model: Optional[Type[GeneratedTableModel]] = None,
    ):
        """
        Deletes an existing row of the given table and with row_id.

        :param user: The user of whose behalf the change is made.
        :param table: The table for which the row must be deleted.
        :param row: The row that must be deleted.
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if model is None:
            model = table.get_model()

        before_return = before_row_delete.send(
            self, row=row, user=user, table=table, model=model
        )

        row_id = row.id

        TrashHandler.trash(user, group, table.database, row, parent_id=table.id)

        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=row.id, existing_model=model
        )
        updated_field_ids = [field_id for field_id in model._field_objects.keys()]
        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in FieldDependencyHandler.get_dependant_fields_with_type(
            updated_field_ids, update_collector
        ):
            dependant_field_type.row_of_dependency_deleted(
                dependant_field, row, update_collector, path_to_starting_table
            )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        updated_fields = [o["field"] for o in model._field_objects.values()]
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

    def delete_rows(
        self,
        user: AbstractUser,
        table: Table,
        row_ids: List[int],
        model: Optional[Type[GeneratedTableModel]] = None,
    ) -> TrashedRows:
        """
        Trashes existing rows of the given table based on row_ids.

        :param user: The user of whose behalf the change is made.
        :param table: The table for which the row must be deleted.
        :param row_ids: The ids of the rows that must be deleted.
        :param model:
        :param model: If the correct model has already been generated, it can be
            provided so that it does not have to be generated for a second time.
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if not model:
            model = table.get_model()

        non_unique_ids = get_non_unique_values(row_ids)
        if len(non_unique_ids) > 0:
            raise RowIdsNotUnique(non_unique_ids)

        rows = list(model.objects.filter(id__in=row_ids).enhance_by_fields())

        if len(row_ids) != len(rows):
            db_rows_ids = [db_row.id for db_row in rows]
            raise RowDoesNotExist(sorted(list(set(row_ids) - set(db_rows_ids))))

        before_return = before_rows_delete.send(
            self, rows=rows, user=user, table=table, model=model
        )

        trashed_rows = TrashedRows()
        trashed_rows.row_ids = row_ids
        trashed_rows.table = table
        # It's a bit on a hack, but we're storing the fetched row objects on the
        # trashed_rows object, so that they can optionally be used later. This is for
        # example used when storing the names in the trash.
        trashed_rows.rows = rows

        TrashHandler.trash(
            user, group, table.database, trashed_rows, parent_id=table.id
        )

        updated_field_ids = [field_id for field_id in model._field_objects.keys()]
        update_collector = CachingFieldUpdateCollector(
            table, starting_row_id=row_ids, existing_model=model
        )
        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in FieldDependencyHandler.get_dependant_fields_with_type(
            updated_field_ids, update_collector
        ):
            dependant_field_type.row_of_dependency_deleted(
                dependant_field, rows, update_collector, path_to_starting_table
            )
        update_collector.apply_updates_and_get_updated_fields()

        from baserow.contrib.database.views.handler import ViewHandler

        updated_fields = [o["field"] for o in model._field_objects.values()]
        ViewHandler().field_value_updated(updated_fields)

        rows_deleted.send(
            self,
            rows=rows,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
        )

        return trashed_rows
