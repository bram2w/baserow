from django.db.models import Q, Sum

from baserow.contrib.database.views.models import FormView
from baserow.core.usage.registries import GroupStorageUsageItemType, UsageInBytes
from baserow.core.user_files.models import UserFile


class FormViewGroupStorageUsageItem(GroupStorageUsageItemType):
    type = "form_view"

    def calculate_storage_usage(self, group_id: int) -> UsageInBytes:
        form_views = FormView.objects.filter(
            table__database__group_id=group_id,
            table__trashed=False,
            table__database__trashed=False,
        )

        usage = (
            UserFile.objects.filter(
                Q(id__in=form_views.values("cover_image"))
                | Q(id__in=form_views.values("logo_image"))
            )
            .values("size")
            .aggregate(sum=Sum("size"))["sum"]
        )

        return usage or 0
