import sys
from datetime import timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils.duration import duration_string

from baserow.contrib.database.fields.models import FormulaField

VALID_FORMULA_TESTS = [
    ("'test'", "test"),
    ("UPPER('test')", "TEST"),
    ("LOWER('TEST')", "test"),
    ("LOWER(UPPER('test'))", "test"),
    ("LOWER(UPPER('test'))", "test"),
    ("CONCAT('test', ' ', 'works')", "test works"),
    ("CONCAT('test', ' ', UPPER('works'))", "test WORKS"),
    (
        "UPPER(" * 100 + "'test'" + ")" * 100,
        "TEST",
    ),
    (
        "UPPER('" + "t" * settings.MAX_FORMULA_STRING_LENGTH + "')",
        "T" * settings.MAX_FORMULA_STRING_LENGTH,
    ),
    ("'https://उदाहरण.परीक्षा'", "https://उदाहरण.परीक्षा"),
    ("UPPER('https://उदाहरण.परीक्षा')", "HTTPS://उदाहरण.परीक्षा"),
    ("CONCAT('https://उदाहरण.परीक्षा', '/api')", "https://उदाहरण.परीक्षा/api"),
    ("LOWER('HTTPS://उदाहरण.परीक्षा')", "https://उदाहरण.परीक्षा"),
    ("CONCAT('\ntest', '\n')", "\ntest\n"),
    ("1+1", "2"),
    ("1/0", "NaN"),
    ("10/3", "3.33333"),
    ("10+10/2", "15.00000"),
    ("(10+2)/3", "4.00000"),
    ("CONCAT(1,2)", "12"),
    ("CONCAT('a',2)", "a2"),
    ("'a' = 'a'", True),
    ("1 = '1'", True),
    ("IF('a' = 'a', 'a', 'b')", "a"),
    ("IF('a' = 'b', 'a', 'b')", "b"),
    ("IF('a' = 'b', 1, 'b')", "b"),
    ("IF('a' = 'a', 1, 'b')", "1"),
    (
        "tonumber('" + "9" * 100 + "')+1",
        "NaN",
    ),
    (
        "9" * 100 + "+1",
        "NaN",
    ),
    ("tonumber('1')", "1.00000"),
    ("tonumber('a')", "NaN"),
    ("tonumber('-12.12345')", "-12.12345"),
    ("1.2 * 2", "2.4"),
    ("isblank(1)", False),
    ("isblank('')", True),
    ("isblank(' ')", False),
    ("t('aaaa')", "aaaa"),
    ("t(10)", ""),
    ("true", True),
    ("false", False),
    ("not(false)", True),
    ("not(true)", False),
    ("true != false", True),
    ("'a' != 'b'", True),
    ("'a' != 'a'", False),
    ("1 != '1'", False),
    ("1 > 1", False),
    ("1 >= 1", True),
    ("1 < 1", False),
    ("1 <= 1", True),
    ("todate('20170103','YYYYMMDD')", "2017-01-03"),
    ("todate('blah', 'YYYY')", None),
    ("day(todate('20170103','YYYYMMDD'))", "3"),
    (
        "datediff("
        "'yy', "
        "todate('20200101', 'YYYYMMDD'), "
        "todate('20100101', 'YYYYMMDD')"
        ")",
        "-10",
    ),
    (
        "datediff("
        "'incorrect thingy', "
        "todate('20200101', 'YYYYMMDD'), "
        "todate('20100101', 'YYYYMMDD')"
        ")",
        "NaN",
    ),
    ("and(true, false)", False),
    ("and(false, false)", False),
    ("and(false, true)", False),
    ("and(true, true)", True),
    ("or(true, false)", True),
    ("or(false, false)", False),
    ("or(false, true)", True),
    ("or(true, true)", True),
    ("'a' + 'b'", "ab"),
    ("date_interval('1 year')", duration_string(timedelta(days=365))),
    ("date_interval('1 year') > date_interval('1 day')", True),
    ("date_interval('1 invalid')", None),
    ("todate('20200101', 'YYYYMMDD') + date_interval('1 year')", "2021-01-01"),
    ("date_interval('1 year') + todate('20200101', 'YYYYMMDD')", "2021-01-01"),
    ("todate('20200101', 'YYYYMMDD') + date_interval('1 second')", "2020-01-01"),
    ("todate('20200101', 'YYYYMMDD') - date_interval('1 year')", "2019-01-01"),
    (
        "todate('20200101', 'YYYYMMDD') - todate('20210101', 'YYYYMMDD')",
        duration_string(-timedelta(days=366)),
    ),
    (
        "date_interval('1 year') - date_interval('1 day')",
        duration_string(timedelta(days=364)),
    ),
    ("replace('test test', 'test', 'a')", "a a"),
    ("search('test test', 'test')", "1"),
    ("search('a', 'test')", "0"),
    ("length('aaa')", "3"),
    ("length('')", "0"),
    ("reverse('abc')", "cba"),
    ("totext(1)", "1"),
    ("totext(true)", "true"),
    ("totext(date_interval('1 year'))", "1 year"),
    ("totext(todate('20200101', 'YYYYMMDD'))", "2020-01-01"),
    ("not(isblank(tonumber('x')))", True),
    ("if(1=1, todate('20200101', 'YYYYMMDD'), 'other')", "2020-01-01"),
    ("not(isblank('')) != false", False),
]


