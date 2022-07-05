from typing import Tuple, List

from baserow.contrib.database.fields.dependencies.models import FieldDependency

ThroughFieldName = str
TargetFieldName = str
FieldName = str
ThroughFieldDependency = Tuple[ThroughFieldName, TargetFieldName]
FieldDependencies = List[FieldDependency]
