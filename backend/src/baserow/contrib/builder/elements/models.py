from typing import TYPE_CHECKING, Optional

from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import SET_NULL, QuerySet

from baserow.core.formula.field import FormulaField
from baserow.core.mixins import (
    CreatedAndUpdatedOnMixin,
    FractionOrderableMixin,
    HierarchicalModelMixin,
    PolymorphicContentTypeMixin,
    TrashableModelMixin,
    WithRegistry,
)
from baserow.core.user_files.models import UserFile

if TYPE_CHECKING:
    from baserow.contrib.builder.pages.models import Page


class HorizontalAlignments(models.TextChoices):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalAlignments(models.TextChoices):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class WIDTHS(models.TextChoices):
    AUTO = "auto"
    FULL = "full"


class BackgroundTypes(models.TextChoices):
    NONE = "none"
    COLOR = "color"


class WidthTypes(models.TextChoices):
    FULL = "full"
    NORMAL = "normal"
    MEDIUM = "medium"
    SMALL = "small"


def get_default_element_content_type():
    return ContentType.objects.get_for_model(Element)


class Element(
    HierarchicalModelMixin,
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    FractionOrderableMixin,
    PolymorphicContentTypeMixin,
    WithRegistry,
    models.Model,
):
    """
    This model represents a page element. An element is a piece of the page that
    display an information or something the user can interact with.
    """

    page = models.ForeignKey("builder.Page", on_delete=models.CASCADE)
    order = models.DecimalField(
        help_text="Lowest first.",
        max_digits=40,
        decimal_places=20,
        editable=False,
        default=1,
    )
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="page_elements",
        on_delete=models.SET(get_default_element_content_type),
    )
    # This is used for container elements, if NULL then this is a root element
    parent_element = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        default=None,
        help_text="The parent element, if inside a container.",
        related_name="children",
    )

    # The following fields are used to store the position of the element in the
    # container. If the element is a root element then this is null.
    place_in_container = models.CharField(
        null=True,
        blank=True,
        default=None,
        max_length=255,
        help_text="The place in the container.",
    )

    style_border_top_color = models.CharField(
        max_length=20,
        default="border",
        blank=True,
        help_text="Top border color.",
    )
    style_border_top_size = models.PositiveIntegerField(
        default=0, help_text="Pixel height of the top border."
    )
    style_padding_top = models.PositiveIntegerField(
        default=10, help_text="Padding size of the top border."
    )

    style_border_bottom_color = models.CharField(
        max_length=20,
        default="border",
        blank=True,
        help_text="Bottom border color",
    )
    style_border_bottom_size = models.PositiveIntegerField(
        default=0, help_text="Pixel height of the bottom border."
    )
    style_padding_bottom = models.PositiveIntegerField(
        default=10, help_text="Padding size of the bottom border."
    )

    style_border_left_color = models.CharField(
        max_length=20,
        default="border",
        blank=True,
        help_text="Left border color",
    )
    style_border_left_size = models.PositiveIntegerField(
        default=0, help_text="Pixel height of the left border."
    )
    style_padding_left = models.PositiveIntegerField(
        default=20, help_text="Padding size of the left border."
    )

    style_border_right_color = models.CharField(
        max_length=20,
        default="border",
        blank=True,
        help_text="Right border color",
    )
    style_border_right_size = models.PositiveIntegerField(
        default=0, help_text="Pixel height of the right border."
    )
    style_padding_right = models.PositiveIntegerField(
        default=20, help_text="Padding size of the right border."
    )

    style_background = models.CharField(
        choices=BackgroundTypes.choices,
        default=BackgroundTypes.NONE,
        help_text="What type of background the element should have.",
        max_length=20,
    )
    style_background_color = models.CharField(
        max_length=20,
        default="#ffffffff",
        blank=True,
        help_text="The background color if `style_background` is color.",
    )

    style_width = models.CharField(
        choices=WidthTypes.choices,
        default=WidthTypes.NORMAL,
        help_text="Indicates the width of the element.",
        max_length=20,
    )

    class Meta:
        ordering = ("order", "id")

    @staticmethod
    def get_type_registry():
        from .registries import element_type_registry

        return element_type_registry

    def get_parent(self):
        return self.page

    def get_sibling_elements(self):
        return Element.objects.filter(
            parent_element=self.parent_element, page=self.page
        ).exclude(id=self.id)

    @property
    def is_root_element(self):
        return self.parent_element is None

    @classmethod
    def get_last_order(
        cls,
        page: "Page",
        parent_element_id: Optional[int] = None,
        place_in_container: Optional[str] = None,
    ):
        """
        Returns the last order for the given page.

        :param page: The page we want the order for.
        :param base_queryset: The base queryset to use.
        :return: The last order.
        """

        return cls.get_last_orders(page, parent_element_id, place_in_container)[0]

    @classmethod
    def get_last_orders(
        cls,
        page: "Page",
        parent_element_id: Optional[int] = None,
        place_in_container: Optional[str] = None,
        amount=1,
    ):
        """
        Returns the last orders for the given page.

        :param page: The page we want the order for.
        :param parent_element_id: The id of the parent element.
        :param place_in_container: The place in the container
        :param amount: The number of orders you wish to have returned
        :return: The last order.
        """

        queryset = Element.objects.filter(page=page)

        queryset = cls._scope_queryset_to_container(
            queryset, parent_element_id, place_in_container
        )

        return cls.get_highest_order_of_queryset(queryset, amount=amount)

    @classmethod
    def get_unique_order_before_element(
        cls, before: "Element", parent_element_id: int, place_in_container: str
    ):
        """
        Returns a safe order value before the given element in the given page.

        :param before: The element before which we want the safe order
        :param parent_element_id: The id of the parent element.
        :param place_in_container: The place in the container
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the items must be recalculated in this
            case before calling this method again.
        :return: The order value.
        """

        queryset = Element.objects.filter(page=before.page)

        queryset = cls._scope_queryset_to_container(
            queryset, parent_element_id, place_in_container
        )

        return cls.get_unique_orders_before_item(before, queryset)[0]

    @classmethod
    def _scope_queryset_to_container(
        cls, queryset: QuerySet, parent_element_id: int, place_in_container: str
    ) -> QuerySet:
        """
        Filters the queryset to only include elements that are in the same container
        as the child element.

        :param queryset: The queryset to filter.
        :param parent_element_id: The ID of the parent element.
        :param place_in_container: The place in container of the child element.
        :return: The filtered queryset.
        """

        if parent_element_id:
            return queryset.filter(
                parent_element_id=parent_element_id,
                place_in_container=place_in_container,
            )
        else:
            return queryset.filter(
                parent_element_id=None,
            )


