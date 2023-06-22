from typing import NewType, TypeVar

from .models import Integration

IntegrationSubClass = TypeVar("IntegrationSubClass", bound="Integration")

IntegrationForUpdate = NewType("IntegrationForUpdate", Integration)
