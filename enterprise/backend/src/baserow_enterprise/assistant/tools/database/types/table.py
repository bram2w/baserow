from django.db.models import Q

from pydantic import Field

from baserow.contrib.database.tools.tables import (  # noqa: F401
    BaseTableItem,
    BaseTableItemCreate,
    TableItem,
    TableItemCreate,
)
from baserow_enterprise.assistant.types import BaseModel


class ListTablesFilterArg(BaseModel):
    database_id_or_name: int | str | None = Field(
        default=None,
        description="The ID or name of the database to filter. null to exclude this filter.",
    )
    table_ids_or_names: list[int | str] | None = Field(
        default=None,
        description="A list of table ids or names to filter in an OR fashion. null to exclude this filter.",
    )

    def to_orm_filter(self) -> Q:
        q_filter = Q()
        if isinstance(self.database_id_or_name, int):
            q_filter &= Q(database_id=self.database_id_or_name)
        elif isinstance(self.database_id_or_name, str):
            q_filter &= Q(database__name__icontains=self.database_id_or_name)
        if self.table_ids_or_names:
            combined = Q()
            ids = [item for item in self.table_ids_or_names if isinstance(item, int)]
            names = [item for item in self.table_ids_or_names if isinstance(item, str)]
            if ids:
                combined |= Q(id__in=ids)
            if names:
                for name in names:
                    combined |= Q(name__icontains=name)
            q_filter &= combined
        return q_filter
