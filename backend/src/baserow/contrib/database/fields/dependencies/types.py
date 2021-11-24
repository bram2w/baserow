from typing import Union, Tuple, Optional, Set

ThroughFieldName = str
TargetFieldName = str
FieldName = str
ThroughFieldDependency = Tuple[ThroughFieldName, TargetFieldName]
FieldDependencies = Set[Union[FieldName, ThroughFieldDependency]]
"""
A field dependency can either be a string field name to a field in the same table,
or a tuple of ThroughFieldName and TargetFieldName, both string field names also.
The ThroughFieldName must be the name of a link row field in the same table and the
TargetFieldName must be the name of a field in the link_row_table of the link row field.
"""
OptionalFieldDependencies = Optional[FieldDependencies]
