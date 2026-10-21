from __future__ import annotations

from pydantic import BaseModel, Field


class ListDatabasesInput(BaseModel):
    pass


class ListTablesInput(BaseModel):
    database_id: int | None = Field(
        None, description="If provided, only return tables from this database."
    )


class UpdateTableInput(BaseModel):
    table_id: int = Field(..., description="The ID of the table to rename.")
    name: str = Field(..., description="The new name for the table.")


class DeleteTableInput(BaseModel):
    table_id: int = Field(..., description="The ID of the table to delete.")


class GetTableSchemaInput(BaseModel):
    table_ids: list[int] = Field(
        ..., description="List of table IDs to get the schema for."
    )
