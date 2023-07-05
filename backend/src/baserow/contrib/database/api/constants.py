# When entities are exposed publicly to anonymous users as many entity ids are hardcoded
# to this value as possible to prevent data leaks.
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from baserow.contrib.database.search.handler import SearchModes

PUBLIC_PLACEHOLDER_ENTITY_ID = 0
SEARCH_MODE_API_PARAM = OpenApiParameter(
    name="search_mode",
    location=OpenApiParameter.QUERY,
    type=OpenApiTypes.STR,
    description=(
        "If provided, allows API consumers to determine what kind of search "
        "experience they wish to have. "
        f"If the default `{SearchModes.MODE_FT_WITH_COUNT}` is used, then Postgres "
        f"full-text search is used. If `{SearchModes.MODE_COMPAT}` is "
        "provided then the search term will be exactly searched for including "
        "whitespace on each cell. This is the Baserow legacy search behaviour."
    ),
)
