from django.urls import re_path

from baserow.contrib.builder.api.workflow_actions.views import (
    BuilderWorkflowActionsView,
    BuilderWorkflowActionView,
    OrderBuilderWorkflowActionsView,
)

app_name = "baserow.contrib.builder.api.workflow_actions"

urls_without_builder_id = [
    re_path(
        r"page/(?P<page_id>[0-9]+)/workflow_actions/$",
        BuilderWorkflowActionsView.as_view(),
        name="list",
    ),
    re_path(
        r"workflow_action/(?P<workflow_action_id>[0-9]+)/$",
        BuilderWorkflowActionView.as_view(),
        name="item",
    ),
    re_path(
        r"page/(?P<page_id>[0-9]+)/workflow_actions/order/$",
        OrderBuilderWorkflowActionsView.as_view(),
        name="order",
    ),
]
