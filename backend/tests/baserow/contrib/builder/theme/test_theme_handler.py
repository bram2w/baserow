import pytest

from baserow.contrib.builder.theme.handler import ThemeHandler


@pytest.mark.django_db
def test_update_theme(data_fixture):
    builder = data_fixture.create_builder_application()

    ThemeHandler().update_theme(
        builder,
        primary_color="#f00000ff",
        heading_1_font_size=30,
        heading_1_color="#ff0000ff",
    )

    builder.mainthemeconfigblock.refresh_from_db()

    assert builder.mainthemeconfigblock.primary_color == "#f00000ff"
    assert builder.mainthemeconfigblock.secondary_color == "#000000ff"
    assert builder.mainthemeconfigblock.heading_1_font_size == 30
    assert builder.mainthemeconfigblock.heading_1_color == "#ff0000ff"
    assert builder.mainthemeconfigblock.heading_2_font_size == 20
    assert builder.mainthemeconfigblock.heading_2_color == "#000000ff"
    assert builder.mainthemeconfigblock.heading_3_font_size == 16
    assert builder.mainthemeconfigblock.heading_3_color == "#000000ff"
