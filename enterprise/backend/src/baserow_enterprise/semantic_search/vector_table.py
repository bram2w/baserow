from dataclasses import dataclass

from django.db import connection, transaction

from baserow.core.pgvector import DEFAULT_EMBEDDING_DIMENSIONS
from baserow.core.psycopg import sql

# Workspaces of which the vector table is known to exist, so that it isn't checked
# on every indexing run. Tables are only dropped together with their workspace.
_existing_vector_tables: set[int] = set()


@dataclass
class Chunk:
    row_id: int
    chunk_index: int
    content_hash: str
    embedding: list[float]


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


class SemanticSearchVectorTable:
    """
    The chunks and embeddings of all semantic search fields of a workspace. The
    table is created when the workspace first needs it.
    """

    def __init__(self, workspace_id: int):
        """
        :param workspace_id: The workspace of which the table contains the vectors.
        """

        self.workspace_id = workspace_id
        self.name = f"database_semantic_search_workspace_{workspace_id}_data"

    @property
    def identifier(self) -> sql.Identifier:
        return sql.Identifier(self.name)

    def exists(self) -> bool:
        """
        :return: Whether the table was created.
        """

        with connection.cursor() as cursor:
            # Quoted, because `to_regclass` lowercases unquoted names.
            cursor.execute("SELECT to_regclass(%s) IS NOT NULL", [f'"{self.name}"'])
            return cursor.fetchone()[0]

    def create_if_not_exists(self):
        if self.workspace_id in _existing_vector_tables or self.exists():
            _existing_vector_tables.add(self.workspace_id)
            return

        with transaction.atomic(), connection.cursor() as cursor:
            # Two tables of the same workspace can be indexed at the same time, and
            # `IF NOT EXISTS` doesn't protect against concurrent creation.
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [self.name])
            cursor.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {table} (
                        id bigserial PRIMARY KEY,
                        field_id integer NOT NULL,
                        row_id integer NOT NULL,
                        chunk_index smallint NOT NULL,
                        content_hash char(32) NOT NULL,
                        embedding vector({dimensions}) NOT NULL,
                        UNIQUE (field_id, row_id, chunk_index)
                    )
                    """
                ).format(
                    table=self.identifier,
                    dimensions=sql.Literal(DEFAULT_EMBEDDING_DIMENSIONS),
                )
            )
            # Built while the table is still empty, so that it never has to be built
            # on a large table.
            cursor.execute(
                sql.SQL(
                    """
                    CREATE INDEX IF NOT EXISTS {index} ON {table}
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                    """
                ).format(
                    index=sql.Identifier(f"{self.name}_embedding_idx"),
                    table=self.identifier,
                )
            )
        _existing_vector_tables.add(self.workspace_id)

    def drop(self):
        _existing_vector_tables.discard(self.workspace_id)
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {table}").format(table=self.identifier)
            )

    def get_content_hashes(self, field_id: int, row_ids: list[int]) -> dict[int, str]:
        """
        :param field_id: The field of the cells.
        :param row_ids: The rows of the cells.
        :return: The hash of the indexed value of every cell that has chunks, by
            row id.
        """

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    """
                    SELECT row_id, content_hash FROM {table}
                    WHERE field_id = %s AND row_id = ANY(%s) AND chunk_index = 0
                    """
                ).format(table=self.identifier),
                [field_id, row_ids],
            )
            return dict(cursor.fetchall())

    def replace_chunks(self, field_id: int, row_ids: list[int], chunks: list[Chunk]):
        """
        Replaces all the chunks of the provided rows. Rows without new chunks no
        longer have a value to search in.

        :param field_id: The field of the cells.
        :param row_ids: The rows of which the chunks are replaced.
        :param chunks: The new chunks of the rows.
        """

        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "DELETE FROM {table} WHERE field_id = %s AND row_id = ANY(%s)"
                ).format(table=self.identifier),
                [field_id, row_ids],
            )
            if chunks:
                cursor.executemany(
                    sql.SQL(
                        """
                        INSERT INTO {table}
                            (field_id, row_id, chunk_index, content_hash, embedding)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        """
                    ).format(table=self.identifier),
                    [
                        (
                            field_id,
                            chunk.row_id,
                            chunk.chunk_index,
                            chunk.content_hash,
                            _vector_literal(chunk.embedding),
                        )
                        for chunk in chunks
                    ],
                )

    def delete(
        self, field_ids: list[int] | None = None, row_ids: list[int] | None = None
    ):
        """
        :param field_ids: Only deletes the chunks of these fields, if set.
        :param row_ids: Only deletes the chunks of these rows, if set.
        """

        conditions = []
        params = []
        if field_ids is not None:
            conditions.append(sql.SQL("field_id = ANY(%s)"))
            params.append(field_ids)
        if row_ids is not None:
            conditions.append(sql.SQL("row_id = ANY(%s)"))
            params.append(row_ids)
        where = sql.SQL(" AND ").join(conditions) if conditions else sql.SQL("TRUE")
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DELETE FROM {table} WHERE {where}").format(
                    table=self.identifier, where=where
                ),
                params,
            )

    def delete_rows_not_in(self, field_id: int, table_name: str):
        """
        Deletes the chunks of rows that no longer exist, because not every way of
        deleting rows goes through the trash.

        :param field_id: The field of which the chunks are checked.
        :param table_name: The database table of the rows of the field.
        """

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    """
                    DELETE FROM {vector_table} AS chunk
                    WHERE chunk.field_id = %s AND NOT EXISTS (
                        SELECT 1 FROM {table} AS row WHERE row.id = chunk.row_id
                    )
                    """
                ).format(
                    vector_table=self.identifier, table=sql.Identifier(table_name)
                ),
                [field_id],
            )

    def copy_field(
        self,
        source: "SemanticSearchVectorTable",
        source_field_id: int,
        target_field_id: int,
    ):
        """
        Copies the chunks of a field of which the rows were copied with the same
        ids, so that they don't have to be embedded again.

        :param source: The vector table of the workspace of the source field.
        :param source_field_id: The field of which the chunks are copied.
        :param target_field_id: The field that gets the chunks.
        """

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    """
                    INSERT INTO {target}
                        (field_id, row_id, chunk_index, content_hash, embedding)
                    SELECT %s, row_id, chunk_index, content_hash, embedding
                    FROM {source} WHERE field_id = %s
                    ON CONFLICT DO NOTHING
                    """
                ).format(target=self.identifier, source=source.identifier),
                [target_field_id, source_field_id],
            )
