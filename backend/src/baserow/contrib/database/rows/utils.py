from decimal import Decimal
from fractions import Fraction
from typing import Tuple, Union

from .exceptions import CannotCalculateIntermediateOrder


def find_intermediate_fraction(p1: int, q1: int, p2: int, q2: int) -> Tuple[int, int]:
    """
    Find an intermediate fraction between p1/q1 and p2/q2.

    The fraction chosen is the highest fraction in the Stern-Brocot tree which falls
    strictly between the specified values. This is intended to avoid going deeper in
    the tree unnecessarily when the list is already sparse due to deletion or moving
    of items, but in fact the case when the two items are already adjacent in the tree
    is common so we shortcut it. As a bonus, this method always generates fractions
    in lowest terms, so there is no need for GCD calculations  anywhere.

    Based on `find_intermediate` in
    https://wiki.postgresql.org/wiki/User-specified_ordering_with_fractions
    """

    pl = 0
    ql = 1
    ph = 1
    qh = 0

    if p1 * q2 + 1 != p2 * q1:
        while True:
            p = pl + ph
            q = ql + qh
            if p * q1 <= q * p1:
                pl = p
                ql = q
            elif p2 * q <= q2 * p:
                ph = p
                qh = q
            else:
                return p, q
    else:
        p = p1 + p2
        q = q1 + q2

    return p, q


def find_intermediate_order(
    order_1: Union[float, Decimal],
    order_2: Union[float, Decimal],
    max_denominator: int = 10000000,
) -> float:
    """
    Calculates what the intermediate order of the two provided orders should be.
    This can be used when a row must be moved before or after another row. It just
    needs to order of the before and after row and it will return the best new order.

    - order_1
    - return_value
    - order_2

    :param order_1: The order of the before adjacent row. The new returned order will
        be after this one
    :param order_2: The order of the after adjacent row. The new returned order will
        be before this one.
    :param max_denominator: The max denominator of the fraction calculator from the
        order.
    :raises ValueError: If the fractions of the orders are equal.
    :return: The new order that can safely be used and will be a unique value.
    """

    p1, q1 = Fraction(order_1).limit_denominator(max_denominator).as_integer_ratio()
    p2, q2 = Fraction(order_2).limit_denominator(max_denominator).as_integer_ratio()

    if p1 == p2 and q1 == q2:
        raise CannotCalculateIntermediateOrder("The fractions of the orders are equal.")

    intermediate_fraction = float(Fraction(*find_intermediate_fraction(p1, q1, p2, q2)))

    if intermediate_fraction == float(order_1) or intermediate_fraction == float(
        order_2
    ):
        raise CannotCalculateIntermediateOrder(
            "Could not find an intermediate fraction because it's equal "
            "to the provided order."
        )

    return float(Fraction(*find_intermediate_fraction(p1, q1, p2, q2)))
