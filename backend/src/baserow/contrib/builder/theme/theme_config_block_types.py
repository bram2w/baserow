from .models import MainThemeConfigBlock
from .registries import ThemeConfigBlockType

main_theme_config_block_fields = [
    "primary_color",
    "secondary_color",
    "heading_1_font_size",
    "heading_1_color",
    "heading_2_font_size",
    "heading_2_color",
    "heading_3_font_size",
    "heading_3_color",
]


class MainThemeConfigBlockType(ThemeConfigBlockType):
    type = "main"
    model_class = MainThemeConfigBlock
    allowed_fields = main_theme_config_block_fields
    serializer_field_names = main_theme_config_block_fields
