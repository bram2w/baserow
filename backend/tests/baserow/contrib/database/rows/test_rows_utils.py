from decimal import Decimal

import pytest

from baserow.contrib.database.rows.exceptions import CannotCalculateIntermediateOrder
from baserow.contrib.database.rows.utils import find_intermediate_order


def test_find_intermediate_order_with_decimals():
    assert find_intermediate_order(
        Decimal("1.00000000000000000000"), Decimal("2.00000000000000000000")
    ) == Decimal("1.50000000000000000000")


def test_find_intermediate_order_with_floats():
    assert find_intermediate_order(
        1.00000000000000000000, 2.00000000000000000000
    ) == Decimal("1.50000000000000000000")


def test_find_intermediate_order_with_lower_than_one_values():
    assert find_intermediate_order(
        Decimal("0.00000000000000000000"), Decimal("1.00000000000000000000")
    ) == Decimal("0.50000000000000000000")


def test_find_intermediate_order_with_10k_iterations():
    start = Decimal("1.00000000000000000000")
    end = Decimal("2.00000000000000000000")

    for i in range(0, 10000):
        end = find_intermediate_order(start, end)

    assert end == 1.000099990001


def test_find_intermediate_order_with_more_iterations_than_max_denominator():
    start = Decimal("1.00000000000000000000")
    end = Decimal("2.00000000000000000000")

    for i in range(0, 100):
        end = find_intermediate_order(start, end, 100)

    with pytest.raises(CannotCalculateIntermediateOrder):
        find_intermediate_order(start, end, 100)


def test_find_intermediate_with_equal_order():
    with pytest.raises(CannotCalculateIntermediateOrder):
        find_intermediate_order(
            Decimal("1.00000000000000000001"), Decimal("1.00000000000000100000")
        )

    find_intermediate_order(
        Decimal("1.0100000000000000000"), Decimal("1.02000000000000000000"), 100
    )

    with pytest.raises(CannotCalculateIntermediateOrder):
        find_intermediate_order(
            Decimal("1.0100000000000000000"), Decimal("1.02000000000000000000"), 10
        )
