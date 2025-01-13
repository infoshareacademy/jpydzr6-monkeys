from typing import TypedDict


class Currency(TypedDict):
    """
    A class for currency representation in its smallest value (called minor).

    1 major unit = base^exponent

    It is inspired by Dinero.js (v1/v2).
    :param code: Code of the currency according to ISO 4217
    :param base: The number of unique digits used to represent the currency's minor unit.
    :param exponent: A relationship between currency's major and minor units. It can be thought as number of digits after decimal separator

    """
    code: str
    base: int
    exponent: int
