from django.core.management import call_command

import pytest

from baserow.contrib.database.fields.models import FormulaField
from baserow.contrib.database.formula.types.exceptions import InvalidFormulaType


@pytest.mark.django_db
def test_reset_formula_changes_formula_value(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    formula_field = data_fixture.create_formula_field(
        user=user, table=table, formula="1"
    )
    before_internal = formula_field.internal_formula

    call_command("reset_formula", formula_field.id, "'a'")

    formula_field.refresh_from_db()
    assert formula_field.formula == "'a'"
    # Assert we have recalculated properly
    assert formula_field.internal_formula != before_internal


@pytest.mark.django_db
def test_reset_formula_raises_for_missing_formula(data_fixture):
    with pytest.raises(FormulaField.DoesNotExist):
        call_command("reset_formula", 9999, "1")


@pytest.mark.django_db
def test_reset_formula_raises_for_invalid(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    formula_field = data_fixture.create_formula_field(
        user=user, table=table, formula="1"
    )

    with pytest.raises(InvalidFormulaType):
        call_command("reset_formula", formula_field.id, "'a' + 1")

    formula_field.refresh_from_db()
    assert formula_field.formula == "1"
