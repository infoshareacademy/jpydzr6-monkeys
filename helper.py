from typing import Any, Callable


class InvalidData(Exception):
    pass


class Helper:
    @staticmethod
    def check_value(data: Any, test_value: Callable) -> Any:
        try:
            validated_data = test_value(data)
            return validated_data
        except ValueError:
            raise InvalidData('Nieprawidłowe dane: ') from None
