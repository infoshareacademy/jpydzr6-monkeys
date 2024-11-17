from __future__ import annotations
from math import floor

from currency import Currency
from currencies import PLN


class Monetary:
    """
    Base class for holding money values.
    It is inspired by Dinero.js (v1/v2).
    """
    __slot__ = ("__amount", "__currency")

    def __init__(self, amount: int, currency: Currency) -> None:
        """
        While instantiating a Monetary object the value should be given in the smallest available unit available in
        chosen currency. There is given a static method to convert non-minor value to the minor.
        :param amount: Amount of the money in the smallest unit of the currency.
        :param currency: Currency dictionary from 'currencies' directory
        """
        try:
            self.__validate_amount(amount)
        except Exception as e:
            print(e)
        else:
            self.__amount = amount
        self.__currency = currency

    def __add__(self, ingredient: Monetary) -> Monetary:
        if self.__validate_ingredient(ingredient):
            result = self.amount + ingredient.amount
            return Monetary(result, self.__currency)

    def __sub__(self, ingredient: Monetary) -> Monetary:
        if self.__validate_ingredient(ingredient):
            result = self.amount - ingredient.amount
            return Monetary(result, self.__currency)

    def __mul__(self, ingredient: int | float) -> Monetary:
        if not isinstance(ingredient, (int, float)):
            raise TypeError("It is not possible to multiply an amount of money by another one")
        else:
            result = int(round(self.amount * ingredient, 0))
            return Monetary(result, self.__currency)

    def __truediv__(self, ingredient: int | float) -> Monetary:
        if not isinstance(ingredient, (int, float)):
            raise TypeError("It is not possible to divide an amount of money by another one")
        else:
            result = int(round(self.amount / ingredient, 0))
            return Monetary(result, self.__currency)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.amount}, {self.currency})"

    def __str__(self):
        factor = pow(self.__currency.get("base"), self.__currency.get("exponent"))
        major = self.amount / factor
        exponent = self.__currency.get("exponent")
        return f"{self.currency} {major:.{exponent}f}"

    @property
    def amount(self) -> int:
        return self.__amount

    @property
    def currency(self) -> str:
        return self.__currency.get("code")


    @staticmethod
    def __validate_amount(amount) -> bool:
        """Validate whether the amount (type int) is nonzero"""
        if not isinstance(amount, int):
            raise TypeError("Amount must be an integer")
        if amount < 0:
            raise ValueError("Amount can not be negative")
        return True

    @staticmethod
    def major_to_minor_monetary_unit(major_value: int | float | str, currency: Currency) -> int:
        """
        Converts an amount of money in major unit to appropriate minor unit
        :param major_value: Amount of money in major unit
        :param currency: Currency on which basis the amount will be converted
        :return:
        """
        factor = pow(currency.get("base"), currency.get("exponent"))
        match major_value:
            case int():
                if major_value < 0:
                    raise ValueError("Amount can not be negative")
                else:
                    return major_value * factor
            case float():
                if major_value < 0.0:
                    raise ValueError("Amount can not be negative")
                else:
                    return floor(major_value * factor)
            case str():
                major_value.strip().replace(",", ".")
                try:
                    converted = float(major_value)
                except:
                    raise ValueError("Given string cannot be converted into float")
                else:
                    if converted < 0.0:
                        raise ValueError("Amount can not be negative")
                    else:
                        return floor(converted * factor)
            case _:
                raise TypeError("Wrong type of given value")

    def __validate_ingredient(self, ingredient: Monetary) -> bool:
        """For checking whether in mathematical operations are used instancies with the same currency"""
        if not isinstance(ingredient, Monetary):
            raise TypeError(f"The type is not a {self.__class__} instance")
        elif self.currency != ingredient.currency:
            raise AttributeError("The currencies does not match")
        else:
            return True


if __name__ == '__main__':
    print(Monetary.major_to_minor_monetary_unit(1, PLN))
    print(Monetary.major_to_minor_monetary_unit(1.11, PLN))
    print(Monetary.major_to_minor_monetary_unit("1.2", PLN))
    print(Monetary.major_to_minor_monetary_unit("1.34", PLN))
    print(Monetary.major_to_minor_monetary_unit("1.567", PLN))
