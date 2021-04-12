from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
)
from baserow.contrib.database.fields.models import Field
from baserow.core.mixins import (
    OrderableMixin,
    PolymorphicContentTypeMixin,
    CreatedAndUpdatedOnMixin,
)

FILTER_TYPES = ((FILTER_TYPE_AND, "And"), (FILTER_TYPE_OR, "Or"))

SORT_ORDER_ASC = "ASC"
SORT_ORDER_DESC = "DESC"
SORT_ORDER_CHOICES = ((SORT_ORDER_ASC, "Ascending"), (SORT_ORDER_DESC, "Descending"))


def get_default_view_content_type():
    return ContentType.objects.get_for_model(View)


class View(
    CreatedAndUpdatedOnMixin, OrderableMixin, PolymorphicContentTypeMixin, models.Model
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


class ViewFilter(models.Model):
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


class ViewSort(models.Model):
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

    def get_field_options(self, create_if_not_exists=False, fields=None):
        """
        Each field can have unique options per view. This method returns those
        options per field type and can optionally create the missing ones.

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
        :rtype: list
        """

        field_options = GridViewFieldOptions.objects.filter(grid_view=self)

        if create_if_not_exists:
            field_options = list(field_options)
            if not fields:
                fields = Field.objects.filter(table=self.table)

            existing_field_ids = [options.field_id for options in field_options]
            for field in fields:
                if field.id not in existing_field_ids:
                    field_option = GridViewFieldOptions.objects.create(
                        grid_view=self, field=field
                    )
                    field_options.append(field_option)

        return field_options


class GridViewFieldOptions(models.Model):
    grid_view = models.ForeignKey(GridView, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    # The defaults should be the same as in the `fieldCreated` of the `GridViewType`
    # abstraction in the web-frontend.
    width = models.PositiveIntegerField(default=200)
    hidden = models.BooleanField(default=False)
    # The default value is the maximum value of the small integer field because a newly
    # created field must always be last.
    order = models.SmallIntegerField(default=32767)

    class Meta:
        ordering = ("field_id",)
