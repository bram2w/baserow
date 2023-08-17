from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.contrib.database.api.rows.serializers import (
    get_example_row_serializer_class,
)

example_pagination_row_serializer_class = get_example_pagination_serializer_class(
    get_example_row_serializer_class(example_type="get", user_field_names=True)
)
