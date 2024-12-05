import unittest
import os
from datetime import datetime
from budget_manager import BudgetManager
from money import Monetary, Currency
from currencies import PLN

currency_for_test = PLN
class TestBudgetManager(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_budget.db'
        self.manager = BudgetManager(currency_for_test, db_name=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_budget_entry(self):
        money = Monetary.major_to_minor_unit(100.50, currency_for_test)
        self.manager.add_budget_entry(
            entry_type='income',
            entry = Monetary(money, currency_for_test),
            description='Test income',
            category='Test category'
        )
        self.manager.load_budget_from_file()
        self.assertEqual(len(self.manager.budget), 1)
        self.assertEqual(self.manager.budget[0]['type'], 'income')
        self.assertEqual(self.manager.budget[0]['amount'], 10050)
        self.assertEqual(self.manager.budget[0]['description'], 'Test income')
        self.assertEqual(self.manager.budget[0]['category'], 'Test category')

    def test_delete_budget_entry(self):
        money = Monetary.major_to_minor_unit(50, currency_for_test)
        self.manager.add_budget_entry(
            entry_type='income',
            entry = Monetary(money, currency_for_test),
            description='To delete',
            category='Test'
        )
        self.manager.load_budget_from_file()
        self.manager.delete_budget_entry(1)
        self.manager.load_budget_from_file()
        self.assertEqual(len(self.manager.budget), 0)

    def test_show_budget_summary(self):
        money = Monetary.major_to_minor_unit(200, currency_for_test)
        self.manager.add_budget_entry(
            entry_type='income',
            entry = Monetary(money, currency_for_test),
            description='Test income',
            category='Category1'
        )
        money = Monetary.major_to_minor_unit(50, currency_for_test)
        self.manager.add_budget_entry(
            entry_type='outcome',
            entry = Monetary(money, currency_for_test),
            description='Test outcome',
            category='Category2'
        )
        self.manager.load_budget_from_file()

        income = sum(entry['amount'] for entry in self.manager.budget if entry['type'] == 'income')
        outcome = sum(entry['amount'] for entry in self.manager.budget if entry['type'] == 'outcome')
        income = Monetary(income, currency_for_test)
        outcome = Monetary(outcome, currency_for_test)
        balance = income - outcome

        self.assertEqual(income.amount, 20000)
        self.assertEqual(outcome.amount, 5000)
        self.assertEqual(balance.amount, 15000)

    def test_edit_budget_entry(self):
        money = Monetary.major_to_minor_unit(100, currency_for_test)
        self.manager.add_budget_entry(
            entry_type='income',
            entry = Monetary(money, currency_for_test),
            description='Initial description',
            category='Initial category'
        )
        self.manager.load_budget_from_file()

        entry_index = 1
        new_type = 'outcome'
        new_amount = 75.50
        new_amount = Monetary.major_to_minor_unit(new_amount, currency_for_test)
        new_amount = Monetary(new_amount, currency_for_test)
        new_description = 'Updated description'
        new_category = 'Updated category'

        self.manager.budget[entry_index - 1]['type'] = new_type
        self.manager.budget[entry_index - 1]['amount'] = new_amount.amount
        self.manager.budget[entry_index - 1]['description'] = new_description
        self.manager.budget[entry_index - 1]['category'] = new_category

        self.manager.save_budget_to_file()
        self.manager.load_budget_from_file()

        edited_entry = self.manager.budget[0]
        self.assertEqual(edited_entry['type'], new_type)
        self.assertEqual(edited_entry['amount'], new_amount.amount)
        self.assertEqual(edited_entry['description'], new_description)
        self.assertEqual(edited_entry['category'], new_category)

    def test_show_incomes(self):
        self.manager.add_budget_entry(
            entry_type='income',
            entry=Monetary(300, currency_for_test),
            description='Income test',
            category='Income category'
        )
        self.manager.load_budget_from_file()
        incomes = [entry for entry in self.manager.budget if entry['type'] == 'income']
        self.assertEqual(len(incomes), 1)
        self.assertEqual(incomes[0]['amount'], 300)

    def test_show_outcomes(self):
        self.manager.add_budget_entry(
            entry_type='outcome',
            entry=Monetary(150, currency_for_test),
            description='Outcome test',
            category='Outcome category'
        )
        self.manager.load_budget_from_file()
        outcomes = [entry for entry in self.manager.budget if entry['type'] == 'outcome']
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]['amount'], 150)


if __name__ == '__main__':
    unittest.main()
