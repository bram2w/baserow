from django.contrib.auth.models import AbstractUser

from baserow.contrib.builder.handler import BuilderHandler
from baserow.contrib.builder.models import Builder
from baserow.core.handler import CoreHandler
from baserow.core.operations import ReadApplicationOperationType


class BuilderService:
    def __init__(self):
        self.handler = BuilderHandler()

    def get_builder(self, user: AbstractUser, builder_id: int) -> Builder:
        """
        Gets builder instance from database using its Id if the user has the permission
        to see it.

        :param user: The user who wants to get the builder.
        :param builder_id: ID of the builder instance you want to get.
        :return: The builder model instance.
        """

        builder = self.handler.get_builder(builder_id)

        application = builder.application_ptr

        CoreHandler().check_permissions(
            user,
            ReadApplicationOperationType.type,
            workspace=application.workspace,
            context=application,
        )

        return builder
