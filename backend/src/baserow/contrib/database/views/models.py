import secrets

from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.core.utils import get_model_reference_field_name
from baserow.core.models import UserFile
from baserow.core.mixins import (
    OrderableMixin,
    PolymorphicContentTypeMixin,
    CreatedAndUpdatedOnMixin,
)
from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.views.registries import (
    view_type_registry,
    view_filter_type_registry,
)
from baserow.contrib.database.mixins import (
    ParentTableTrashableModelMixin,
    ParentFieldTrashableModelMixin,
)

FILTER_TYPES = ((FILTER_TYPE_AND, "And"), (FILTER_TYPE_OR, "Or"))

SORT_ORDER_ASC = "ASC"
SORT_ORDER_DESC = "DESC"
SORT_ORDER_CHOICES = ((SORT_ORDER_ASC, "Ascending"), (SORT_ORDER_DESC, "Descending"))

FORM_VIEW_SUBMIT_ACTION_MESSAGE = "MESSAGE"
FORM_VIEW_SUBMIT_ACTION_REDIRECT = "REDIRECT"
FORM_VIEW_SUBMIT_ACTION_CHOICES = (
    (FORM_VIEW_SUBMIT_ACTION_MESSAGE, "Message"),
    (FORM_VIEW_SUBMIT_ACTION_REDIRECT, "Redirect"),
)


def get_default_view_content_type():
    return ContentType.objects.get_for_model(View)


class View(
    ParentTableTrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    PolymorphicContentTypeMixin,
    models.Model,
):
    table = models.ForeignKey("database.Table", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="database_views",
        on_delete=models.SET(get_default_view_content_type),
    )
    filter_type = models.CharField(
        max_length=3,
        choices=FILTER_TYPES,
        default=FILTER_TYPE_AND,
        help_text="Indicates whether all the rows should apply to all filters (AND) "
        "or to any filter (OR).",
    )
    filters_disabled = models.BooleanField(
        default=False,
        help_text="Allows users to see results unfiltered while still keeping "
        "the filters saved for the view.",
    )

    class Meta:
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, table):
        queryset = View.objects.filter(table=table)
        return cls.get_highest_order_of_queryset(queryset) + 1

    def get_field_options(self, create_if_not_exists=False, fields=None):
        """
        Each field can have unique options per view. This method returns those
        options per field type and can optionally create the missing ones. This method
        only works if the `field_options` property is a ManyToManyField with a relation
        to a field options model.

        :param create_if_not_exists: If true the missing GridViewFieldOptions are
            going to be created. If a fields has been created at a later moment it
            could be possible that they don't exist yet. If this value is True, the
            missing relationships are created in that case.
        :type create_if_not_exists: bool
        :param fields: If all the fields related to the table of this grid view have
            already been fetched, they can be provided here to avoid having to fetch
            them for a second time. This is only needed if `create_if_not_exists` is
            True.
        :type fields: list
        :return: A list of field options instances related to this grid view.
        :rtype: list or QuerySet
        """

        view_type = view_type_registry.get_by_model(self.specific_class)
        through_model = view_type.field_options_model_class

        if not through_model:
            raise ValueError(
                f"The view type {view_type.type} does not support field " f"options."
            )

        field_name = get_model_reference_field_name(through_model, View)

        if not field_name:
            raise ValueError(
                "The through model doesn't have a relationship with the View model or "
                "any descendants."
            )

        field_options = through_model.objects.filter(**{field_name: self})

        if create_if_not_exists:
            field_options = list(field_options)
            if not fields:
                fields = Field.objects.filter(table=self.table)

            existing_field_ids = [options.field_id for options in field_options]
            for field in fields:
                if field.id not in existing_field_ids:
                    field_option = through_model.objects.create(
                        **{field_name: self, "field": field}
                    )
                    field_options.append(field_option)

        return field_options


class ViewFilter(ParentFieldTrashableModelMixin, models.Model):
    view = models.ForeignKey(
        View,
        on_delete=models.CASCADE,
        help_text="The view to which the filter applies. Each view can have his own "
        "filters.",
    )
    field = models.ForeignKey(
        "database.Field",
        on_delete=models.CASCADE,
        help_text="The field of which the value must be compared to the filter value.",
    )
    type = models.CharField(
        max_length=48,
        help_text="Indicates how the field's value must be compared to the filter's "
        "value. The filter is always in this order `field` `type` `value` "
        "(example: `field_1` `contains` `Test`).",
    )
    value = models.CharField(
        max_length=255,
        blank=True,
        help_text="The filter value that must be compared to the field's value.",
    )

    class Meta:
        ordering = ("id",)

    @property
    def preload_values(self):
        return view_filter_type_registry.get(self.type).get_preload_values(self)


