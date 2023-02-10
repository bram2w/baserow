import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Q
from django.utils.functional import lazy

from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
)
from baserow.contrib.database.fields.models import Field, FileField
from baserow.contrib.database.views.registries import (
    form_view_mode_registry,
    view_filter_type_registry,
    view_type_registry,
)
from baserow.core.mixins import (
    CreatedAndUpdatedOnMixin,
    HierarchicalModelMixin,
    OrderableMixin,
    PolymorphicContentTypeMixin,
    TrashableModelMixin,
)
from baserow.core.models import UserFile
from baserow.core.utils import get_model_reference_field_name

FILTER_TYPES = ((FILTER_TYPE_AND, "And"), (FILTER_TYPE_OR, "Or"))

SORT_ORDER_ASC = "ASC"
SORT_ORDER_DESC = "DESC"
SORT_ORDER_CHOICES = ((SORT_ORDER_ASC, "Ascending"), (SORT_ORDER_DESC, "Descending"))

FORM_VIEW_SUBMIT_TEXT = "Submit"
FORM_VIEW_SUBMIT_ACTION_MESSAGE = "MESSAGE"
FORM_VIEW_SUBMIT_ACTION_REDIRECT = "REDIRECT"
FORM_VIEW_SUBMIT_ACTION_CHOICES = (
    (FORM_VIEW_SUBMIT_ACTION_MESSAGE, "Message"),
    (FORM_VIEW_SUBMIT_ACTION_REDIRECT, "Redirect"),
)

OWNERSHIP_TYPE_COLLABORATIVE = "collaborative"
DEFAULT_OWNERSHIP_TYPE = OWNERSHIP_TYPE_COLLABORATIVE
VIEW_OWNERSHIP_TYPES = [OWNERSHIP_TYPE_COLLABORATIVE]


def get_default_view_content_type():
    return ContentType.objects.get_for_model(View)


class View(
    HierarchicalModelMixin,
    TrashableModelMixin,
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
    slug = models.SlugField(
        default=secrets.token_urlsafe,
        help_text="The unique slug where the view can be accessed publicly on.",
        unique=True,
        db_index=True,
    )
    public = models.BooleanField(
        default=False,
        help_text="Indicates whether the view is publicly accessible to visitors.",
        db_index=True,
    )
    public_view_password = models.CharField(
        max_length=128,
        blank=True,
        help_text="The password required to access the public view URL.",
    )
    show_logo = models.BooleanField(
        default=True,
        help_text="Indicates whether the logo should be shown in the public view.",
    )
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    ownership_type = models.CharField(
        max_length=255,
        default=DEFAULT_OWNERSHIP_TYPE,
        help_text=(
            "Indicates how the access to the view is determined."
            " By default, views are collaborative and shared for all users"
            " that have access to the table."
        ),
    )

    @property
    def public_view_has_password(self) -> bool:
        """
        Indicates whether the public view is password protected or not.

        :return: True if the public view is password protected, False otherwise.
        """

        return self.public_view_password != ""  # nosec b105

    def get_parent(self):
        return self.table

    def rotate_slug(self):
        """
        Rotates the slug used to address this view.
        """

        self.slug = secrets.token_urlsafe()

    @staticmethod
    def create_new_slug() -> str:
        """
        Create a new slug for a view.

        :return: The new slug.
        """

        return secrets.token_urlsafe()

    @staticmethod
    def make_password(password: str) -> str:
        """
        Makes a password hash from the given password.

        :param password: The password to hash.
        :return: The hashed password.
        """

        return make_password(password)

    def set_password(self, password: str):
        """
        Sets the public view password.

        :param password: The password to set.
        """

        self.public_view_password = View.make_password(password)

    def check_public_view_password(self, password: str) -> bool:
        """
        Checks if the given password matches the public view password.

        :param password: The password to check.
        :return: True if the password matches, False otherwise.
        """

        if not self.public_view_has_password:
            return True
        return check_password(password, self.public_view_password)

    class Meta:
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, table):
        queryset = View.objects.filter(table=table)
        return cls.get_highest_order_of_queryset(queryset) + 1

    def get_field_options(self, create_if_missing=False, fields=None):
        """
        Each field can have unique options per view. This method returns those
        options per field type and can optionally create the missing ones. This method
        only works if the `field_options` property is a ManyToManyField with a relation
        to a field options model.

        :param create_if_missing: If true the missing GridViewFieldOptions are
            going to be created. If a fields has been created at a later moment it
            could be possible that they don't exist yet. If this value is True, the
            missing relationships are created in that case.
        :type create_if_missing: bool
        :param fields: If all the fields related to the table of this grid view have
            already been fetched, they can be provided here to avoid having to fetch
            them for a second time. This is only needed if `create_if_missing` is True.
        :type fields: list
        :return: A queryset containing all the field options of view.
        :rtype: QuerySet
        """

        view_type = view_type_registry.get_by_model(self.specific_class)
        through_model = view_type.field_options_model_class

        if not through_model:
            raise ValueError(
                f"The view type {view_type.type} does not support field options."
            )

        field_name = get_model_reference_field_name(through_model, View)

        if not field_name:
            raise ValueError(
                "The through model doesn't have a relationship with the View model or "
                "any descendants."
            )

        def get_queryset():
            return view_type.enhance_field_options_queryset(
                through_model.objects.filter(**{field_name: self})
            )

        field_options = get_queryset()

        if create_if_missing:
            fields_queryset = Field.objects.filter(table_id=self.table.id)

            if fields is None:
                field_count = fields_queryset.count()
            else:
                field_count = len(fields)

            # The check there are missing field options must be as efficient as
            # possible because this is being done a lot.
            if len(field_options) < field_count:
                if fields is None:
                    fields = fields_queryset

                with transaction.atomic():
                    # Lock the view so concurrent calls to this method wont create
                    # duplicate field options.
                    View.objects.filter(id=self.id).select_for_update(
                        of=("self",)
                    ).first()

                    # Invalidate the field options because they could have been
                    # changed concurrently.
                    field_options = get_queryset()

                    # In the case when field options are missing, we can be more
                    # in-efficient because this rarely happens. The most important part
                    # is that the check is fast.
                    existing_field_ids = [options.field_id for options in field_options]
                    through_model.objects.bulk_create(
                        [
                            through_model(**{field_name: self, "field": field})
                            for field in fields
                            if field.id not in existing_field_ids
                        ]
                    )

                # Invalidate the field options because new ones have been created and
                # we always want to return a queryset.
                field_options = get_queryset()

        return field_options


