from baserow.contrib.builder.workflow_actions.models import NotificationWorkflowAction


class WorkflowActionFixture:
    def create_notification_workflow_action(self, **kwargs):
        return self.create_workflow_action(NotificationWorkflowAction, **kwargs)

    def create_workflow_action(self, model_class, **kwargs):
        if "order" not in "kwargs":
            kwargs["order"] = 0

        if "page" not in kwargs and "element" in kwargs:
            kwargs["page"] = kwargs["element"].page

        return model_class.objects.create(**kwargs)