def a_test_case(name, starting_table_setup, formula_info, expectation):
    return name, starting_table_setup, formula_info, expectation


def given_a_table(columns, rows):
    return columns, rows


def when_a_formula_field_is_added(formula):
    return formula


def when_multiple_formula_fields_are_added(formulas):
    return formulas


def then_expect_the_rows_to_be(rows):
    return rows


COMPLEX_VALID_TESTS = [
    a_test_case(
        "Can reference and add to a integer column",
        given_a_table(columns=[("number", "number")], rows=[[1], [2], [None]]),
        when_a_formula_field_is_added("field('number')+1"),
        then_expect_the_rows_to_be([["1", "2"], ["2", "3"], [None, None]]),
    ),
    a_test_case(
        "Can reference and add to a integer column",
        given_a_table(columns=[("number", "number")], rows=[[1], [2], [None]]),
        when_multiple_formula_fields_are_added(
            [("formula_1", "field('number')+1"), "field('formula_1')+1"]
        ),
        then_expect_the_rows_to_be(
            [["1", "2", "3"], ["2", "3", "4"], [None, None, None]]
        ),
    ),
    a_test_case(
        "Can reference and if a text column",
        given_a_table(columns=[("text", "text")], rows=[["a"], ["b"], [None]]),
        when_a_formula_field_is_added("if(field('text')='a', field('text'), 'no')"),
        then_expect_the_rows_to_be([["a", "a"], ["b", "no"], [None, "no"]]),
    ),
    a_test_case(
        "Can reference and if a phone number column",
        given_a_table(
            columns=[("pn", "phone_number")], rows=[["01772"], ["+2002"], [None]]
        ),
        when_a_formula_field_is_added("if(field('pn')='01772', field('pn'), 'no')"),
        then_expect_the_rows_to_be([["01772", "01772"], ["+2002", "no"], [None, "no"]]),
    ),
    a_test_case(
        "Can compare a phone number and number column",
        given_a_table(
            columns=[("pn", "phone_number"), ("num", "number")],
            rows=[["123", "123"], ["+2002", "2002"], [None, None]],
        ),
        when_a_formula_field_is_added("field('pn')=field('num')"),
        then_expect_the_rows_to_be(
            [["123", "123", True], ["+2002", "2002", False], [None, None, None]]
        ),
    ),
    a_test_case(
        "Can compare a date field and text with formatting",
        given_a_table(
            columns=[("date", {"type": "date", "date_format": "US"})],
            rows=[["2020-02-01"], ["2020-03-01"], [None]],
        ),
        when_a_formula_field_is_added("field('date')='02/01/2020'"),
        then_expect_the_rows_to_be(
            [
                ["2020-02-01", True],
                ["2020-03-01", False],
                [None, False],
            ]
        ),
    ),
    a_test_case(
        "Can compare a datetime field and text with eu formatting",
        given_a_table(
            columns=[
                (
                    "date",
                    {"type": "date", "date_format": "EU", "date_include_time": True},
                )
            ],
            rows=[["2020-02-01T00:10:00Z"], ["2020-02-01T02:00:00Z"], [None]],
        ),
        when_a_formula_field_is_added("field('date')='01/02/2020 00:10'"),
        then_expect_the_rows_to_be(
            [
                ["2020-02-01T00:10:00Z", True],
                ["2020-02-01T02:00:00Z", False],
                [None, False],
            ]
        ),
    ),
    a_test_case(
        "Can use a boolean field in an if",
        given_a_table(
            columns=[("boolean", "boolean")],
            rows=[[True], [False]],
        ),
        when_a_formula_field_is_added("if(field('boolean'), 'true', 'false')"),
        then_expect_the_rows_to_be(
            [
                [True, "true"],
                [False, "false"],
            ]
        ),
    ),
]

