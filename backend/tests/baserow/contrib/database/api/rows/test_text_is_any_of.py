from django.urls import reverse

import pytest


@pytest.mark.django_db
@pytest.mark.parametrize("use_formula_field", [False, True])
@pytest.mark.parametrize(
    "value,expected",
    [
        ("France,Belgique", ["France", "Belgique"]),
        ("France,France", ["France"]),
        ('"Design, Europe",France', ["France", "Design, Europe"]),
        ('" Design "', [" Design "]),
        ("france", []),
        ('"unterminated', []),
        ('"France" ,Belgique', []),
        ("France\n", []),
        ("France\nBelgique", []),
        (",France,,", ["France"]),
        ("", ["France", "Belgique", "Design, Europe", " Design ", ""]),
    ],
)
def test_text_is_any_of_row_filter(
    api_client, data_fixture, use_formula_field, value, expected
):
    user, token = data_fixture.create_user_and_token()
    table, fields, _ = data_fixture.build_table(
        user=user,
        columns=[("Country", "text")],
        rows=[["France"], ["Belgique"], ["Design, Europe"], [" Design "], [""]],
    )
    field = (
        data_fixture.create_formula_field(table=table, formula="field('Country')")
        if use_formula_field
        else fields[0]
    )
    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {f"filter__{field.db_column}__text_is_any_of": value},
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert [row[fields[0].db_column] for row in response.json()["results"]] == expected


@pytest.mark.django_db
@pytest.mark.parametrize("valid", [True, False])
def test_text_is_any_of_parses_long_text_values(api_client, data_fixture, valid):
    user, token = data_fixture.create_user_and_token()
    long_value = "A" * 131073
    table, fields, _ = data_fixture.build_table(
        user=user, columns=[("Text", "long_text")], rows=[[long_value], ["Short"]]
    )
    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {
            f"filter__{fields[0].db_column}__text_is_any_of": f'"{long_value}"'
            if valid
            else f'{long_value}"'
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["count"] == (1 if valid else 0)
    if valid:
        assert response.json()["results"][0][fields[0].db_column] == long_value
