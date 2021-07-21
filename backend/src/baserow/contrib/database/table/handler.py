from django.conf import settings
from django.db import connection

from baserow.contrib.database.fields.exceptions import (
    MaxFieldLimitExceeded,
    ReservedBaserowFieldNameException,
    InvalidBaserowFieldName,
)
from baserow.contrib.database.fields.field_types import (
    LongTextFieldType,
    BooleanFieldType,
)
from baserow.contrib.database.fields.handler import (
    FieldHandler,
    RESERVED_BASEROW_FIELD_NAMES,
)
from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.view_types import GridViewType
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import extract_allowed, set_allowed_attrs
from .exceptions import (
    TableDoesNotExist,
    TableNotInDatabase,
    InvalidInitialTableData,
    InitialTableDataLimitExceeded,
    InitialTableDataDuplicateName,
)
from .models import Table
from .signals import table_created, table_updated, table_deleted, tables_reordered


class TableHandler:
    def get_table(self, table_id, base_queryset=None):
        """
        Selects a table with a given id from the database.

        :param table_id: The identifier of the table that must be returned.
        :type table_id: int
        :param base_queryset: The base queryset from where to select the table
            object from. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises TableDoesNotExist: When the table with the provided id does not exist.
        :return: The requested table of the provided id.
        :rtype: Table
        """

        if not base_queryset:
            base_queryset = Table.objects

        try:
            table = base_queryset.select_related("database__group").get(id=table_id)
        except Table.DoesNotExist:
            raise TableDoesNotExist(f"The table with id {table_id} does not exist.")

        if TrashHandler.item_has_a_trashed_parent(table):
            raise TableDoesNotExist(f"The table with id {table_id} does not exist.")

        return table

    def create_table(
        self,
        user,
        database,
        fill_example=False,
        data=None,
        first_row_header=True,
        **kwargs,
    ):
        """
        Creates a new table and a primary text field.

        :param user: The user on whose behalf the table is created.
        :type user: User
        :param database: The database that the table instance belongs to.
        :type database: Database
        :param fill_example: Indicates whether an initial view, some fields and
            some rows should be added. Works only if no data is provided.
        :type fill_example: bool
        :param data: A list containing all the rows that need to be inserted is
            expected. All the values of the row are going to be converted to a string
            and will be inserted in the database.
        :type: initial_data: None or list[list[str]
        :param first_row_header: Indicates if the first row are the fields. The names
            of these rows are going to be used as fields.
        :type first_row_header: bool
        :param kwargs: The fields that need to be set upon creation.
        :type kwargs: object
        :raises MaxFieldLimitExceeded: When the data contains more columns
            than the field limit.
        :return: The created table instance.
        :rtype: Table
        """

        database.group.has_user(user, raise_error=True)

        if data is not None:
            fields, data = self.normalize_initial_table_data(data, first_row_header)
            if len(fields) > settings.MAX_FIELD_LIMIT:
                raise MaxFieldLimitExceeded(
                    f"Fields count exceeds the limit of {settings.MAX_FIELD_LIMIT}"
                )

        table_values = extract_allowed(kwargs, ["name"])
        last_order = Table.get_last_order(database)
        table = Table.objects.create(
            database=database, order=last_order, **table_values
        )

        if data is not None:
            # If the initial data has been provided we will create those fields before
            # creating the model so that we the whole table schema is created right
            # away.
            for index, name in enumerate(fields):
                fields[index] = TextField.objects.create(
                    table=table, order=index, primary=index == 0, name=name
                )

        else:
            # If no initial data is provided we want to create a primary text field for
            # the table.
            TextField.objects.create(table=table, order=0, primary=True, name="Name")

        # Create the table schema in the database database.
        with connection.schema_editor() as schema_editor:
            model = table.get_model()
            schema_editor.create_model(model)

        if data is not None:
            self.fill_initial_table_data(user, table, fields, data, model)
        elif fill_example:
            self.fill_example_table_data(user, table)

        table_created.send(self, table=table, user=user)

        return table

    def normalize_initial_table_data(self, data, first_row_header):
        """
        Normalizes the provided initial table data. The amount of columns will be made
        equal for each row. The header and the rows will also be separated.

        :param data: A list containing all the provided rows.
        :type data: list
        :param first_row_header: Indicates if the first row is the header. For each
            of these header columns a field is going to be created.
        :type first_row_header: bool
        :return: A list containing the field names and a list containing all the rows.
        :rtype: list, list
        :raises InvalidInitialTableData: When the data doesn't contain a column or row.
        """

        if len(data) == 0:
            raise InvalidInitialTableData("At least one row should be provided.")

        limit = settings.INITIAL_TABLE_DATA_LIMIT
        if limit and len(data) > limit:
            raise InitialTableDataLimitExceeded(
                f"It is not possible to import more than "
                f"{settings.INITIAL_TABLE_DATA_LIMIT} rows when creating a table."
            )

        largest_column_count = len(max(data, key=len))

        if largest_column_count == 0:
            raise InvalidInitialTableData("At least one column should be provided.")

        fields = data.pop(0) if first_row_header else []

        for i in range(len(fields), largest_column_count):
            fields.append(f"Field {i + 1}")

        # Stripping whitespace from field names is already done by
        # TableCreateSerializer  however we repeat to ensure that non API usages of
        # this method is consistent with api usage.
        field_name_set = {name.strip() for name in fields}

        if len(field_name_set) != len(fields):
            raise InitialTableDataDuplicateName()

        if len(field_name_set.intersection(RESERVED_BASEROW_FIELD_NAMES)) > 0:
            raise ReservedBaserowFieldNameException()

        if "" in field_name_set:
            raise InvalidBaserowFieldName()

        for row in data:
            for i in range(len(row), largest_column_count):
                row.append("")

        return fields, data

    def fill_initial_table_data(self, user, table, fields, data, model):
        """
        Fills the provided table with the normalized data that needs to be created upon
        creation of the table.

        :param user: The user on whose behalf the table is created.
        :type user: User`
        :param table: The newly created table where the initial data has to be inserted
            into.
        :type table: Table
        :param fields: A list containing the field names.
        :type fields: list
        :param data: A list containing the rows that need to be inserted.
        :type data: list
        :param model: The generated table model of the table that needs to be filled
            with initial data.
        :type model: TableModel
        """

        ViewHandler().create_view(user, table, GridViewType.type, name="Grid")

        bulk_data = [
            model(
                order=index + 1,
                **{
                    f"field_{fields[index].id}": str(value)
                    for index, value in enumerate(row)
                },
            )
            for index, row in enumerate(data)
        ]
        model.objects.bulk_create(bulk_data)

    def fill_example_table_data(self, user, table):
        """
        Fills the table with some initial example data. A new table is expected that
        already has the primary field named 'name'.

        :param user: The user on whose behalf the table is filled.
        :type: user: User
        :param table: The table that needs the initial data.
        :type table: User
        """

        view_handler = ViewHandler()
        field_handler = FieldHandler()

        view = view_handler.create_view(user, table, GridViewType.type, name="Grid")
        notes = field_handler.create_field(
            user, table, LongTextFieldType.type, name="Notes"
        )
        active = field_handler.create_field(
            user, table, BooleanFieldType.type, name="Active"
        )

        field_options = {notes.id: {"width": 400}, active.id: {"width": 100}}
        fields = [notes, active]
        view_handler.update_field_options(user, view, field_options, fields=fields)

        model = table.get_model(attribute_names=True)
        model.objects.create(name="Tesla", active=True, order=1)
        model.objects.create(name="Amazon", active=False, order=2)

    def update_table(self, user, table, **kwargs):
        """
        Updates an existing table instance.

        :param user: The user on whose behalf the table is updated.
        :type user: User
        :param table: The table instance that needs to be updated.
        :type table: Table
        :param kwargs: The fields that need to be updated.
        :type kwargs: object
        :raises ValueError: When the provided table is not an instance of Table.
        :return: The updated table instance.
        :rtype: Table
        """

        if not isinstance(table, Table):
            raise ValueError("The table is not an instance of Table")

        table.database.group.has_user(user, raise_error=True)

        table = set_allowed_attrs(kwargs, ["name"], table)
        table.save()

        table_updated.send(self, table=table, user=user)

        return table

    def order_tables(self, user, database, order):
        """
        Updates the order of the tables in the given database. The order of the views
        that are not in the `order` parameter set set to `0`.

        :param user: The user on whose behalf the tables are ordered.
        :type user: User
        :param database: The database of which the views must be updated.
        :type database: Database
        :param order: A list containing the table ids in the desired order.
        :type order: list
        :raises TableNotInDatabase: If one of the table ids in the order does not belong
            to the database.
        """

        group = database.group
        group.has_user(user, raise_error=True)

        queryset = Table.objects.filter(database_id=database.id)
        table_ids = [table["id"] for table in queryset.values("id")]

        for table_id in order:
            if table_id not in table_ids:
                raise TableNotInDatabase(table_id)

        Table.order_objects(queryset, order)
        tables_reordered.send(self, database=database, order=order, user=user)

    def delete_table(self, user, table):
        """
        Deletes an existing table instance if the user has access to the related group.
        The table deleted signals are also fired.

        :param user: The user on whose behalf the table is deleted.
        :type user: User
        :param table: The table instance that needs to be deleted.
        :type table: Table
        :raises ValueError: When the provided table is not an instance of Table.
        """

        if not isinstance(table, Table):
            raise ValueError("The table is not an instance of Table")

        table.database.group.has_user(user, raise_error=True)
        table_id = table.id

        TrashHandler.trash(user, table.database.group, table.database, table)

        table_deleted.send(self, table_id=table_id, table=table, user=user)
