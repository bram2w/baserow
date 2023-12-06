from typing import List

from django.contrib.auth.models import AbstractUser

from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.workflow_actions.handler import (
    BuilderWorkflowActionHandler,
)
from baserow.contrib.builder.workflow_actions.models import (
    BuilderWorkflowAction,
    WorkflowAction,
)
from baserow.contrib.builder.workflow_actions.operations import (
    CreateBuilderWorkflowActionOperationType,
    DeleteBuilderWorkflowActionOperationType,
    ListBuilderWorkflowActionsPageOperationType,
    OrderBuilderWorkflowActionOperationType,
    ReadBuilderWorkflowActionOperationType,
    UpdateBuilderWorkflowActionOperationType,
)
from baserow.contrib.builder.workflow_actions.signals import (
    workflow_action_created,
    workflow_action_deleted,
    workflow_action_updated,
    workflow_actions_reordered,
)
from baserow.contrib.builder.workflow_actions.workflow_action_types import (
    BuilderWorkflowActionType,
)
from baserow.core.handler import CoreHandler


class BuilderWorkflowActionService:
    def __init__(self):
        self.handler = BuilderWorkflowActionHandler()

    def get_workflow_action(
        self, user: AbstractUser, workflow_action_id: int
    ) -> WorkflowAction:
        """
        Returns an workflow_action instance from the database. Also checks the user
        permissions.

        :param user: The user trying to get the workflow_action
        :param workflow_action_id: The ID of the workflow_action
        :return: The workflow_action instance
        """

        workflow_action = self.handler.get_workflow_action(workflow_action_id)

        CoreHandler().check_permissions(
            user,
            ReadBuilderWorkflowActionOperationType.type,
            workspace=workflow_action.page.builder.workspace,
            context=workflow_action,
        )

        return workflow_action

    def get_workflow_actions(
        self,
        user: AbstractUser,
        page: Page,
    ) -> List[WorkflowAction]:
        """
        Gets all the workflow_actions of a given page visible to the given user.

        :param user: The user trying to get the workflow_actions.
        :param page: The page that holds the workflow_actions.
        :return: The workflow_actions of that page.
        """

        CoreHandler().check_permissions(
            user,
            ListBuilderWorkflowActionsPageOperationType.type,
            workspace=page.builder.workspace,
            context=page,
        )

        user_workflow_actions = CoreHandler().filter_queryset(
            user,
            ListBuilderWorkflowActionsPageOperationType.type,
            BuilderWorkflowAction.objects.all(),
            workspace=page.builder.workspace,
        )

        return self.handler.get_workflow_actions(
            page, base_queryset=user_workflow_actions
        )

    def create_workflow_action(
        self,
        user: AbstractUser,
        workflow_action_type: BuilderWorkflowActionType,
        page: Page,
        **kwargs,
    ) -> WorkflowAction:
        """
        Creates a new workflow_action for a page given the user permissions.

        :param user: The user trying to create the workflow_action.
        :param workflow_action_type: The type of the workflow_action.
        :param page: The page the workflow_action is associated with.
        :param kwargs: Additional attributes of the workflow_action.
        :return: The created workflow_action.
        """

        CoreHandler().check_permissions(
            user,
            CreateBuilderWorkflowActionOperationType.type,
            workspace=page.builder.workspace,
            context=page,
        )

        new_workflow_action = self.handler.create_workflow_action(
            workflow_action_type, page=page, **kwargs
        )

        workflow_action_created.send(
            self,
            workflow_action=new_workflow_action,
            user=user,
        )

        return new_workflow_action

    def update_workflow_action(
        self, user: AbstractUser, workflow_action: WorkflowAction, **kwargs
    ) -> WorkflowAction:
        """
        Updates and workflow_action with values. Will also check if the values are
        allowed to be set on the workflow_action first.

        :param user: The user trying to update the workflow_action.
        :param workflow_action: The workflow_action that should be updated.
        :param kwargs: Additional attributes of the workflow_action.
        :return: The updated workflow_action.
        """

        CoreHandler().check_permissions(
            user,
            UpdateBuilderWorkflowActionOperationType.type,
            workspace=workflow_action.page.builder.workspace,
            context=workflow_action,
        )

        workflow_action = self.handler.update_workflow_action(workflow_action, **kwargs)

        workflow_action_updated.send(self, workflow_action=workflow_action, user=user)

        return workflow_action

    def delete_workflow_action(
        self, user: AbstractUser, workflow_action: WorkflowAction
    ):
        """
        Deletes a workflow_action.

        :param user: The user trying to delete the workflow_action.
        :param workflow_action: The to-be-deleted workflow_action.
        """

        page = workflow_action.page

        CoreHandler().check_permissions(
            user,
            DeleteBuilderWorkflowActionOperationType.type,
            workspace=page.builder.workspace,
            context=workflow_action,
        )

        self.handler.delete_workflow_action(workflow_action)

        workflow_action_deleted.send(
            self, workflow_action_id=workflow_action.id, page=page, user=user
        )

    def order_workflow_actions(
        self,
        user: AbstractUser,
        page: Page,
        order: List[int],
        element: Element = None,
    ) -> List[int]:
        """
        Assigns a new order to the workflow actions in a builder application.

        :param user: The user trying to order the domains
        :param page: The page that the workflow actions belong to
        :param order: The new order of the workflow actions
        :param element: The element the page belongs to
        :return: The new order of the workflow actions
        """

        CoreHandler().check_permissions(
            user,
            OrderBuilderWorkflowActionOperationType.type,
            workspace=page.builder.workspace,
            context=page,
        )

        all_workflow_actions = BuilderWorkflowAction.objects.filter(
            page=page, element=element
        )

        user_workflow_actions = CoreHandler().filter_queryset(
            user,
            OrderBuilderWorkflowActionOperationType.type,
            all_workflow_actions,
            workspace=page.builder.workspace,
        )

        full_order = self.handler.order_workflow_actions(
            page, order, base_qs=user_workflow_actions, element=element
        )

        workflow_actions_reordered.send(self, order=full_order, user=user)

        return full_order
