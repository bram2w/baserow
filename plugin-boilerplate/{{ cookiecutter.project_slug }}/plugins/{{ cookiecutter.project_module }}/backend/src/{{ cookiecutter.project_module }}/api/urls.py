from django.urls import re_path

from .views import StartingView

app_name = "{{ cookiecutter.project_module }}.api"

urlpatterns = [
    re_path(r"starting/$", StartingView.as_view(), name="starting"),
]
