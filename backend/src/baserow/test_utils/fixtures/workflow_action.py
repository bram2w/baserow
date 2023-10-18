from baserow.contrib.builder.workflow_actions.models import NotificationWorkflowAction


class WorkflowActionFixture:
    def create_notification_workflow_action(self, **kwargs):
        return self.create_workflow_action(NotificationWorkflowAction, **kwargs)

    def create_workflow_action(self, model_class, **kwargs):
        return model_class.objects.create(**kwargs)
