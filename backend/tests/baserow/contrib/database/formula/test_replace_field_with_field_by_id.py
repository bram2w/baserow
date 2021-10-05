from baserow.contrib.database.formula.parser.replace_field_with_field_by_id import (
    replace_field_with_field_by_id,
)


def test_replace_single_quoted_field_ref_with_id():
    new_formula = replace_field_with_field_by_id("field('test')", {"test": 1})

    assert new_formula == "field_by_id(1)"


def test_replace_double_quoted_field_ref_with_id():
    new_formula = replace_field_with_field_by_id('field("test")', {"test": 1})

    assert new_formula == "field_by_id(1)"


def test_replace_field_reference_keeping_whitespace():
    new_formula = replace_field_with_field_by_id("field( \n \n'test'  )", {"test": 1})

    assert new_formula == "field_by_id( \n \n1  )"


def test_replace_double_quote_field_ref_containing_single_quotes():
    new_formula = replace_field_with_field_by_id(
        'field("test with \'")', {"test with '": 1}
    )

    assert new_formula == "field_by_id(1)"


def test_replace_double_quote_field_ref_containing_double_quotes():
    new_formula = replace_field_with_field_by_id(
        'field("test with \\"")', {'test with "': 1}
    )

    assert new_formula == "field_by_id(1)"


def test_replace_single_quote_field_ref_containing_single_quotes():
    new_formula = replace_field_with_field_by_id(
        "field('test with \\'')", {"test with '": 1}
    )

    assert new_formula == "field_by_id(1)"


def test_replace_single_quote_field_ref_containing_double_quotes():
    new_formula = replace_field_with_field_by_id(
        "field('test with \"')", {'test with "': 1}
    )

    assert new_formula == "field_by_id(1)"


def test_can_replace_field_ref_keeping_whitespace_and_comments():
    new_formula = replace_field_with_field_by_id(
        "/* comment */field(/* comment */ \n \n'test'  /* a comment */)",
        {"test": 1},
    )

    assert (
        new_formula == "/* comment */field_by_id(/* comment */ \n \n1  /* a comment */)"
    )


def test_can_replace_multiple_different_field_references():
    new_formula = replace_field_with_field_by_id(
        'concat(field("test"), field("test"), field(\'other\'))',
        {"test": 1, "other": 2},
    )

    assert new_formula == "concat(field_by_id(1), field_by_id(1), field_by_id(2))"


def test_leaves_unknown_field_references_along():
    new_formula = replace_field_with_field_by_id(
        "field('test')",
        {"notTest": 1},
    )
    assert new_formula == "field('test')"


def test_returns_same_formula_with_field_names_for_invalid_syntax():
    _assert_returns_same("field('test'")
    _assert_returns_same("field(''''test'")
    _assert_returns_same("field(test")
    _assert_returns_same("field(1)")
    _assert_returns_same("field)")
    _assert_returns_same("field_by_id(1)")


def _assert_returns_same(formula):
    new_formula = replace_field_with_field_by_id(
        formula,
        {
            "test": 1,
        },
    )
    assert new_formula == formula
