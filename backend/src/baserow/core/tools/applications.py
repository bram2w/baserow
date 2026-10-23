"""
Application tools shared by the clients that act for a user. An application is a
database, an application builder, an automation or a dashboard.
"""

from typing import Annotated, Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from pydantic import Field

from baserow.core.models import Application
from baserow.core.registries import application_type_registry
from baserow.core.service import CoreService
from baserow.core.tools import ToolContext

MAX_PAGE_SIZE = 100


def visible_applications(
    ctx: ToolContext, types: list[str] | None = None
) -> QuerySet[Application]:
    """
    The applications of the workspace the user can see, in sidebar order.

    :param types: Only applications of these types, if given.
    :raises InstanceTypeDoesNotExist: If a type isn't an application type.
    """

    applications = CoreService().list_applications_in_workspace(
        ctx.user, ctx.workspace, specific=False
    )
    if types is not None:
        models = [application_type_registry.get(t).model_class for t in types]
        applications = applications.filter(
            content_type__in=ContentType.objects.get_for_models(*models).values()
        )
    return applications


def list_applications(
    ctx: ToolContext,
    types: Annotated[
        list[str] | None,
        Field(
            description="Only list applications of these types: database, builder, "
            "automation or dashboard. null lists all types."
        ),
    ] = None,
    page: Annotated[int, Field(ge=1, description="The page to return.")] = 1,
    size: Annotated[
        int,
        Field(ge=1, le=MAX_PAGE_SIZE, description="The number of applications a page."),
    ] = 20,
) -> dict[str, Any]:
    """
    List the applications in the workspace: databases, application builders,
    automations and dashboards, with their id, name and type, in sidebar order.
    Returns one page, the total count, and whether more pages follow.
    """

    applications = visible_applications(ctx, types)
    total = applications.count()
    offset = (page - 1) * size
    return {
        "applications": [
            {
                "id": application.id,
                "name": application.name,
                "type": application_type_registry.get_by_model(
                    application.specific_class
                ).type,
            }
            for application in applications[offset : offset + size]
        ],
        "total": total,
        "page": page,
        "has_more": offset + size < total,
    }
