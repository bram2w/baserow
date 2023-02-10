from django.db import transaction
from django.db.transaction import Atomic

from baserow.contrib.builder.models import Builder
from baserow.core.models import Application
from baserow.core.registries import ApplicationType


class BuilderApplicationType(ApplicationType):
    type = "builder"
    model_class = Builder

    def export_safe_transaction_context(self, application: Application) -> Atomic:
        return transaction.atomic()
