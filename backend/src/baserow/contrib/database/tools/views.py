from collections import defaultdict
from typing import Annotated, Any

from django.utils.translation import gettext as _

from pydantic import BaseModel, ConfigDict, Field, model_serializer

from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import FormView, View
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.tools import ToolContext


class FormFieldOption(BaseModel):
    model_config = ConfigDict(extra="forbid", coerce_numbers_to_str=True)

    field_id: int = Field(..., description="Field ID.")
    name: str = Field(..., description="Display name in form.")
    description: str = Field(..., description="Field description, or ''.")
    required: bool = Field(..., description="Required?")
    order: int = Field(..., description="Sort order.")


def _form_field_option(fo) -> FormFieldOption:
    return FormFieldOption(
        field_id=fo.field_id,
        name=fo.name,
        description=fo.description,
        required=fo.required,
        order=fo.order,
    )


def _form_field_options_from_orm(orm_view):
    return [_form_field_option(fo) for fo in orm_view.active_field_options.all()]


def _form_field_options_by_view(views: list[View]) -> dict[int, list]:
    """The active field options of the form views among ``views``, in one query."""

    form_ids = [view.id for view in views if isinstance(view, FormView)]
    if not form_ids:
        return {}
    by_view = defaultdict(list)
    options = (
        FormView.active_field_options_in(views[0].table.database.workspace)
        .filter(form_view_id__in=form_ids)
        .order_by("order")
    )
    for fo in options:
        by_view[fo.form_view_id].append(_form_field_option(fo))
    return by_view


_FROM_DJANGO_ORM: dict[str, Any] = {
    "grid": lambda v: {"row_height": v.row_height_size},
    "kanban": lambda v: {"column_field_id": v.single_select_field_id},
    "calendar": lambda v: {"date_field_id": v.date_field_id},
    "gallery": lambda v: {"cover_field_id": v.card_cover_image_field_id},
    "timeline": lambda v: {
        "start_date_field_id": v.start_date_field_id,
        "end_date_field_id": v.end_date_field_id,
    },
}


class ViewItem(BaseModel):
    """An existing view, with the settings of its type."""

    model_config = ConfigDict(extra="forbid", coerce_numbers_to_str=True)

    id: int = Field(...)
    name: str = Field(...)
    public: bool = Field(...)
    type: str = Field(...)

    # Type-specific (populated per type, others excluded via serializer)
    row_height: str | None = None
    column_field_id: int | None = None
    date_field_id: int | None = None
    cover_field_id: int | None = None
    start_date_field_id: int | None = None
    end_date_field_id: int | None = None
    title: str | None = None
    description: str | None = None
    field_options: list[FormFieldOption] | None = None

    @model_serializer(mode="wrap")
    def _exclude_none(self, handler):
        return {k: v for k, v in handler(self).items() if v is not None}

    @classmethod
    def from_django_orm(
        cls, orm_view: View, form_field_options: list | None = None
    ) -> "ViewItem":
        """
        :param form_field_options: The field options of a form view, when the caller
            loaded them for several views at once. Otherwise they are queried.
        """

        view_type = view_type_registry.get_by_model(orm_view).type
        kwargs: dict[str, Any] = {
            "id": orm_view.id,
            "name": orm_view.name,
            "public": orm_view.public,
            "type": view_type,
        }
        builder = _FROM_DJANGO_ORM.get(view_type)
        if builder:
            kwargs.update(builder(orm_view))
        if view_type == "form":
            if form_field_options is None:
                form_field_options = _form_field_options_from_orm(orm_view)
            kwargs.update(
                title=orm_view.title,
                description=orm_view.description,
                field_options=form_field_options,
            )
        return cls(**kwargs)


def list_views(
    ctx: ToolContext,
    table_id: Annotated[
        int, Field(description="The ID of the table to list views for.")
    ],
) -> dict[str, Any]:
    """
    List the views of a table, at most 100, with their id, name, type and the
    settings of their type.
    """

    table = (
        TableHandler().list_workspace_tables(ctx.user, ctx.workspace).get(id=table_id)
    )
    ctx.update_status(
        _("Listing views in %(table_name)s...") % {"table_name": table.name}
    )
    views = ViewHandler().list_views(
        ctx.user,
        table,
        filters=False,
        sortings=False,
        decorations=False,
        group_bys=False,
        limit=100,
        prefetch_field_options=False,
    )
    views = list(views)
    form_options = _form_field_options_by_view(views)
    return {
        "views": [
            ViewItem.from_django_orm(view, form_options.get(view.id, [])).model_dump()
            for view in views
        ]
    }
