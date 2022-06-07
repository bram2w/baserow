from typing import Any, cast, NewType, List, Tuple, Optional, Type

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.utils import timezone

from baserow.contrib.database.fields.constants import RESERVED_BASEROW_FIELD_NAMES
from baserow.contrib.database.fields.exceptions import (
    MaxFieldLimitExceeded,
    MaxFieldNameLengthExceeded,
    ReservedBaserowFieldNameException,
    InvalidBaserowFieldName,
)
from baserow.contrib.database.fields.field_types import (
    LongTextFieldType,
    BooleanFieldType,
)
from baserow.contrib.database.fields.handler import (
    FieldHandler,
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.models import Database
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.view_types import GridViewType
from baserow.core.trash.handler import TrashHandler
from baserow.contrib.database.db.schema import safe_django_schema_editor
from .exceptions import (
    TableDoesNotExist,
    TableNotInDatabase,
    InvalidInitialTableData,
    InitialTableDataLimitExceeded,
    InitialTableDataDuplicateName,
)
from .models import GeneratedTableModel, Table
from .signals import table_created, table_updated, table_deleted, tables_reordered


TableForUpdate = NewType("TableForUpdate", Table)


class TableHandler:
    def get_table(
        self, table_id: int, base_queryset: Optional[QuerySet] = None
    ) -> Table:
        """
        Selects a table with a given id from the database.

        :param table_id: The identifier of the table that must be returned.
        :param base_queryset: The base queryset from where to select the table
            object from. This can for example be used to do a `select_related`.
        :raises TableDoesNotExist: When the table with the provided id does not exist.
        :return: The requested table of the provided id.
        """

        if base_queryset is None:
            base_queryset = Table.objects

        try:
            table = base_queryset.select_related("database__group").get(id=table_id)
        except Table.DoesNotExist:
            raise TableDoesNotExist(f"The table with id {table_id} does not exist.")

        if TrashHandler.item_has_a_trashed_parent(table):
            raise TableDoesNotExist(f"The table with id {table_id} does not exist.")

        return table

    def get_table_for_update(self, table_id: int) -> TableForUpdate:
        """
        Provide a type hint for tables that need to be updated.
        :param table_id: The id of the table that needs to be updated.
        :return: The table that needs to be updated.
        """

        return cast(
            TableForUpdate,
            self.get_table(
                table_id, base_queryset=Table.objects.select_for_update(of=("self",))
            ),
        )

    def get_tables_order(self, database: Database) -> List[int]:
        """
        Returns the tables in the database ordered by the order field.

        :param database: The database that the tables belong to.
        :return: A list containing the order of the tables in the database.
        """

        return [table.id for table in database.table_set.order_by("order")]

    def create_table(
        self,
        user: AbstractUser,
        database: Database,
        name: str,
        fill_example: bool = False,
        data: Optional[List[List[str]]] = None,
        first_row_header: bool = True,
    ) -> Table:
        """
        Creates a new table and a primary text field.

        :param user: The user on whose behalf the table is created.
        :param database: The database that the table instance belongs to.
        :param name: The name of the table is created.
        :param fill_example: Indicates whether an initial view, some fields and
            some rows should be added. Works only if no data is provided.
        :param data: A list containing all the rows that need to be inserted is
            expected. All the values of the row are going to be converted to a string
            and will be inserted in the database.
        :param first_row_header: Indicates if the first row are the fields. The names
            of these rows are going to be used as fields.
        :raises MaxFieldLimitExceeded: When the data contains more columns
            than the field limit.
        :return: The created table instance.
        """

        database.group.has_user(user, raise_error=True)

        if data is not None:
            fields, data = self.normalize_initial_table_data(data, first_row_header)
            if len(fields) > settings.MAX_FIELD_LIMIT:
                raise MaxFieldLimitExceeded(
                    f"Fields count exceeds the limit of {settings.MAX_FIELD_LIMIT}"
                )

        last_order = Table.get_last_order(database)
        table = Table.objects.create(
            database=database,
            order=last_order,
            name=name,
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
        with safe_django_schema_editor() as schema_editor:
            # Django only creates indexes when the model is managed.
            model = table.get_model(managed=True)
            schema_editor.create_model(model)

        if data is not None:
            self.fill_initial_table_data(user, table, fields, data, model)
        elif fill_example:
            self.fill_example_table_data(user, table)

        table_created.send(self, table=table, user=user)

        return table

    def normalize_initial_table_data(
        self, data: List[List[str]], first_row_header: bool
    ) -> Tuple[List, List]:
        """
        Normalizes the provided initial table data. The amount of columns will be made
        equal for each row. The header and the rows will also be separated.

        :param data: A list containing all the provided rows.
        :param first_row_header: Indicates if the first row is the header. For each
            of these header columns a field is going to be created.
        :return: A list containing the field names and a list containing all the rows.
        :raises InvalidInitialTableData: When the data doesn't contain a column or row.
        :raises MaxFieldNameLengthExceeded: When the provided name is too long.
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

        max_field_name_length = Field.get_max_name_length()
        long_field_names = [x for x in field_name_set if len(x) > max_field_name_length]

        if len(long_field_names) > 0:
            raise MaxFieldNameLengthExceeded(max_field_name_length)

        if len(field_name_set.intersection(RESERVED_BASEROW_FIELD_NAMES)) > 0:
            raise ReservedBaserowFieldNameException()

        if "" in field_name_set:
            raise InvalidBaserowFieldName()

        for row in data:
            for i in range(len(row), largest_column_count):
                row.append("")

        return fields, data

    def fill_initial_table_data(
        self,
        user: AbstractUser,
        table: Table,
        fields: List[str],
        data: List[List[Any]],
        model: Type[GeneratedTableModel],
    ):
        """
        Fills the provided table with the normalized data that needs to be created upon
        creation of the table.

        :param user: The user on whose behalf the table is created.
        :param table: The newly created table where the initial data has to be inserted
            into.
        :param fields: A list containing the field names.
        :param data: A list containing the rows that need to be inserted.
        :param model: The generated table model of the table that needs to be filled
            with initial data.
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

    def fill_example_table_data(self, user: AbstractUser, table: Table):
        """
        Fills the table with some initial example data. A new table is expected that
        already has the primary field named 'name'.

        :param user: The user on whose behalf the table is filled.
        :param table: The table that needs the initial data.
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
        view_handler.update_field_options(
            user=user, view=view, field_options=field_options, fields=fields
        )

        model = table.get_model(attribute_names=True)
        model.objects.create(name="Tesla", active=True, order=1)
        model.objects.create(name="Amazon", active=False, order=2)

    def update_table_by_id(self, user: AbstractUser, table_id: int, name: str) -> Table:
        """
        Updates an existing table instance.

        :param user: The user on whose behalf the table is updated.
        :param table_id: The id of the table that needs to be updated.
        :param name: The name to be updated.
        :raises ValueError: When the provided table is not an instance of Table.
        :return: The updated table instance.
        """

        table = self.get_table_for_update(table_id)
        return self.update_table(user, table, name)

    def update_table(
        self, user: AbstractUser, table: TableForUpdate, name: str
    ) -> TableForUpdate:
        """
        Updates an existing table instance.

        :param user: The user on whose behalf the table is updated.
        :param table: The table instance that needs to be updated.
        :param name: The name to be updated.
        :raises ValueError: When the provided table is not an instance of Table.
        :return: The updated table instance.
        """

        if not isinstance(table, Table):
            raise ValueError("The table is not an instance of Table")

        table.database.group.has_user(user, raise_error=True)

        table.name = name
        table.save()

        table_updated.send(self, table=table, user=user)

        return table

    def order_tables(self, user: AbstractUser, database: Database, order: List[int]):
        """
        Updates the order of the tables in the given database. The order of the views
        that are not in the `order` parameter set set to `0`.

        :param user: The user on whose behalf the tables are ordered.
        :param database: The database of which the views must be updated.
        :param order: A list containing the table ids in the desired order.
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

    def delete_table_by_id(self, user: AbstractUser, table_id: int):
        """
        Moves to the trash an existing an existing table instance if the user
        has access to the related group.
        The table deleted signals are also fired.

        :param user: The user on whose behalf the table is deleted.
        :param table_id: The table id of the table that needs to be deleted.
        :raises ValueError: When the provided table is not an instance of Table.
        """

        table = self.get_table_for_update(table_id)
        self.delete_table(user, table)

    def delete_table(self, user: AbstractUser, table: TableForUpdate):
        """
        Moves to the trash an existing table instance if the user has access
        to the related group.
        The table deleted signals are also fired.

        :param user: The user on whose behalf the table is deleted.
        :param table: The table instance that needs to be deleted.
        :raises ValueError: When the provided table is not an instance of Table.
        """

        if not isinstance(table, Table):
            raise ValueError("The table is not an instance of Table")

        table.database.group.has_user(user, raise_error=True)
        table_id = table.id

        TrashHandler.trash(user, table.database.group, table.database, table)

        table_deleted.send(self, table_id=table_id, table=table, user=user)

    @classmethod
    def count_rows(cls):
        """
        Counts how many rows each user table has and stores the count
        for later reference.
        """

        chunk_size = 200
        tables_to_store = []
        time = timezone.now()
        for i, table in enumerate(
            Table.objects.filter(database__group__template__isnull=True).iterator(
                chunk_size=chunk_size
            )
        ):
            count = table.get_model(field_ids=[]).objects.count()
            table.row_count = count
            table.row_count_updated_at = time
            tables_to_store.append(table)

            # This makes sure we don't pollute the memory
            if i % chunk_size == 0:
                Table.objects.bulk_update(
                    tables_to_store, ["row_count", "row_count_updated_at"]
                )
                tables_to_store = []

        if len(tables_to_store) > 0:
            Table.objects.bulk_update(
                tables_to_store, ["row_count", "row_count_updated_at"]
            )