class ContainerElement(Element):
    """
    Base class for container elements.
    """

    class Meta:
        abstract = True


class ColumnElement(ContainerElement):
    """
    A column element that can contain other elements.
    """

    column_amount = models.IntegerField(
        default=3,
        help_text="The amount of columns inside this column element.",
        validators=[
            MinValueValidator(1, message="Value cannot be less than 0."),
            MaxValueValidator(6, message="Value cannot be greater than 6."),
        ],
    )
    column_gap = models.IntegerField(
        default=20,
        help_text="The amount of space between the columns.",
        validators=[
            MinValueValidator(0, message="Value cannot be less than 0."),
            MaxValueValidator(2000, message="Value cannot be greater than 2000."),
        ],
    )
    alignment = models.CharField(
        choices=VerticalAlignments.choices,
        max_length=10,
        default=VerticalAlignments.TOP,
    )


class HeadingElement(Element):
    """
    A Heading element to display a title.
    """

    class HeadingLevel(models.IntegerChoices):
        H1 = 1
        H2 = 2
        H3 = 3
        H4 = 4
        H5 = 5

    value = FormulaField(default="")
    level = models.IntegerField(
        choices=HeadingLevel.choices, default=1, help_text="The level of the heading"
    )
    font_color = models.CharField(
        max_length=20,
        default="default",
        blank=True,
        help_text="The font color of the heading",
    )
    alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )


