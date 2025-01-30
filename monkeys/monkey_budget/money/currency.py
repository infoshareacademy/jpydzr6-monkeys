from typing import TypedDict
from . import currencies


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


class CurrencyHelper:
    @staticmethod
    def get_currency_by_its_code(code: str = None) -> Currency:
        try:
            currency_dict = getattr(currencies, code)
            return currency_dict
        except AttributeError:
            print(f"No such a currency with code {code}")

    @staticmethod
    def get_currencies_set() -> list[tuple[str, str]]:
        return [(currency["code"], currency["code"]) for currency in currencies.currencies_tuple]

