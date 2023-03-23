from django.urls import include, path, re_path

from .domains import urls as domain_urls
from .elements import urls as element_urls
from .pages import urls as page_urls

app_name = "baserow.contrib.builder.api"

paths_with_builder_id = [
    path(
        "pages/",
        include(
            (page_urls.urlpatterns_with_builder_id, page_urls.app_name),
            namespace="pages",
        ),
    ),
    path(
        "domains/",
        include(
            (domain_urls.urlpatterns_with_builder_id, page_urls.app_name),
            namespace="domains",
        ),
    ),
]

paths_without_builder_id = [
    path(
        "pages/",
        include(
            (page_urls.urlpatterns_without_builder_id, page_urls.app_name),
            namespace="pages",
        ),
    ),
    path(
        "",
        include(
            element_urls,
            namespace="element",
        ),
    ),
    path(
        "domains/",
        include(
            (domain_urls.urlpatterns_without_builder_id, page_urls.app_name),
            namespace="domains",
        ),
    ),
]


urlpatterns = [
    re_path(
        "(?P<builder_id>[0-9]+)/",
        include(
            (paths_with_builder_id, app_name),
            namespace="builder_id",
        ),
    ),
] + paths_without_builder_id
