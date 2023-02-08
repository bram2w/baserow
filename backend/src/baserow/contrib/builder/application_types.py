from baserow.contrib.builder.models import Builder
from baserow.core.registries import ApplicationType


class BuilderApplicationType(ApplicationType):
    type = "builder"
    model_class = Builder
