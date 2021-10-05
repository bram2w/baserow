from baserow.contrib.database.formula.parser.replace_field_by_id_with_field import (
    replace_field_by_id_with_field,
)


def test_replace_single_field_by_id():
    new_formula = replace_field_by_id_with_field("field_by_id(1)", {1: "newName"})

    assert new_formula == "field('newName')"


def test_replace_field_by_id_keeping_whitespace():
    new_formula = replace_field_by_id_with_field(
        "field_by_id( \n \n1  )", {1: "newName"}
    )

    assert new_formula == "field( \n \n'newName'  )"


def test_can_replace_field_by_id_keeping_whitespace_and_comments():
    new_formula = replace_field_by_id_with_field(
        "/* comment */field_by_id(/* comment */ \n \n1  /* a comment */)",
        {1: "newName"},
    )

    assert (
        new_formula
        == "/* comment */field(/* comment */ \n \n'newName'  /* a comment */)"
    )


def test_replace_field_by_id_with_a_name_containing_double_quotes():
    new_formula = replace_field_by_id_with_field("field_by_id(1)", {1: 'name with "'})

    assert new_formula == "field('name with \"')"


def test_can_replace_multiple_different_ids():
    new_formula = replace_field_by_id_with_field(
        "concat(field_by_id(1), field_by_id(1), field_by_id(2))",
        {1: "newName", 2: "newOther"},
    )

    assert (
        new_formula == "concat(field('newName'), field('newName'), field('newOther'))"
    )


def test_doesnt_change_field_by_id_not_in_dict():
    new_formula = replace_field_by_id_with_field(
        "field_by_id(2)",
        {
            1: "newName",
        },
    )

    assert new_formula == "field_by_id(2)"


def test_returns_same_formula_for_invalid_syntax():
    _assert_returns_same("field_by_id(2")
    _assert_returns_same("field_by_id('test')")
    _assert_returns_same("field_by_id(test)")
    _assert_returns_same("field_by_id((test))")
    _assert_returns_same("field_by_id('''test'')")
    _assert_returns_same(
        "field_by_id(111111111111111111111111111111111111111111111111111111111111111)"
    )


def _assert_returns_same(formula):
    new_formula = replace_field_by_id_with_field(
        formula,
        {2: "newName"},
    )
    assert new_formula == formula