class ViewFilterManager(models.Manager):
    """
    Manager for the ViewFilter model.
    The View can be trashed and the filters are not deleted, therefore
    we need to filter out the trashed views.
    """

    def get_queryset(self):
        trashed_Q = Q(view__trashed=True) | Q(field__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class ViewFilter(HierarchicalModelMixin, models.Model):
    objects = ViewFilterManager()

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

    def get_parent(self):
        return self.view


class ViewDecorationManager(models.Manager):
    """
    Manager for the ViewDecoration model.
    The View can be trashed and the decorations are not deleted, therefore
    we need to filter out the trashed views.
    """

    def get_queryset(self):
        trashed_Q = Q(view__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class ViewDecoration(HierarchicalModelMixin, OrderableMixin, models.Model):
    objects = ViewDecorationManager()

    view = models.ForeignKey(
        View,
        on_delete=models.CASCADE,
        help_text="The view to which the decoration applies. Each view can have his own "
        "decorations.",
    )
    type = models.CharField(
        max_length=255,
        help_text=(
            "The decorator type. This is then interpreted by the frontend to "
            "display the decoration."
        ),
    )
    value_provider_type = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The value provider type that gives the value to the decorator.",
    )
    value_provider_conf = models.JSONField(
        default=dict,
        help_text="The configuration consumed by the value provider.",
    )
    # The default value is the maximum value of the small integer field because a newly
    # created decoration must always be last.
    order = models.SmallIntegerField(
        default=32767,
        help_text="The position of the decorator has within the view, lowest first. If "
        "there is another decorator with the same order value then the decorator "
        "with the lowest id must be shown first.",
    )

    @classmethod
    def get_last_order(cls, view):
        queryset = ViewDecoration.objects.filter(view=view)
        return cls.get_highest_order_of_queryset(queryset) + 1

    def get_parent(self):
        return self.view

    class Meta:
        ordering = ("order", "id")


class ViewSortManager(models.Manager):
    """
    Manager for the ViewSort model.
    The View can be trashed and the sorts are not deleted, therefore
    we need to filter out the trashed views.
    """

    def get_queryset(self):
        trashed_Q = Q(view__trashed=True) | Q(field__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class ViewSort(HierarchicalModelMixin, models.Model):
    objects = ViewSortManager()

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

    def get_parent(self):
        return self.view

    class Meta:
        ordering = ("id",)


class GridView(View):
    class RowIdentifierTypes(models.TextChoices):
        ID = "id"
        count = "count"

    # `field_options` is a very misleading name
    # it should probably be more like `fields_with_field_options`
    # since this field will return instances of `Field` not of
    # `GridViewFieldOptions`
    # We might want to change this in the future.
    field_options = models.ManyToManyField(Field, through="GridViewFieldOptions")
    row_identifier_type = models.CharField(
        choices=RowIdentifierTypes.choices, default="id", max_length=10
    )


class GridViewFieldOptionsManager(models.Manager):
    """
    Manager for the GridViewFieldOptions model.
    The View can be trashed and the field options are not deleted, therefore
    we need to filter out the trashed views.
    """

    def get_queryset(self):
        trashed_Q = Q(grid_view__trashed=True) | Q(field__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class GridViewFieldOptions(HierarchicalModelMixin, models.Model):
    objects = GridViewFieldOptionsManager()
    objects_and_trash = models.Manager()

    grid_view = models.ForeignKey(GridView, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    # The defaults should match the ones in `afterFieldCreated` of the `GridViewType`
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

    aggregation_type = models.CharField(
        default="",
        blank=True,
        max_length=48,
        help_text=(
            "Indicates how the field value is aggregated. This value is "
            "different from the `aggregation_raw_type`. The `aggregation_raw_type` "
            "is the value extracted from "
            "the database, while the `aggregation_type` can implies further "
            "calculations. For example: "
            "if you want to compute an average, `sum` is going to be the "
            "`aggregation_raw_type`, "
            "the value extracted from database, and `sum / row_count` will be the "
            "aggregation result displayed to the user. "
            "This aggregation_type should be used by the client to compute the final "
            "value."
        ),
    )

    aggregation_raw_type = models.CharField(
        default="",
        blank=True,
        max_length=48,
        help_text=(
            "Indicates how to compute the raw aggregation value from database. "
            "This type must be registered in the backend prior to use it."
        ),
    )

    def get_parent(self):
        return self.grid_view

    class Meta:
        ordering = ("field_id",)


class GalleryView(View):
    field_options = models.ManyToManyField(Field, through="GalleryViewFieldOptions")
    card_cover_image_field = models.ForeignKey(
        FileField,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="gallery_view_card_cover_field",
        help_text="References a file field of which the first image must be shown as "
        "card cover image.",
    )


class GalleryViewFieldOptionsManager(models.Manager):
    """
    The View can be trashed and the field options are not deleted, therefore
    we need to filter out the trashed views.
    """

    def get_queryset(self):
        trashed_Q = Q(gallery_view__trashed=True) | Q(field__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class GalleryViewFieldOptions(HierarchicalModelMixin, models.Model):
    objects = GalleryViewFieldOptionsManager()
    objects_and_trash = models.Manager()

    gallery_view = models.ForeignKey(GalleryView, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    hidden = models.BooleanField(
        default=True,
        help_text="Whether or not the field should be hidden in the card.",
    )
    # The default value is the maximum value of the small integer field because a newly
    # created field must always be last.
    order = models.SmallIntegerField(
        default=32767,
        help_text="The order that the field has in the form. Lower value is first.",
    )

    def get_parent(self):
        return self.gallery_view

    class Meta:
        ordering = (
            "order",
            "field_id",
        )


class FormView(View):
    field_options = models.ManyToManyField(Field, through="FormViewFieldOptions")
    title = models.TextField(
        blank=True,
        help_text="The title that is displayed at the beginning of the form.",
    )
    description = models.TextField(
        blank=True,
        help_text="The description that is displayed at the beginning of the form.",
    )
    mode = models.TextField(
        max_length=64,
        default=lazy(form_view_mode_registry.get_default_choice, str)(),
        choices=lazy(form_view_mode_registry.get_choices, list)(),
        help_text="Configurable mode of the form.",
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
    submit_text = models.TextField(
        default=FORM_VIEW_SUBMIT_TEXT,
        help_text="The text displayed on the submit button.",
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

    @property
    def active_field_options(self):
        return (
            FormViewFieldOptions.objects.filter(form_view=self, enabled=True)
            .select_related("field")
            .prefetch_related("conditions")
            .order_by("order")
        )


class FormViewFieldOptionsManager(models.Manager):
    """
    The View can be trashed and the field options are not deleted, therefore
    we need to filter out the trashed views.
    """

    def get_queryset(self):
        trashed_Q = Q(form_view__trashed=True) | Q(field__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class FormViewFieldOptions(HierarchicalModelMixin, models.Model):
    objects = FormViewFieldOptionsManager()
    objects_and_trash = models.Manager()

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
    show_when_matching_conditions = models.BooleanField(
        default=False,
        help_text="Indicates whether this field is visible when the conditions are "
        "met.",
    )
    condition_type = models.CharField(
        max_length=3,
        choices=FILTER_TYPES,
        default=FILTER_TYPE_AND,
        help_text="Indicates whether all (AND) or any (OR) of the conditions should "
        "match before shown.",
    )
    # The default value is the maximum value of the small integer field because a newly
    # created field must always be last.
    order = models.SmallIntegerField(
        default=32767,
        help_text="The order that the field has in the form. Lower value is first.",
    )

    def get_parent(self):
        return self.form_view

    class Meta:
        ordering = (
            "order",
            "field_id",
        )

    def is_required(self):
        return (
            self.required
            # If the field is only visible when conditions are met, we can't do a
            # required backend validation because there is no way of knowing whether
            # the provided values match the conditions in the backend.
            and (
                not self.show_when_matching_conditions
                or len(self.conditions.all()) == 0
            )
        )


class FormViewFieldOptionsConditionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(~Q(field__trashed=True))


class FormViewFieldOptionsCondition(HierarchicalModelMixin, models.Model):
    field_option = models.ForeignKey(
        FormViewFieldOptions,
        on_delete=models.CASCADE,
        help_text="The form view option where the condition is related to.",
        related_name="conditions",
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
    objects = FormViewFieldOptionsConditionManager()

    def get_parent(self):
        return self.field_option

    class Meta:
        ordering = ("id",)
