class InvalidData(Exception):
    pass


class Helper:
    @staticmethod
    def check_type(number, test_type):
        try:
            test = test_type(number)
            return test
        except ValueError:
            raise InvalidData('Nieprawidłowe dane: ') from None


if __name__ == '__main__':
    test = Helper()
    print(test.check_type(3.8, float))
