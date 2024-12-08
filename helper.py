from typing import Any, Callable
import currencies
from money import Currency


class InvalidData(Exception):
    pass


class Helper:
    @staticmethod
    def check_value(data: Any, test_value: Callable, error_message: str) -> Any:
        try:
            validated_data = test_value(data)
            return validated_data
        except ValueError:
            raise InvalidData(error_message) from None

    @staticmethod
    def check_length(data: Any, length: int, error_message: str) -> Any:
        if len(data) == length:
            return data
        raise InvalidData(error_message) from None

    @staticmethod
    def check_currency(currency_id: str, error_message: str) -> Any:
        if currency_id not in currencies.__all__:
            raise InvalidData(error_message) from None
        else:
            return currency_id
