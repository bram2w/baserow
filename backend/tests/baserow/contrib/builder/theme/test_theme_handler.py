import pytest

from baserow.contrib.builder.theme.handler import ThemeHandler
from baserow.contrib.builder.theme.registries import theme_config_block_registry


@pytest.mark.django_db
def test_update_theme(data_fixture):
    builder = data_fixture.create_builder_application()

    ThemeHandler().update_theme(
        builder,
        primary_color="#f00000ff",
        heading_1_font_size=30,
        heading_1_text_color="#ff0000ff",
        button_background_color="#ccddcc",
    )

    for theme_config_block_type in theme_config_block_registry.get_all():
        related_name = theme_config_block_type.related_name_in_builder_model
        getattr(builder, related_name).refresh_from_db()

    assert builder.colorthemeconfigblock.primary_color == "#f00000ff"
    assert builder.colorthemeconfigblock.secondary_color == "#0eaa42ff"
    assert builder.typographythemeconfigblock.heading_1_font_size == 30
    assert builder.typographythemeconfigblock.heading_1_text_color == "#ff0000ff"
    assert builder.typographythemeconfigblock.heading_2_font_size == 20
    assert builder.typographythemeconfigblock.heading_2_text_color == "#070810ff"
    assert builder.typographythemeconfigblock.heading_3_font_size == 16
    assert builder.typographythemeconfigblock.heading_3_text_color == "#070810ff"
    assert builder.buttonthemeconfigblock.button_background_color == "#ccddcc"
