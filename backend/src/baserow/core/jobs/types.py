from typing import TypeVar

from .models import Job

AnyJob = TypeVar("AnyJob", bound=Job, covariant=True)
