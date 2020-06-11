from django.db import models
from django.contrib.contenttypes.models import ContentType

from baserow.core.mixins import OrderableMixin, PolymorphicContentTypeMixin
from baserow.contrib.database.fields.models import Field


def get_default_view_content_type():
    return ContentType.objects.get_for_model(View)


class View(OrderableMixin, PolymorphicContentTypeMixin, models.Model):
    table = models.ForeignKey('database.Table', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name='content type',
        related_name='database_views',
        on_delete=models.SET(get_default_view_content_type)
    )

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, table):
        queryset = View.objects.filter(table=table)
        return cls.get_highest_order_of_queryset(queryset) + 1


class GridView(View):
    field_options = models.ManyToManyField(Field, through='GridViewFieldOptions')

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
                        grid_view=self,
                        field=field
                    )
                    field_options.append(field_option)

        return field_options


class GridViewFieldOptions(models.Model):
    grid_view = models.ForeignKey(GridView, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    # The defaults should be the same as in the `fieldCreated` of the `GridViewType`
    # abstraction in the web-frontend.
    width = models.PositiveIntegerField(default=200)

    class Meta:
        ordering = ('field_id',)
