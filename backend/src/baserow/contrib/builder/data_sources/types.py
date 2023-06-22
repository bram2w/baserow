from typing import NewType

from .models import DataSource

Expression = str

DataSourceForUpdate = NewType("DataSourceForUpdate", DataSource)
