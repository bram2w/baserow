from typing import Any, cast, NewType, List, Tuple, Optional, Dict
from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet, Sum
from django.utils import timezone
from django.utils import translation
from django.utils.translation import gettext as _

from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.models import Job
from baserow.contrib.database.fields.constants import RESERVED_BASEROW_FIELD_NAMES
from baserow.contrib.database.fields.exceptions import (
    MaxFieldLimitExceeded,
    MaxFieldNameLengthExceeded,
    ReservedBaserowFieldNameException,
    InvalidBaserowFieldName,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.models import Field
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
    InitialSyncTableDataLimitExceeded,
    InitialTableDataDuplicateName,
)
from .models import Table
from .signals import table_updated, table_deleted, tables_reordered


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
        data: Optional[List[List[Any]]] = None,
        first_row_header: bool = True,
        session: Optional[str] = None,
        sync: bool = False,
    ) -> Job:
        """
        Starts a new job to create a new table from optional provided data.

        :param user: The user on whose behalf the table is created.
        :param database: The database that the table instance belongs to.
        :param name: The name of the table is created.
        :param data: A list containing all the rows that need to be inserted is
            expected. All the values will be inserted in the database.
        :param first_row_header: Indicates if the first row are the fields. The names
            of these rows are going to be used as fields. If `fields` is provided,
            this options is ignored.
        :param session: The user session Id used to register the action.
        :param sync: Set to True if you want to execute the task synchronously.
        :return: The created job instance.
        """

        database.group.has_user(user, raise_error=True)

        if sync:
            limit = settings.BASEROW_INITIAL_CREATE_SYNC_TABLE_DATA_LIMIT
            if limit and len(data) > limit:
                raise InitialSyncTableDataLimitExceeded(
                    f"It is not possible to import more than "
                    f"{settings.BASEROW_INITIAL_CREATE_SYNC_TABLE_DATA_LIMIT} rows "
                    "when creating a table synchronously. Use Asynchronous "
                    "alternative instead."
                )

        job = JobHandler().create_and_start_job(
            user,
            "file_import",
            database=database,
            name=name,
            data=data,
            first_row_header=first_row_header,
            user_session_id=session,
            sync=sync,
        )

        if sync:
            job.refresh_from_db()

        return job

    def create_minimal_table(
        self,
        user: AbstractUser,
        database: Database,
        name: str,
        fill_example: bool = False,
        session: Optional[str] = None,
    ) -> Job:
        """
        Creates a new minimum table with only one text field and no data.

        :param user: The user on whose behalf the table is created.
        :param database: The database that the table instance belongs to.
        :param name: The name of the table is created.
        :param fill_example: Fill the table with example field and data.
        :param session: The user session Id used to register the action.
        :return: The created job instance.
        """

        database.group.has_user(user, raise_error=True)

        with translation.override(user.profile.language):
            if fill_example:
                fields, data = self.get_example_table_field_and_data()
            else:
                fields, data = self.get_minimal_table_field_and_data()

        table = self.create_table_and_fields(user, database, name, fields)

        job = self.import_table_data(user, table, data, session=session, sync=True)

        return job

    def import_table_data(
        self,
        user: AbstractUser,
        table: Table,
        data: List[List[Any]],
        session: Optional[str] = None,
        sync: bool = False,
    ) -> Job:
        """
        Creates job to import data into the specified table.

        :param user: The user on whose behalf the table is created.
        :param table: The table we want the data to be inserted.
        :param data: A list containing all the rows that need to be inserted is
            expected.
        :param session: The user session Id used to register the action.
        :param sync: Set to True if you want to execute the task synchronously.
        :return: The created job instance.
        """

        job = JobHandler().create_and_start_job(
            user,
            "file_import",
            data=data,
            table=table,
            user_session_id=session,
            sync=sync,
        )

        if sync:
            job.refresh_from_db()

        return job

    def create_table_and_fields(
        self,
        user: AbstractUser,
        database: Database,
        name: str,
        fields: List[Tuple[str, str, Dict[str, Any]]],
    ) -> Table:
        """
        Creates a new table with the specified fields. Also creates a default grid view
        for this table.

        :param user: The user on whose behalf the table is created.
        :param database: The database that the table instance belongs to.
        :param name: The name of the table is created.
        :param fields: You specify the field configuration with this parameter. The
            tuples content is the field name, then the field type and the field
            configuration. You can add an optional `field_options` dict for the
            field_options of the created view.
        """

        last_order = Table.get_last_order(database)
        table = Table.objects.create(
            database=database,
            order=last_order,
            name=name,
        )

        # Let's create the fields before creating the model so that the whole
        # table schema is created right away.
        field_options_dict = {}
        for index, (name, field_type_name, field_config) in enumerate(fields):
            field_options = field_config.pop("field_options", None)
            field_type = field_type_registry.get(field_type_name)
            FieldModel = field_type.model_class

            fields[index] = FieldModel.objects.create(
                table=table,
                order=index,
                primary=index == 0,
                name=name,
                **field_config,
            )
            if field_options:
                field_options_dict[fields[index].id] = field_options

        # Creates a default view
        view_handler = ViewHandler()

        with translation.override(user.profile.language):
            view = view_handler.create_view(
                user, table, GridViewType.type, name=_("Grid")
            )

        # Fix field_options if any
        if field_options_dict:
            view_handler.update_field_options(
                user=user,
                view=view,
                field_options=field_options_dict,
                fields=fields,
            )

        # Create the table schema in the database database.
        with safe_django_schema_editor() as schema_editor:
            # Django only creates indexes when the model is managed.
            model = table.get_model(managed=True)
            schema_editor.create_model(model)

        return table

    def normalize_initial_table_data_and_guess_types(
        self, data: List[List[Any]], first_row_header: bool
    ) -> Tuple[List, List]:
        """
        Normalizes the provided initial table data. The amount of columns will be made
        equal for each row. The header and the rows will also be separated. Try to guess
        the field type by counting the occurrence of all values type in data. The
        guesser try to be as safer as possible but by setting the value
        `settings.BASEROW_IMPORT_TOLERATED_TYPE_ERROR_THRESHOLD` to something greater
        than 0 we allow this percentage of rows to fail import to have more precise
        types.

        :param data: A list containing all the provided rows.
        :param first_row_header: Indicates if the first row is the header. For each
            of these header columns a field is going to be created.
        :return: A list containing the field names and a list containing all the rows.
        :raises InvalidInitialTableData: When the data doesn't contain a column or row.
        :raises MaxFieldNameLengthExceeded: When the provided name is too long.
        :raises InitialTableDataDuplicateName: When duplicates exit in field names.
        :raises ReservedBaserowFieldNameException: When the field name is reserved by
            Baserow.
        :raises InvalidBaserowFieldName: When the field name is invalid (emtpy).
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
            fields.append(_("Field %d") % (i + 1,))

        if len(fields) > settings.MAX_FIELD_LIMIT:
            raise MaxFieldLimitExceeded(
                f"Fields count exceeds the limit of {settings.MAX_FIELD_LIMIT}"
            )

        # Stripping whitespace from field names is already done by
        # TableCreateSerializer however we repeat to ensure that non API usages of
        # this method is consistent with api usage.
        field_name_set = {str(name).strip() for name in fields}

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

        normalized_data = []

        # Fill missing rows and computes value type frequencies
        value_type_frequencies = defaultdict(lambda: defaultdict(lambda: 0))
        for row in data:
            new_row = []
            for index, value in enumerate(row):
                if value is not None:
                    if isinstance(value, int):
                        if len(str(value)) <= 50:
                            value_type_frequencies[index]["number_int"] += 1
                        else:
                            value_type_frequencies[index]["text"] += 1
                    elif isinstance(value, float):
                        sign, digits, exponent = Decimal(str(value)).as_tuple()
                        if abs(exponent) <= 10 and len(digits) <= 50 + 10:
                            value_type_frequencies[index]["number_float"] += 1
                        else:
                            value_type_frequencies[index]["text"] += 1
                    else:
                        value = "" if value is None else str(value)
                        if len(value) > 255:
                            value_type_frequencies[index]["long_text"] += 1
                        else:
                            value_type_frequencies[index]["text"] += 1

                new_row.append(value)

            # Fill incomplete rows with empty values
            for i in range(len(new_row), largest_column_count):
                new_row.append(None)

            normalized_data.append(new_row)

        field_with_type = []
        tolerated_error_threshold = (
            len(normalized_data)
            / 100
            * settings.BASEROW_IMPORT_TOLERATED_TYPE_ERROR_THRESHOLD
        )
        # Try to guess field type from type frequency
        for index, field_name in enumerate(fields):
            frequencies = value_type_frequencies[index]
            if frequencies["long_text"] > tolerated_error_threshold:
                field_with_type.append(
                    (field_name, "long_text", {"field_options": {"width": 400}})
                )
            elif frequencies["text"] > tolerated_error_threshold:
                field_with_type.append((field_name, "text", {}))
            elif frequencies["number_float"] > tolerated_error_threshold:
                field_with_type.append(
                    (
                        field_name,
                        "number",
                        {"number_negative": True, "number_decimal_places": 10},
                    )
                )
            elif frequencies["number_int"] > tolerated_error_threshold:
                field_with_type.append(
                    (
                        field_name,
                        "number",
                        {"number_negative": True, "field_options": {"width": 150}},
                    )
                )
            else:
                field_with_type.append((field_name, "text", {}))

        return field_with_type, normalized_data

    def get_example_table_field_and_data(self):
        """
        Generates fields and data with some initial example data.
        """

        fields = [
            (_("Name"), "text", {}),
            (_("Notes"), "long_text", {"field_options": {"width": 400}}),
            (_("Active"), "boolean", {"field_options": {"width": 100}}),
        ]
        data = [["", "", False], ["", "", False]]
        return fields, data

    def get_minimal_table_field_and_data(self):
        """
        Generates fields and data for an empty table.
        """

        fields = [
            (_("Name"), "text", {}),
        ]
        data = []
        return fields, data

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

    @classmethod
    def get_total_row_count_of_group(cls, group_id: int) -> int:
        """
        Returns the total row count of all tables in the given group.

        :param group_id: The group of which the total row count needs to be calculated.
        :return: The total row count of all tables in the given group.
        """

        return (
            Table.objects.filter(database__group_id=group_id).aggregate(
                Sum("row_count")
            )["row_count__sum"]
            or 0
        )