class TextElement(Element):
    """
    A simple blob of text.
    """

    class TEXT_FORMATS(models.TextChoices):
        PLAIN = "plain"
        MARKDOWN = "markdown"

    value = FormulaField(default="")
    alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    format = models.CharField(
        choices=TEXT_FORMATS.choices,
        help_text="The format of the text",
        max_length=10,
        default=TEXT_FORMATS.PLAIN,
    )


class LinkElement(Element):
    """
    A simple link.
    """

    class NAVIGATION_TYPES(models.TextChoices):
        PAGE = "page"
        CUSTOM = "custom"

    class VARIANTS(models.TextChoices):
        LINK = "link"
        BUTTON = "button"

    class TARGETS(models.TextChoices):
        SELF = "self"
        BLANK = "blank"

    value = FormulaField(default="")
    navigation_type = models.CharField(
        choices=NAVIGATION_TYPES.choices,
        help_text="The navigation type.",
        max_length=10,
        default=NAVIGATION_TYPES.PAGE,
    )
    navigate_to_page = models.ForeignKey(
        "builder.Page",
        null=True,
        on_delete=models.SET_NULL,
        help_text=(
            "Destination page id for this link. If null then we use the "
            "navigate_to_url property instead.",
        ),
    )
    navigate_to_url = FormulaField(
        default="",
        help_text="If no page is selected, this indicate the destination of the link.",
    )
    page_parameters = models.JSONField(
        default=list,
        help_text="The parameters for each parameters of the selected page if any.",
    )

    variant = models.CharField(
        choices=VARIANTS.choices,
        help_text="The variant of the link.",
        max_length=10,
        default=VARIANTS.LINK,
    )
    target = models.CharField(
        choices=TARGETS.choices,
        help_text="The target of the link when we click on it.",
        max_length=10,
        default=TARGETS.SELF,
    )
    width = models.CharField(
        choices=WIDTHS.choices,
        max_length=10,
        default=WIDTHS.AUTO,
    )
    alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    button_color = models.CharField(
        max_length=20,
        default="primary",
        blank=True,
        help_text="The color of the button",
    )


class ImageElement(Element):
    """
    A simple image element that can display an image either through a remote source
    or via an uploaded file
    """

    class IMAGE_SOURCE_TYPES(models.TextChoices):
        UPLOAD = "upload"
        URL = "url"

    class IMAGE_CONSTRAINT_TYPES(models.TextChoices):
        COVER = "cover"
        CONTAIN = "contain"
        FULL_WIDTH = "full-width"

    image_source_type = models.CharField(
        choices=IMAGE_SOURCE_TYPES.choices,
        max_length=32,
        default=IMAGE_SOURCE_TYPES.UPLOAD,
    )
    image_file = models.ForeignKey(
        UserFile,
        null=True,
        on_delete=models.SET_NULL,
        related_name="image_element_image_file",
        help_text="An image file uploaded by the user to be used by the element",
    )
    image_url = FormulaField(
        help_text="A link to the image file", blank=True, default="", max_length=1000
    )
    alt_text = FormulaField(
        help_text="Text that is displayed when the image can't load",
        default="",
        blank=True,
    )
    alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    style_max_width = models.PositiveIntegerField(
        null=True,
        help_text="The max-width for this image element.",
        default=100,
        validators=[
            MinValueValidator(0, message="Value cannot be less than 0."),
            MaxValueValidator(100, message="Value cannot be greater than 100."),
        ],
    )
    style_max_height = models.PositiveIntegerField(
        null=True,
        help_text="The max-height for this image element.",
        validators=[
            MinValueValidator(5, message="Value cannot be less than 5."),
            MaxValueValidator(3000, message="Value cannot be greater than 3000."),
        ],
    )
    style_image_constraint = models.CharField(
        help_text="The image constraint to apply to this image",
        choices=IMAGE_CONSTRAINT_TYPES.choices,
        max_length=32,
        default=IMAGE_CONSTRAINT_TYPES.CONTAIN,
    )


class InputElement(Element):
    """
    The base input element, which can be extended to
    support an element for each supported type.
    """

    class Meta:
        abstract = True


