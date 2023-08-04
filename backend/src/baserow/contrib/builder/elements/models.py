from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.contrib.builder.pages.models import Page
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


class ALIGNMENTS(models.TextChoices):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


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

    page = models.ForeignKey(Page, on_delete=models.CASCADE)
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

    style_padding_top = models.PositiveIntegerField(default=10)
    style_padding_bottom = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ("order", "id")

    @staticmethod
    def get_type_registry():
        from .registries import element_type_registry

        return element_type_registry

    def get_parent(self):
        return self.page

    @classmethod
    def get_last_order(cls, page: Page):
        """
        Returns the last order for the given page.

        :param page: The page we want the order for.
        :return: The last order.
        """

        queryset = Element.objects.filter(page=page)
        return cls.get_highest_order_of_queryset(queryset)[0]

    @classmethod
    def get_unique_order_before_element(cls, before: "Element"):
        """
        Returns a safe order value before the given element in the given page.

        :param page: The page we want the order for.
        :param before: The element before which we want the safe order
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the items must be recalculated in this
            case before calling this method again.
        :return: The order value.
        """

        queryset = Element.objects.filter(page=before.page)
        return cls.get_unique_orders_before_item(before, queryset)[0]


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


class ParagraphElement(Element):
    """
    A simple paragraph.
    """

    value = FormulaField(default="")


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

    class WIDTHS(models.TextChoices):
        AUTO = "auto"
        FULL = "full"

    value = FormulaField(default="")
    navigation_type = models.CharField(
        choices=NAVIGATION_TYPES.choices,
        help_text="The navigation type.",
        max_length=10,
        default=NAVIGATION_TYPES.PAGE,
    )
    navigate_to_page = models.ForeignKey(
        Page,
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
        choices=ALIGNMENTS.choices, max_length=10, default=ALIGNMENTS.LEFT
    )


class ImageElement(Element):
    """
    A simple image element that can display an image either through a remote source
    or via an uploaded file
    """

    class IMAGE_SOURCE_TYPES(models.TextChoices):
        UPLOAD = "upload"
        URL = "url"

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
    image_url = models.URLField(
        help_text="A link to the image file", blank=True, default="", max_length=1000
    )
    alt_text = models.TextField(
        help_text="Text that is displayed when the image can't load",
        default="",
        blank=True,
    )
    alignment = models.CharField(
        choices=ALIGNMENTS.choices, max_length=10, default=ALIGNMENTS.LEFT
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

    default_value = FormulaField(
        default="", help_text="This text input's default value."
    )
    required = models.BooleanField(
        default=False, help_text="Whether this text input is a required field."
    )
    placeholder = models.CharField(
        blank=True,
        default="",
        max_length=225,
        help_text="The placeholder text which should be applied to the element.",
    )
