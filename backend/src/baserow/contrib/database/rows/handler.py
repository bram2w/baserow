from django.db import transaction
import re
from decimal import Decimal
from math import floor, ceil

from django.db.models import Max, F
from django.db.models.fields.related import ManyToManyField

from baserow.contrib.database.fields.models import Field
from baserow.core.trash.handler import TrashHandler

from baserow.core.utils import split_comma_separated_string
from .exceptions import RowDoesNotExist
from .signals import (
    before_row_update,
    before_row_delete,
    row_created,
    row_updated,
    row_deleted,
)


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

    def extract_field_ids_from_dict(self, values):
        """
        Extracts the field ids from a dict containing the values that need to
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

    def extract_field_ids_from_string(self, value):
        """
        Extracts the field ids from a string. Multiple ids can be separated by a comma.
        For example if you provide 'field_1,field_2' then [1, 2] is returned.

        :param value: A string containing multiple ids separated by comma.
        :type value: str
        :return: A list containing the field ids as integers.
        :rtype: list
        """

        if not value:
            return []

        return [
            int(re.sub("[^0-9]", "", str(v)))
            for v in value.split(",")
            if any(c.isdigit() for c in v)
        ]

    def get_include_exclude_fields(
        self, table, include=None, exclude=None, user_field_names=False
    ):
        """
        Returns a field queryset containing the requested fields based on the value
        and exclude parameter.

        :param table: The table where to select the fields from. Field id's that are
            not in the table won't be included.
        :type table: Table
        :param include: The field ids that must be included. Only the provided ones
            are going to be in the returned queryset. Multiple can be provided
            separated by comma
        :type include: Optional[str]
        :param exclude: The field ids that must be excluded. Only the ones that are not
            provided are going to be in the returned queryset. Multiple can be provided
            separated by comma.
        :type exclude: Optional[str]
        :return: A Field's QuerySet containing the allowed fields based on the provided
            input.
        :param user_field_names: If true then the value and exclude parameters are
            retreated as a comma separated list of user field names instead of id's
        :type user_field_names: bool
        :rtype: QuerySet
        """

        queryset = Field.objects.filter(table=table)

        if user_field_names:
            includes = self.extract_field_names_from_string(include)
            excludes = self.extract_field_names_from_string(exclude)
            filter_type = "name__in"
        else:
            includes = self.extract_field_ids_from_string(include)
            excludes = self.extract_field_ids_from_string(exclude)
            filter_type = "id__in"

        if len(includes) == 0 and len(excludes) == 0:
            return None

        if len(includes) > 0:
            queryset = queryset.filter(**{filter_type: includes})

        if len(excludes) > 0:
            queryset = queryset.exclude(**{filter_type: excludes})

        return queryset

    # noinspection PyMethodMayBeStatic
    def extract_field_names_from_string(self, value):
        """
        Given a comma separated string of field names this function will split the
        string into a list of individual field names. For weird field names containing
        commas etc the field should be escaped with quotes.
        :param value: The string to split into a list of field names.
        :return: A list of field names.
        """

        if not value:
            return []

        return split_comma_separated_string(value)

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
            raise RowDoesNotExist(f"The row with id {row_id} does not exist.")

        return row

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
                row = model.objects.select_for_update().get(id=row_id)
            except model.DoesNotExist:
                raise RowDoesNotExist(f"The row with id {row_id} does not exist.")

            before_return = before_row_update.send(
                self, row=row, user=user, table=table, model=model
            )
            if user_field_names:
                values = self.map_user_field_name_dict_to_internal(
                    model._field_objects, values
                )
            values = self.prepare_values(model._field_objects, values)
            values, manytomany_values = self.extract_manytomany_values(values, model)

            for name, value in values.items():
                setattr(row, name, value)

            row.save()

            for name, value in manytomany_values.items():
                getattr(row, name).set(value)

        row_updated.send(
            self,
            row=row,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
        )

        return row

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
            raise RowDoesNotExist(f"The row with id {row_id} does not exist.")

        before_return = before_row_update.send(
            self, row=row, user=user, table=table, model=model
        )

        row.order = self.get_order_before_row(before, model)
        row.save()

        row_updated.send(
            self,
            row=row,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
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
            raise RowDoesNotExist(f"The row with id {row_id} does not exist.")

        before_return = before_row_delete.send(
            self, row=row, user=user, table=table, model=model
        )

        row_id = row.id

        TrashHandler.trash(user, group, table.database, row, parent_id=table.id)

        row_deleted.send(
            self,
            row_id=row_id,
            row=row,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
        )
