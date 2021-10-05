from django.urls import path, include

from .tables import urls as table_urls
from .views import urls as view_urls
from .fields import urls as field_urls
from .rows import urls as row_urls
from .tokens import urls as token_urls
from .export import urls as export_urls
from .formula import urls as formula_urls

app_name = "baserow.contrib.database.api"

urlpatterns = [
    path("tables/", include(table_urls, namespace="tables")),
    path("views/", include(view_urls, namespace="views")),
    path("fields/", include(field_urls, namespace="fields")),
    path("rows/", include(row_urls, namespace="rows")),
    path("tokens/", include(token_urls, namespace="tokens")),
    path("export/", include(export_urls, namespace="export")),
    path("formula/", include(formula_urls, namespace="formula")),
]
