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
            raise TypeError("Amount must be an integer"),
        if amount < 0:
            raise ValueError("Amount can not be negative")
        return True