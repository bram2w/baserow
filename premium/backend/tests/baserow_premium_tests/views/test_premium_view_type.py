import pytest


@pytest.mark.django_db
@pytest.mark.parametrize("view_type", ["kanban", "calendar", "timeline"])
def test_new_fields_are_hidden_by_default_in_premium_views_if_public(
    view_type, premium_data_fixture
):
    user = premium_data_fixture.create_user()
    table = premium_data_fixture.create_database_table(user=user)
    premium_data_fixture.create_text_field(table=table)

    # NOTE: every time we create a kanban or a calendar, a single select field
    # or a date field is created respectively
    create_view_func = getattr(premium_data_fixture, f"create_{view_type}_view")
    public_view = create_view_func(table=table, public=True, create_options=False)

    options = public_view.get_field_options()
    assert len(options) == 0

    options = public_view.get_field_options(create_if_missing=True)
    for option in options:
        assert option.hidden is True
