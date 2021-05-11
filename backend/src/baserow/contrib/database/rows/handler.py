import re
from math import floor, ceil
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, F, Q
from django.db.models.fields.related import ManyToManyField
from django.conf import settings

from baserow.contrib.database.fields.models import Field

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

    def get_include_exclude_fields(self, table, include=None, exclude=None):
        """
        Returns a field queryset containing the requested fields based on the include
        and exclude parameter.

        :param table: The table where to select the fields from. Field id's that are
            not in the table won't be included.
        :type table: Table
        :param include: The field ids that must be included. Only the provided ones
            are going to be in the returned queryset. Multiple can be provided
            separated by comma
        :type include: str
        :param exclude: The field ids that must be excluded. Only the ones that are not
            provided are going to be in the returned queryset. Multiple can be provided
            separated by comma.
        :type exclude: str
        :return: A Field's QuerySet containing the allowed fields based on the provided
            input.
        :rtype: QuerySet
        """

        queryset = Field.objects.filter(table=table)
        include_ids = self.extract_field_ids_from_string(include)
        exclude_ids = self.extract_field_ids_from_string(exclude)

        if len(include_ids) == 0 and len(exclude_ids) == 0:
            return None

        if len(include_ids) > 0:
            queryset = queryset.filter(id__in=include_ids)

        if len(exclude_ids) > 0:
            queryset = queryset.filter(~Q(id__in=exclude_ids))

        return queryset

    def extract_manytomany_values(self, values, model):
        """
        Extracts the ManyToMany values out of the values because they need to be
        created and updated in a different way compared to a regular value.

        :param values: The values where to extract the manytomany values from.
        :type values: dict
        :param model: The model containing the fields. They key, which is also the
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

    def create_row(self, user, table, values=None, model=None, before=None):
        """
        Creates a new row for a given table with the provided values.

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
        :return: The created row instance.
        :rtype: Model
        """

        if not values:
            values = {}

        group = table.database.group
        group.has_user(user, raise_error=True)

        if not model:
            model = table.get_model()

        values = self.prepare_values(model._field_objects, values)
        values, manytomany_values = self.extract_manytomany_values(values, model)
        values["order"] = self.get_order_before_row(before, model)
        instance = model.objects.create(**values)

        for name, value in manytomany_values.items():
            getattr(instance, name).set(value)

        row_created.send(
            self, row=instance, before=before, user=user, table=table, model=model
        )

        return instance

    def update_row(self, user, table, row_id, values, model=None):
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
        :raises RowDoesNotExist: When the row with the provided id does not exist.
        :return: The updated row instance.
        :rtype: Model
        """

        group = table.database.group
        group.has_user(user, raise_error=True)

        if not model:
            model = table.get_model()

        # Because it is possible to have a different database for the user tables we
        # need to start another transaction here, otherwise it is not possible to use
        # the select_for_update function.
        with transaction.atomic(settings.USER_TABLE_DATABASE):
            try:
                row = model.objects.select_for_update().get(id=row_id)
            except model.DoesNotExist:
                raise RowDoesNotExist(f"The row with id {row_id} does not exist.")

            before_return = before_row_update.send(
                self, row=row, user=user, table=table, model=model
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

        # Because it is possible to have a different database for the user tables we
        # need to start another transaction here, otherwise it is not possible to use
        # the select_for_update function.
        with transaction.atomic(settings.USER_TABLE_DATABASE):
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
        row.delete()

        row_deleted.send(
            self,
            row_id=row_id,
            row=row,
            user=user,
            table=table,
            model=model,
            before_return=before_return,
        )
