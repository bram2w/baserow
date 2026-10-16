from django.urls import path

from .views import AgentApplicationView, AgentConfigurationView, AgentReadinessView

app_name = "baserow.contrib.agent"

urlpatterns = [
    path("<int:agent_id>/", AgentApplicationView.as_view(), name="item"),
    path("<int:agent_id>/readiness/", AgentReadinessView.as_view(), name="readiness"),
    path(
        "<int:agent_id>/configuration/",
        AgentConfigurationView.as_view(),
        name="configuration",
    ),
]
