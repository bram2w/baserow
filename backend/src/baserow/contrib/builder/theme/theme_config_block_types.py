from .models import (
    ButtonThemeConfigBlock,
    ColorThemeConfigBlock,
    ImageThemeConfigBlock,
    LinkThemeConfigBlock,
    TypographyThemeConfigBlock,
)
from .registries import ThemeConfigBlockType


class ColorThemeConfigBlockType(ThemeConfigBlockType):
    type = "color"
    model_class = ColorThemeConfigBlock
    allowed_fields = [
        "primary_color",
        "secondary_color",
        "border_color",
    ]
    serializer_field_names = [
        "primary_color",
        "secondary_color",
        "border_color",
    ]


class TypographyThemeConfigBlockType(ThemeConfigBlockType):
    type = "typography"
    model_class = TypographyThemeConfigBlock
    allowed_fields = [
        "body_font_size",
        "body_text_color",
        "body_text_alignment",
        "heading_1_font_size",
        "heading_1_text_color",
        "heading_1_text_alignment",
        "heading_2_font_size",
        "heading_2_text_color",
        "heading_2_text_alignment",
        "heading_3_font_size",
        "heading_3_text_color",
        "heading_3_text_alignment",
        "heading_4_font_size",
        "heading_4_text_color",
        "heading_4_text_alignment",
        "heading_5_font_size",
        "heading_5_text_color",
        "heading_5_text_alignment",
        "heading_6_font_size",
        "heading_6_text_color",
        "heading_6_text_alignment",
    ]
    serializer_field_names = [
        "body_font_size",
        "body_text_color",
        "body_text_alignment",
        "heading_1_font_size",
        "heading_1_text_color",
        "heading_1_text_alignment",
        "heading_2_font_size",
        "heading_2_text_color",
        "heading_2_text_alignment",
        "heading_3_font_size",
        "heading_3_text_color",
        "heading_3_text_alignment",
        "heading_4_font_size",
        "heading_4_text_color",
        "heading_4_text_alignment",
        "heading_5_font_size",
        "heading_5_text_color",
        "heading_5_text_alignment",
        "heading_6_font_size",
        "heading_6_text_color",
        "heading_6_text_alignment",
    ]

    def import_serialized(self, parent, serialized_values, id_mapping):
        # Translate from old color property names to new names for compat with templates
        for level in range(3):
            if f"heading_{level+1}_color" in serialized_values:
                serialized_values[
                    f"heading_{level+1}_text_color"
                ] = serialized_values.pop(f"heading_{level+1}_color")

        return super().import_serialized(parent, serialized_values, id_mapping)


class ButtonThemeConfigBlockType(ThemeConfigBlockType):
    type = "button"
    model_class = ButtonThemeConfigBlock
    allowed_fields = [
        "button_background_color",
        "button_hover_background_color",
        "button_text_alignment",
        "button_alignment",
        "button_width",
    ]
    serializer_field_names = [
        "button_background_color",
        "button_hover_background_color",
        "button_text_alignment",
        "button_alignment",
        "button_width",
    ]


class LinkThemeConfigBlockType(ThemeConfigBlockType):
    type = "link"
    model_class = LinkThemeConfigBlock
    allowed_fields = [
        "link_text_alignment",
        "link_text_color",
        "link_hover_text_color",
    ]
    serializer_field_names = [
        "link_text_alignment",
        "link_text_color",
        "link_hover_text_color",
    ]


class ImageThemeConfigBlockType(ThemeConfigBlockType):
    type = "image"
    model_class = ImageThemeConfigBlock
    allowed_fields = [
        "image_alignment",
        "image_max_width",
        "image_max_height",
        "image_constraint",
    ]
    serializer_field_names = [
        "image_alignment",
        "image_max_width",
        "image_max_height",
        "image_constraint",
    ]
