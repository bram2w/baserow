from typing import NewType

from .models import DataSource

DataSourceForUpdate = NewType("DataSourceForUpdate", DataSource)
