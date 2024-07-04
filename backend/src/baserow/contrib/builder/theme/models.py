from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from baserow.contrib.builder.constants import WIDTHS, HorizontalAlignments
from baserow.core.fields import AutoOneToOneField


class ThemeConfigBlock(models.Model):
    builder = AutoOneToOneField(
        "builder.Builder",
        on_delete=models.CASCADE,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True


class MainThemeConfigBlock(ThemeConfigBlock):
    # TODO zdm remove the whole model in next release
    primary_color = models.CharField(max_length=9, default="#5190efff")
    secondary_color = models.CharField(max_length=9, default="#0eaa42ff")
    border_color = models.CharField(max_length=9, default="#d7d8d9ff")
    heading_1_font_size = models.SmallIntegerField(default=24)
    heading_1_color = models.CharField(max_length=9, default="#070810ff")
    heading_2_font_size = models.SmallIntegerField(default=20)
    heading_2_color = models.CharField(max_length=9, default="#070810ff")
    heading_3_font_size = models.SmallIntegerField(default=16)
    heading_3_color = models.CharField(max_length=9, default="#070810ff")


class ColorThemeConfigBlock(ThemeConfigBlock):
    primary_color = models.CharField(max_length=9, default="#5190efff")
    secondary_color = models.CharField(max_length=9, default="#0eaa42ff")
    border_color = models.CharField(max_length=9, default="#d7d8d9ff")


class TypographyThemeConfigBlock(ThemeConfigBlock):
    body_font_size = models.SmallIntegerField(default=14)
    body_text_color = models.CharField(max_length=9, default="#070810ff")
    body_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    heading_1_font_size = models.SmallIntegerField(default=24)
    heading_1_text_color = models.CharField(max_length=9, default="#070810ff")
    heading_1_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    heading_2_font_size = models.SmallIntegerField(default=20)
    heading_2_text_color = models.CharField(max_length=9, default="#070810ff")
    heading_2_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    heading_3_font_size = models.SmallIntegerField(default=16)
    heading_3_text_color = models.CharField(max_length=9, default="#070810ff")
    heading_3_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    heading_4_font_size = models.SmallIntegerField(default=16)
    heading_4_text_color = models.CharField(max_length=9, default="#070810ff")
    heading_4_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    heading_5_font_size = models.SmallIntegerField(default=14)
    heading_5_text_color = models.CharField(max_length=9, default="#070810ff")
    heading_5_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    heading_6_font_size = models.SmallIntegerField(default=14)
    heading_6_text_color = models.CharField(max_length=9, default="#202128")
    heading_6_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )


class ButtonThemeConfigBlock(ThemeConfigBlock):
    button_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    button_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.CENTER,
    )
    button_width = models.CharField(
        choices=WIDTHS.choices,
        max_length=10,
        default=WIDTHS.AUTO,
    )
    button_background_color = models.CharField(
        max_length=20,
        default="primary",
        blank=True,
        help_text="The background color of buttons",
    )
    button_hover_background_color = models.CharField(
        max_length=20,
        default="#96baf6ff",
        blank=True,
        help_text="The background color of buttons when hovered",
    )


class LinkThemeConfigBlock(ThemeConfigBlock):
    link_text_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )
    link_text_color = models.CharField(
        max_length=20,
        default="primary",
        blank=True,
        help_text="The text color of links",
    )
    link_hover_text_color = models.CharField(
        max_length=20,
        default="#96baf6ff",
        blank=True,
        help_text="The hover color of links when hovered",
    )


class ImageThemeConfigBlock(ThemeConfigBlock):
    class IMAGE_CONSTRAINT_TYPES(models.TextChoices):
        COVER = "cover"
        CONTAIN = "contain"
        FULL_WIDTH = "full-width"

    image_alignment = models.CharField(
        choices=HorizontalAlignments.choices,
        max_length=10,
        default=HorizontalAlignments.LEFT,
    )

    image_max_width = models.PositiveIntegerField(
        help_text="The max-width for this image element.",
        default=100,
        validators=[
            MinValueValidator(0, message="Value cannot be less than 0."),
            MaxValueValidator(100, message="Value cannot be greater than 100."),
        ],
    )

    image_max_height = models.PositiveIntegerField(
        null=True,
        help_text="The max-height for this image element.",
        validators=[
            MinValueValidator(5, message="Value cannot be less than 5."),
            MaxValueValidator(3000, message="Value cannot be greater than 3000."),
        ],
    )

    image_constraint = models.CharField(
        help_text="The image constraint to apply to this image",
        choices=IMAGE_CONSTRAINT_TYPES.choices,
        max_length=32,
        default=IMAGE_CONSTRAINT_TYPES.CONTAIN,
    )