INVALID_FORMULA_TESTS = [
    (
        "test",
        "ERROR_WITH_FORMULA",
        (
            "Error with formula: Invalid syntax at line 1, col 4: "
            "mismatched input 'the end of the formula' expecting '('."
        ),
    ),
    (
        "UPPER(" * (sys.getrecursionlimit())
        + "'test'"
        + ")" * (sys.getrecursionlimit()),
        "ERROR_WITH_FORMULA",
        "Error with formula: it exceeded the maximum formula size.",
    ),
    (
        "CONCAT(" + ",".join(["'test'"] * 5000) + ")",
        "ERROR_WITH_FORMULA",
        "Error with formula: it exceeded the maximum formula size.",
    ),
    (
        "UPPER('" + "t" * (settings.MAX_FORMULA_STRING_LENGTH + 1) + "')",
        "ERROR_WITH_FORMULA",
        "Error with formula: an embedded "
        f"string in the formula over the maximum length of "
        f"{settings.MAX_FORMULA_STRING_LENGTH} .",
    ),
    (
        "CONCAT()",
        "ERROR_WITH_FORMULA",
        "Error with formula: 0 arguments were given to the function concat, it must "
        "instead be given more than 1 arguments.",
    ),
    (
        "CONCAT('a')",
        "ERROR_WITH_FORMULA",
        "Error with formula: 1 argument was given to the function concat, it must "
        "instead be given more than 1 arguments.",
    ),
    ("UPPER()", "ERROR_WITH_FORMULA", None),
    ("LOWER()", "ERROR_WITH_FORMULA", None),
    (
        "UPPER('a','a')",
        "ERROR_WITH_FORMULA",
        "Error with formula: 2 arguments were given to the function upper, it must "
        "instead be given exactly 1 argument.",
    ),
    ("LOWER('a','a')", "ERROR_WITH_FORMULA", None),
    ("LOWER('a', CONCAT())", "ERROR_WITH_FORMULA", None),
    (
        "'a' + 2",
        "ERROR_WITH_FORMULA",
        "Error with formula: argument number 2 given to operator + was of type number "
        "but the only usable types for this argument are text,char.",
    ),
    (
        "true + true",
        "ERROR_WITH_FORMULA",
        "Error with formula: argument number 2 given to operator + was of type "
        "boolean but there are no possible types usable here.",
    ),
    ("UPPER(1,2)", "ERROR_WITH_FORMULA", None),
    ("UPPER(1)", "ERROR_WITH_FORMULA", None),
    ("LOWER(1,2)", "ERROR_WITH_FORMULA", None),
    ("LOWER(1)", "ERROR_WITH_FORMULA", None),
    ("10/LOWER(1)", "ERROR_WITH_FORMULA", None),
    ("'t'/1", "ERROR_WITH_FORMULA", None),
    ("1/'t'", "ERROR_WITH_FORMULA", None),
    ("field(9999)", "ERROR_WITH_FORMULA", None),
    ("field_by_id(9999)", "ERROR_WITH_FORMULA", None),
    (
        "upper(1)",
        "ERROR_WITH_FORMULA",
        (
            "Error with formula: argument number 1 given to function upper was of type "
            "number but the only usable type for this argument is text."
        ),
    ),
    (
        "concat(upper(1), lower('a'))",
        "ERROR_WITH_FORMULA",
        (
            "Error with formula: argument number 1 given to function upper was of type "
            "number but the only usable type for this argument is text."
        ),
    ),
    (
        "concat(upper(1), lower(2))",
        "ERROR_WITH_FORMULA",
        (
            "Error with formula: argument number 1 given to function upper was of type "
            "number but the only usable type for this argument is text, argument "
            "number 1 given to function lower was of type number but the only usable "
            "type for this argument is text."
        ),
    ),
    ("true > true", "ERROR_WITH_FORMULA", None),
    ("true > 1", "ERROR_WITH_FORMULA", None),
    ("'a' > 1", "ERROR_WITH_FORMULA", None),
    ("true < true", "ERROR_WITH_FORMULA", None),
    ("true < 1", "ERROR_WITH_FORMULA", None),
    ("'a' < 1", "ERROR_WITH_FORMULA", None),
    (
        "todate('20200101', 'YYYYMMDD') + todate('20210101', 'YYYYMMDD')",
        "ERROR_WITH_FORMULA",
        "Error with formula: argument number 2 given to operator + was of type date "
        "but the only usable type for this argument is date_interval.",
    ),
    (
        "date_interval('1 second') - todate('20210101', 'YYYYMMDD')",
        "ERROR_WITH_FORMULA",
        "Error with formula: argument number 2 given to operator - was of type date "
        "but the only usable type for this argument is date_interval.",
    ),
]


