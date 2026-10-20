from django.urls import path

from .views import AgentApplicationView

app_name = "baserow.contrib.agent"

urlpatterns = [
    path("<int:agent_id>/", AgentApplicationView.as_view(), name="item"),
]
