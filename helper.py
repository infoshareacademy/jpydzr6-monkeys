class Helper:
    @staticmethod
    def check_type(number, test_type):
        try:
            test = test_type(number)
            return test
        except ValueError:
            return False


if __name__ == '__main__':
    test = Helper()
    print(test.check_type(3.8, float))