class ViewSort(ParentFieldTrashableModelMixin, models.Model):
    view = models.ForeignKey(
        View,
        on_delete=models.CASCADE,
        help_text="The view to which the sort applies. Each view can have his own "
        "sortings.",
    )
    field = models.ForeignKey(
        "database.Field",
        on_delete=models.CASCADE,
        help_text="The field that must be sorted on.",
    )
    order = models.CharField(
        max_length=4,
        choices=SORT_ORDER_CHOICES,
        help_text="Indicates the sort order direction. ASC (Ascending) is from A to Z "
        "and DESC (Descending) is from Z to A.",
        default=SORT_ORDER_ASC,
    )

    class Meta:
        ordering = ("id",)


class GridView(View):
    field_options = models.ManyToManyField(Field, through="GridViewFieldOptions")


class GridViewFieldOptions(ParentFieldTrashableModelMixin, models.Model):
    grid_view = models.ForeignKey(GridView, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    # The defaults should be the same as in the `fieldCreated` of the `GridViewType`
    # abstraction in the web-frontend.
    width = models.PositiveIntegerField(
        default=200,
        help_text="The width of the table field in the related view.",
    )
    hidden = models.BooleanField(
        default=False,
        help_text="Whether or not the field should be hidden in the current view.",
    )
    # The default value is the maximum value of the small integer field because a newly
    # created field must always be last.
    order = models.SmallIntegerField(
        default=32767,
        help_text="The position that the field has within the view, lowest first. If "
        "there is another field with the same order value then the field with the "
        "lowest id must be shown first.",
    )

    class Meta:
        ordering = ("field_id",)


class FormView(View):
    field_options = models.ManyToManyField(Field, through="FormViewFieldOptions")
    slug = models.SlugField(
        default=secrets.token_urlsafe,
        help_text="The unique slug where the form can be accessed publicly on.",
        unique=True,
        db_index=True,
    )
    public = models.BooleanField(
        default=False,
        help_text="Indicates whether the form is publicly accessible to visitors and "
        "if they can fill it out.",
    )
    title = models.TextField(
        blank=True,
        help_text="The title that is displayed at the beginning of the form.",
    )
    description = models.TextField(
        blank=True,
        help_text="The description that is displayed at the beginning of the form.",
    )
    cover_image = models.ForeignKey(
        UserFile,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="form_view_cover_image",
        help_text="The user file cover image that is displayed at the top of the form.",
    )
    logo_image = models.ForeignKey(
        UserFile,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="form_view_logo_image",
        help_text="The user file logo image that is displayed at the top of the form.",
    )
    submit_action = models.CharField(
        max_length=32,
        choices=FORM_VIEW_SUBMIT_ACTION_CHOICES,
        default=FORM_VIEW_SUBMIT_ACTION_MESSAGE,
        help_text="The action that must be performed after the visitor has filled out "
        "the form.",
    )
    submit_action_message = models.TextField(
        blank=True,
        help_text=f"If the `submit_action` is {FORM_VIEW_SUBMIT_ACTION_MESSAGE}, "
        f"then this message will be shown to the visitor after submitting the form.",
    )
    submit_action_redirect_url = models.URLField(
        blank=True,
        help_text=f"If the `submit_action` is {FORM_VIEW_SUBMIT_ACTION_REDIRECT},"
        f"then the visitors will be redirected to the this URL after submitting the "
        f"form.",
    )

    def rotate_slug(self):
        self.slug = secrets.token_urlsafe()

    @property
    def active_field_options(self):
        return (
            FormViewFieldOptions.objects.filter(form_view=self, enabled=True)
            .select_related("field")
            .order_by("order")
        )


class FormViewFieldOptions(ParentFieldTrashableModelMixin, models.Model):
    form_view = models.ForeignKey(FormView, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text="By default, the name of the related field will be shown to the "
        "visitor. Optionally another name can be used by setting this name.",
    )
    description = models.TextField(
        blank=True,
        help_text="If provided, then this value be will be shown under the field name.",
    )
    enabled = models.BooleanField(
        default=False, help_text="Indicates whether the field is included in the form."
    )
    required = models.BooleanField(
        default=True,
        help_text="Indicates whether the field is required for the visitor to fill "
        "out.",
    )
    # The default value is the maximum value of the small integer field because a newly
    # created field must always be last.
    order = models.SmallIntegerField(
        default=32767,
        help_text="The order that the field has in the form. Lower value is first.",
    )

    class Meta:
        ordering = (
            "order",
            "field_id",
        )
