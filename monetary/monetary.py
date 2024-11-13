from math import floor

from currency import Currency


class Monetary:
    __slot__ = ("__amount", "__currency")

    def __init__(self, amount: int, currency: Currency) -> None:
        try:
            self.__validate_amount(amount)
        except Exception as e:
            print(e)
        else:
            self.__amount = amount
        self.__currency = currency

    @staticmethod
    def __validate_amount(amount) -> bool:
        if not isinstance(amount, int):
            raise TypeError("Amount must be an integer")
        if amount < 0:
            raise ValueError("Amount can not be negative")
        return True

    @staticmethod
    def major_to_minor_monetary_unit(major_value: int | float | str, currency: Currency) -> int:
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
