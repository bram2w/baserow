from django.db.models import Sum, Q

from baserow.core.usage.registries import GroupStorageUsageItemType, UsageInBytes
from baserow.core.user_files.models import UserFile


class FormViewGroupStorageUsageItem(GroupStorageUsageItemType):
    type = "form_view"

    def calculate_storage_usage(self, group_id: int) -> UsageInBytes:
        image_ids = (
            UserFile.objects.filter(
                Q(
                    form_view_cover_image__table__database__group=group_id,
                    form_view_cover_image__table__database__trashed=False,
                    form_view_cover_image__table__trashed=False,
                )
                | Q(
                    form_view_logo_image__table__database__group=group_id,
                    form_view_logo_image__table__database__trashed=False,
                    form_view_logo_image__table__trashed=False,
                )
            )
            .values("id")
            .distinct()
            .values_list("id", flat=True)
        )

        usage = UserFile.objects.filter(id__in=image_ids).aggregate(sum=Sum("size"))[
            "sum"
        ]

        return usage or 0
