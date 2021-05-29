from django.db.models import Q

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions
from baserow.api.schemas import get_error_schema
from baserow.api.pagination import PageNumberPagination
from baserow_premium.api.admin.errors import (
    ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE,
    ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION,
)
from baserow_premium.admin.exceptions import (
    InvalidSortDirectionException,
    InvalidSortAttributeException,
)


class AdminListingView(APIView):
    permission_classes = (IsAdminUser,)
    serializer_class = None
    search_fields = ["id"]
    sort_field_mapping = {}

    @map_exceptions(
        {
            InvalidSortDirectionException: ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION,
            InvalidSortAttributeException: ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE,
        }
    )
    def get(self, request):
        """
        Responds with paginated results related to queryset and the serializer
        defined on this class.
        """

        search = request.GET.get("search")
        sorts = request.GET.get("sorts")

        queryset = self.get_queryset(request)
        queryset = self._apply_sorts_or_default_sort(sorts, queryset)
        queryset = self._apply_search(search, queryset)

        paginator = PageNumberPagination(limit_page_size=100)
        page = paginator.paginate_queryset(queryset, request, self)
        serializer = self.get_serializer(request, page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def get_queryset(self, request):
        raise NotImplementedError("The get_queryset method must be set.")

    def get_serializer(self, request, *args, **kwargs):
        if not self.serializer_class:
            raise NotImplementedError(
                "Either the serializer_class must be set or the get_serializer method "
                "must be overwritten."
            )

        return self.serializer_class(*args, **kwargs)

    def _apply_search(self, search, queryset):
        """
        Applies the provided search query to the provided query. If the search query
        is provided then an `icontains` lookup will be done for each field in the
        search_fields property. One of the fields has to match the query.

        :param search: The search query.
        :type search: str or None
        :param queryset: The queryset where the search query must be applied to.
        :type queryset: QuerySet
        :return: The queryset filtering the results by the search query.
        :rtype: QuerySet
        """

        if not search:
            return queryset

        q = Q()

        for search_field in self.search_fields:
            q.add(Q(**{f"{search_field}__icontains": search}), Q.OR)

        return queryset.filter(q)

    def _apply_sorts_or_default_sort(self, sorts: str, queryset):
        """
        Takes a comma separated string in the form of +attribute,-attribute2 and
        applies them to a django queryset in order.
        Defaults to sorting by id if no sorts are provided.
        Raises an InvalidSortDirectionException if an attribute does not begin with `+`
        or `-`.
        Raises an InvalidSortAttributeException if an unknown attribute is supplied to
        sort by or multiple of the same attribute are provided.

        :param sorts: The list of sorts to apply to the queryset.
        :param queryset: The queryset to sort.
        :return: The sorted queryset.
        """

        if sorts is None:
            return queryset.order_by("id")

        parsed_django_order_bys = []
        already_seen_sorts = set()
        for s in sorts.split(","):
            if len(s) <= 2:
                raise InvalidSortAttributeException()

            sort_direction_prefix = s[0]
            sort_field_name = s[1:]

            try:
                sort_direction_to_django_prefix = {"+": "", "-": "-"}
                direction = sort_direction_to_django_prefix[sort_direction_prefix]
            except KeyError:
                raise InvalidSortDirectionException()

            try:
                attribute = self.sort_field_mapping[sort_field_name]
            except KeyError:
                raise InvalidSortAttributeException()

            if attribute in already_seen_sorts:
                raise InvalidSortAttributeException()
            else:
                already_seen_sorts.add(attribute)

            parsed_django_order_bys.append(f"{direction}{attribute}")

        return queryset.order_by(*parsed_django_order_bys)

    @staticmethod
    def get_extend_schema_parameters(
        name, serializer_class, search_fields, sort_field_mapping
    ):
        """
        Returns the schema properties that can be used in in the @extend_schema
        decorator.
        """

        fields = sort_field_mapping.keys()
        all_fields = ", ".join(fields)
        field_name_1 = "field_1"
        field_name_2 = "field_2"
        for i, field in enumerate(fields):
            if i == 0:
                field_name_1 = field
            if i == 1:
                field_name_2 = field

        return {
            "parameters": [
                OpenApiParameter(
                    name="search",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.STR,
                    description=f"If provided only {name} that match the query will "
                    f"be returned.",
                ),
                OpenApiParameter(
                    name="sorts",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.STR,
                    description=f"A comma separated string of attributes to sort by, "
                    f"each attribute must be prefixed with `+` for a descending "
                    f"sort or a `-` for an ascending sort. The accepted attribute "
                    f"names are: {all_fields}. For example `sorts=-{field_name_1},"
                    f"-{field_name_2}` will sort the {name} first by descending "
                    f"{field_name_1} and then ascending {field_name_2}. A sort"
                    f"parameter with multiple instances of the same sort attribute "
                    f"will respond with the ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE "
                    f"error.",
                ),
                OpenApiParameter(
                    name="page",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.INT,
                    description="Defines which page should be returned.",
                ),
                OpenApiParameter(
                    name="size",
                    location=OpenApiParameter.QUERY,
                    type=OpenApiTypes.INT,
                    description=f"Defines how many {name} should be returned per "
                    f"page.",
                ),
            ],
            "responses": {
                200: serializer_class(many=True),
                400: get_error_schema(
                    [
                        "ERROR_PAGE_SIZE_LIMIT",
                        "ERROR_INVALID_PAGE",
                        "ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION",
                        "ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE",
                    ]
                ),
                401: None,
            },
        }
