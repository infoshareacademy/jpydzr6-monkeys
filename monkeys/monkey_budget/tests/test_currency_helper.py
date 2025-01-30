import pytest

from ..money import Currency, CurrencyHelper, currencies


@pytest.fixture()
def currency_pln():
    return currencies.PLN


@pytest.fixture()
def all_currencies():
    return CurrencyHelper.get_currencies_set()


def test_currency_pln(currency_pln):
    assert currency_pln["code"] == "PLN"
    assert currency_pln["base"] == 10
    assert currency_pln["exponent"] == 2


def test_get_currency_by_code(currency_pln):
    some_currency = CurrencyHelper.get_currency_by_its_code("PLN")
    assert some_currency == currency_pln


def test_get_all_currencies(all_currencies):
    assert len(all_currencies) == len(currencies.__all__)