@pytest.mark.parametrize("test_input,expected", VALID_FORMULA_TESTS)
@pytest.mark.django_db
def test_valid_formulas(test_input, expected, data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Formula2", "type": "formula", "formula": test_input},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200, response.json()
    field_id = response.json()["id"]
    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200
    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0][f"field_{field_id}"] == expected


@pytest.mark.parametrize("name,table_setup,formula,expected", COMPLEX_VALID_TESTS)
@pytest.mark.django_db
def test_valid_complex_formulas(
    name,
    table_setup,
    formula,
    expected,
    data_fixture,
    api_client,
    django_assert_num_queries,
):
    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        columns=table_setup[0], rows=table_setup[1], user=user
    )
    if not isinstance(formula, list):
        formula = [formula]
    formula_field_ids = []
    j = 0
    for f in formula:
        if not isinstance(f, tuple):
            f = f"baserow_formula_{j}", f
            j += 1
        response = api_client.post(
            reverse("api:database:fields:list", kwargs={"table_id": table.id}),
            {"name": f[0], "type": "formula", "formula": f[1]},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == 200, response.json()
        formula_field_ids.append(response.json()["id"])
    response = api_client.post(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200
    response = api_client.get(
        reverse("api:database:rows:list", kwargs={"table_id": table.id}),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response_json["count"] == len(table_setup[1]) + 1
    i = 0
    for row in expected:
        k = 0
        for field in fields:
            assert response_json["results"][i][f"field_{field.id}"] == row[k]
            k += 1
        for f_id in formula_field_ids:
            assert response_json["results"][i][f"field_{f_id}"] == row[k], response_json
            k += 1
        i += 1


@pytest.mark.parametrize("test_input,error,detail", INVALID_FORMULA_TESTS)
@pytest.mark.django_db
def test_invalid_formulas(test_input, error, detail, data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    response = api_client.post(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        {"name": "Formula2", "type": "formula", "formula": test_input},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 400
    response_json = response.json()
    assert response_json["error"] == error
    if detail:
        assert response_json["detail"] == detail

    response = api_client.get(
        reverse("api:database:fields:list", kwargs={"table_id": table.id}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 200
    assert response.json() == []
    assert FormulaField.objects.count() == 0
