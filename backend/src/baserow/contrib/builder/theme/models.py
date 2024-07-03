from django.db import models

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
    heading_1_font_size = models.SmallIntegerField(default=24)
    heading_1_text_color = models.CharField(max_length=9, default="#070810ff")
    heading_2_font_size = models.SmallIntegerField(default=20)
    heading_2_text_color = models.CharField(max_length=9, default="#070810ff")
    heading_3_font_size = models.SmallIntegerField(default=16)
    heading_3_text_color = models.CharField(max_length=9, default="#070810ff")


class ButtonThemeConfigBlock(ThemeConfigBlock):
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
