from collections import defaultdict
from typing import Optional

from django.db.models import Expression

from baserow.contrib.database.fields.dependencies.exceptions import InvalidViaPath
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.signals import field_updated
from baserow.contrib.database.table.models import GeneratedTableModel


class PathBasedUpdateStatementCollector:
    def __init__(self, table, field_cache):
        self.update_statements = {}
        self.table = table
        self.sub_paths = {}
        self.field_cache = field_cache

    def add_update_statement(
        self, field, update_statement, path_from_starting_table=None
    ):
        if not path_from_starting_table:
            if self.table != field.table:
                raise InvalidViaPath()
            self.update_statements[field.db_column] = update_statement
        else:
            next_via_field_link = path_from_starting_table[0]
            if next_via_field_link.link_row_table != self.table:
                raise InvalidViaPath()
            next_link_db_column = next_via_field_link.db_column
            if next_link_db_column not in self.sub_paths:
                self.sub_paths[next_link_db_column] = PathBasedUpdateStatementCollector(
                    next_via_field_link.table,
                    self.field_cache,
                )
            self.sub_paths[next_link_db_column].add_update_statement(
                field, update_statement, path_from_starting_table[1:]
            )

    def execute_all(self, starting_row_id=None, path_to_starting_table=None):
        path_to_starting_table = path_to_starting_table or []
        self._execute_pending_update_statements(path_to_starting_table, starting_row_id)
        for sub_path_column_name, sub_path in self.sub_paths.items():
            sub_path.execute_all(
                starting_row_id=starting_row_id,
                path_to_starting_table=[sub_path_column_name] + path_to_starting_table,
            )

    def _execute_pending_update_statements(
        self, path_to_starting_table, starting_row_id
    ):
        model = self.field_cache.get_model(self.table)
        qs = model.objects_and_trash
        if starting_row_id is not None:
            if len(path_to_starting_table) == 0:
                path_to_starting_table_id_column = "id"
            else:
                path_to_starting_table_id_column = (
                    "__".join(path_to_starting_table) + "__id"
                )
            qs = qs.filter(**{path_to_starting_table_id_column: starting_row_id})
        qs.update(**self.update_statements)


class CachingFieldUpdateCollector(FieldCache):
    """
    An extended FieldCache which also keeps track of fields which have been specifically
    marked as updated. Used so field graph updates can collect together the entire
    set of changed fields to report back to the user.
    """

    def __init__(
        self,
        starting_table,
        existing_field_lookup_cache: Optional[FieldCache] = None,
        existing_model: Optional[GeneratedTableModel] = None,
        starting_row_id=None,
    ):
        """

        :param starting_table: The table where the triggering field update begins.
        :param existing_field_lookup_cache: An existing cache to initialize this
            collectors internal field cache with.
        :param existing_model: An existing model to initialize this collectors
            internal field cache with.
        :param starting_row_id: If the update starts from a single row in the
            starting table set this and all update statements executed by this collector
            will only update rows which join back to this starting row.
        """

        super().__init__(existing_field_lookup_cache, existing_model)
        self._updated_fields_per_table = defaultdict(dict)
        self._starting_row_id = starting_row_id
        self._starting_table = starting_table

        self._update_statement_collector = PathBasedUpdateStatementCollector(
            self._starting_table, self
        )

    def add_field_with_pending_update_statement(
        self,
        field,
        update_statement: Expression,
        via_path_to_starting_table=None,
    ):
        """
        Stores the provided field as an updated one to send in field updated signals
        when triggered to do so. Also stores the provided update statement to execute
        later when apply_updates is called.

        :param field: The field which has been updated.
        :param update_statement: The update statement to run over the fields row values
            to update them.
        :param via_path_to_starting_table: A list of link row fields which lead from
            the self.starting_table to the table containing field. Used to properly
            order the update statements so the graph is updated in sequence and also
            used if self.starting_row_id is set so only rows which join back to the
            starting row via this path are updated.
        """

        self._updated_fields_per_table[field.table_id][field.id] = field
        self._update_statement_collector.add_update_statement(
            field, update_statement, via_path_to_starting_table
        )

    def apply_updates_returning_updated_fields_in_start_table(self):
        """
        Triggers all update statements to be executed in the correct order in as few
        update queries as possible.
        :return: The list of all fields which have been updated in the starting table.
        """

        self._update_statement_collector.execute_all(self._starting_row_id)
        return self._for_table(self._starting_table)

    def send_additional_field_updated_signals(self):
        """
        Sends field_updated signals for all fields which have been updated in tables
        which were not the self._starting_table. Will group together fields per table
        so only one signal is sent per table where the field_updated.field will be the
        first updated field encountered for that table and field_updated.related_fields
        will be all the other updated fields in that table.
        """

        for field, related_fields in self._get_updated_fields_per_table():
            if field.table != self._starting_table:
                field_updated.send(
                    self,
                    field=field,
                    related_fields=related_fields,
                    user=None,
                )

    def _get_updated_fields_per_table(self):
        result = []
        for fields_dict in self._updated_fields_per_table.values():
            fields = list(fields_dict.values())
            result.append((fields[0], fields[1:]))
        return result

    def _for_table(self, table):
        return list(self._updated_fields_per_table.get(table.id, {}).values())
