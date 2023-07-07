from django.db.models import Q, Sum

from baserow.contrib.builder.elements.models import ImageElement
from baserow.core.usage.registries import UsageInBytes, WorkspaceStorageUsageItemType
from baserow.core.user_files.models import UserFile


class ImageElementWorkspaceStorageUsageItem(WorkspaceStorageUsageItemType):
    type = "image_element"

    def calculate_storage_usage(self, workspace_id: int) -> UsageInBytes:
        image_elements = ImageElement.objects.filter(
            page__builder__workspace_id=workspace_id,
            page__trashed=False,
            page__builder__trashed=False,
        )

        usage = (
            UserFile.objects.filter(Q(id__in=image_elements.values("image_file")))
            .values("size")
            .aggregate(sum=Sum("size"))["sum"]
        )

        return usage or 0
