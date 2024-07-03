from .models import (
    ButtonThemeConfigBlock,
    ColorThemeConfigBlock,
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
        "heading_1_font_size",
        "heading_1_text_color",
        "heading_2_font_size",
        "heading_2_text_color",
        "heading_3_font_size",
        "heading_3_text_color",
    ]
    serializer_field_names = [
        "heading_1_font_size",
        "heading_1_text_color",
        "heading_2_font_size",
        "heading_2_text_color",
        "heading_3_font_size",
        "heading_3_text_color",
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
    allowed_fields = ["button_background_color", "button_hover_background_color"]
    serializer_field_names = [
        "button_background_color",
        "button_hover_background_color",
    ]
