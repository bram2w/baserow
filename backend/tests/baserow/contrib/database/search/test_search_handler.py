import pytest

from baserow.contrib.database.search.handler import SearchHandler


def test_escape_query():
    # Spacing is standardized.
    assert SearchHandler.escape_query("Full   text   search") == "Full text search"
    # Escape colons for URLs.
    assert SearchHandler.escape_query("https://baserow.io") == "https baserow io"
    # Special characters are trimmed.
    assert SearchHandler.escape_query("Base<&(|)!>row") == "Base row"
    # Leading or trailing spaces trimmed.
    assert SearchHandler.escape_query("  Full text search  ") == "Full text search"


def test_escape_postgres_query_with_per_token_wildcard():
    # Doesn't attempt to match the current search
    assert (
        SearchHandler.escape_postgres_query("french cuisi", True)
        == "$$french$$:* <-> $$cuisi$$:*"
    )


def test_escape_postgres_query_without_per_token_wildcard():
    # Attempts to match the current search as closely as possible
    assert (
        SearchHandler.escape_postgres_query("french cuisi", False)
        == "$$french$$ <-> $$cuisi$$:*"
    )


@pytest.mark.django_db()
def test_create_tsvector_columns(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(
        user,
        force_add_tsvectors=False,
    )
    data_fixture.create_text_field(
        table=table,
        tsvector_column_created=False,
    )

    for field in table.field_set.all():
        assert not field.tsvector_column_created

    table = SearchHandler.sync_tsvector_columns(table)
    for field in table.field_set.all():
        assert field.tsvector_column_created

    model = table.get_model()
    for field in model.get_searchable_fields():
        model._meta.get_field(field.tsv_db_column)


@pytest.mark.django_db
def test_get_fields_missing_search_index(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user)
    model = table.get_model()
    assert list(model.get_fields_missing_search_index()) == []
    text_field = data_fixture.create_text_field(
        table=table, tsvector_column_created=False
    )
    model = table.get_model()
    assert list(model.get_fields_missing_search_index()) == [text_field]