class InputTextElement(InputElement):
    """
    An input element of text type.
    """

    label = FormulaField(
        default="",
        help_text="The text label for this input",
    )
    default_value = FormulaField(
        default="", help_text="This text input's default value."
    )
    required = models.BooleanField(
        default=False, help_text="Whether this text input is a required field."
    )
    placeholder = FormulaField(
        default="",
        help_text="The placeholder text which should be applied to the element.",
    )
    is_multiline = models.BooleanField(
        default=False,
        help_text="Whether this text input is multiline.",
    )
    rows = models.PositiveIntegerField(
        default=3,
        help_text="Number of rows displayed by the rendered input element",
    )


class ButtonElement(Element):
    """
    A button element
    """

    value = FormulaField(default="", help_text="The caption of the button.")
    width = models.CharField(
        choices=WIDTHS.choices,
        max_length=10,
        default=WIDTHS.AUTO,
    )
    alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    button_color = models.CharField(
        max_length=20,
        default="primary",
        blank=True,
        help_text="The color of the button",
    )


class CollectionField(models.Model):
    """
    A field of a Collection element
    """

    order = models.PositiveIntegerField()
    name = models.CharField(
        max_length=225,
        help_text="The name of the field.",
    )

    type = models.CharField(
        max_length=225,
        help_text="The type of the field.",
    )

    config = models.JSONField(
        default=dict,
        help_text="The configuration of the field.",
    )

    def get_type(self):
        """Returns the type for this model instance"""

        from .registries import collection_field_type_registry

        return collection_field_type_registry.get(self.type)

    class Meta:
        ordering = ("order", "id")


class CollectionElement(Element):
    data_source = models.ForeignKey(
        "builder.DataSource",
        null=True,
        on_delete=SET_NULL,
        help_text="The data source we want to show in the element for. "
        "Only data_sources that return list are allowed.",
    )

    items_per_page = models.PositiveIntegerField(
        default=20,
        help_text="The amount item loaded with each page.",
        validators=[
            MinValueValidator(1, message="Value cannot be less than 1."),
            MaxValueValidator(100, message="Value cannot be greater than 100."),
        ],
    )

    fields = models.ManyToManyField(CollectionField)

    class Meta:
        abstract = True


class TableElement(CollectionElement):
    """
    A table element
    """

    button_color = models.CharField(
        max_length=20,
        default="primary",
        blank=True,
        help_text="The color of the button",
    )


class FormContainerElement(ContainerElement):
    """
    A form element
    """

    submit_button_label = FormulaField(default="")

    button_color = models.CharField(
        max_length=20,
        default="primary",
        blank=True,
        help_text="The color of the button",
    )


class DropdownElement(Element):
    label = FormulaField(
        default="",
        help_text="The text label for this dropdown",
    )
    default_value = FormulaField(
        default="", help_text="This dropdowns input's default value."
    )
    required = models.BooleanField(
        default=False, help_text="Whether this drodpown is a required field."
    )
    placeholder = FormulaField(
        default="",
        help_text="The placeholder text which should be applied to the element.",
    )


class DropdownElementOption(models.Model):
    value = models.TextField(
        blank=True, default="", help_text="The value of the option"
    )
    name = models.TextField(
        blank=True, default="", help_text="The display name of the option"
    )
    dropdown = models.ForeignKey(DropdownElement, on_delete=models.CASCADE)


class CheckboxElement(InputElement):
    """
    A checkbox element.
    """

    label = FormulaField(
        default="",
        help_text="The text label for this input",
    )
    default_value = FormulaField(default="", help_text="The input's default value.")
    required = models.BooleanField(
        default=False, help_text="Whether this input is a required field."
    )


class IFrameElement(Element):
    """
    An element for embedding external resources in the application.
    """

    class IFRAME_SOURCE_TYPE(models.TextChoices):
        URL = "url"
        EMBED = "embed"

    source_type = models.CharField(
        choices=IFRAME_SOURCE_TYPE.choices,
        max_length=32,
        default=IFRAME_SOURCE_TYPE.URL,
    )
    url = FormulaField(
        help_text="A link to the page to embed",
        blank=True,
        default="",
    )
    embed = FormulaField(help_text="Inline HTML to embed", blank=True, default="")
    height = models.PositiveIntegerField(
        help_text="Height in pixels of the iframe",
        default=300,
    )
