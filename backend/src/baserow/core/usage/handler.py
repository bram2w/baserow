from django.db.models import OuterRef, PositiveIntegerField, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from baserow.contrib.database.table.models import Table
from baserow.core.models import Workspace
from baserow.core.usage.registries import workspace_storage_usage_item_registry
from baserow.core.utils import grouper


class UsageHandler:
    @classmethod
    def calculate_storage_usage(cls) -> int:
        """
        Calculates the storage usage of every workspace.
        :return: The amount of workspaces that have been updated.
        """

        # Item types might need to register some plpgsql functions
        # to speedup the calculations.
        for item in workspace_storage_usage_item_registry.get_all():
            if hasattr(item, "register_plpgsql_functions"):
                item.register_plpgsql_functions()

        count, chunk_size = 0, 256
        workspaces_queryset = Workspace.objects.filter(template__isnull=True).iterator(
            chunk_size=chunk_size
        )

        for workspaces in grouper(chunk_size, workspaces_queryset):
            now = timezone.now()
            for workspace in workspaces:
                usage_in_bytes = 0
                for item in workspace_storage_usage_item_registry.get_all():
                    usage_in_bytes += item.calculate_storage_usage(workspace.id)

                workspace.storage_usage = usage_in_bytes / (1024 * 1024)  # in MB
                workspace.storage_usage_updated_at = now

            Workspace.objects.bulk_update(
                workspaces, ["storage_usage", "storage_usage_updated_at"]
            )
            count += len(workspaces)

        return count

    @classmethod
    def get_workspace_row_count_annotation(cls, outer_ref_name: str = "id") -> Coalesce:
        """
        Generates a subquery that can be used to count the row_count on a Workspace
        QuerySet.

        :param outer_ref_name: The name of the outer ref used to identify the workspace
            name.
        :return: The generated SubQuery.
        """

        return Coalesce(
            Subquery(
                Table.objects.filter(
                    row_count__isnull=False,
                    database__workspace_id=OuterRef(outer_ref_name),
                    database__trashed=False,
                )
                .values("database__workspace_id")
                .annotate(row_count_total=Sum("row_count"))
                .values_list("row_count_total", flat=True),
                output_field=PositiveIntegerField(),
            ),
            0,
        )
