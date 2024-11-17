import unittest
import os
from datetime import datetime
from budget_manager import BudgetManager


class TestBudgetManager(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_budget.db'
        self.manager = BudgetManager(db_name=self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_budget_entry(self):
        self.manager.add_budget_entry(
            entry_type='income',
            amount=100.50,
            description='Test income',
            category='Test category'
        )
        self.manager.load_budget_from_file()
        self.assertEqual(len(self.manager.budget), 1)
        self.assertEqual(self.manager.budget[0]['type'], 'income')
        self.assertEqual(self.manager.budget[0]['amount'], 100.50)
        self.assertEqual(self.manager.budget[0]['description'], 'Test income')
        self.assertEqual(self.manager.budget[0]['category'], 'Test category')

    def test_delete_budget_entry(self):
        self.manager.add_budget_entry(
            entry_type='income',
            amount=50,
            description='To delete',
            category='Test'
        )
        self.manager.load_budget_from_file()
        self.manager.delete_budget_entry(1)
        self.manager.load_budget_from_file()
        self.assertEqual(len(self.manager.budget), 0)

    def test_show_budget_summary(self):
        self.manager.add_budget_entry(
            entry_type='income',
            amount=200,
            description='Test income',
            category='Category1'
        )
        self.manager.add_budget_entry(
            entry_type='outcome',
            amount=50,
            description='Test outcome',
            category='Category2'
        )
        self.manager.load_budget_from_file()

        income = sum(entry['amount'] for entry in self.manager.budget if entry['type'] == 'income')
        outcome = sum(entry['amount'] for entry in self.manager.budget if entry['type'] == 'outcome')
        balance = income - outcome

        self.assertEqual(income, 200)
        self.assertEqual(outcome, 50)
        self.assertEqual(balance, 150)

    def test_edit_budget_entry(self):
        self.manager.add_budget_entry(
            entry_type='income',
            amount=100,
            description='Initial description',
            category='Initial category'
        )
        self.manager.load_budget_from_file()

        entry_index = 1
        new_type = 'outcome'
        new_amount = 75.50
        new_description = 'Updated description'
        new_category = 'Updated category'

        self.manager.budget[entry_index - 1]['type'] = new_type
        self.manager.budget[entry_index - 1]['amount'] = new_amount
        self.manager.budget[entry_index - 1]['description'] = new_description
        self.manager.budget[entry_index - 1]['category'] = new_category

        self.manager.save_budget_to_file()
        self.manager.load_budget_from_file()

        edited_entry = self.manager.budget[0]
        self.assertEqual(edited_entry['type'], new_type)
        self.assertEqual(edited_entry['amount'], new_amount)
        self.assertEqual(edited_entry['description'], new_description)
        self.assertEqual(edited_entry['category'], new_category)

    def test_show_incomes(self):
        self.manager.add_budget_entry(
            entry_type='income',
            amount=300,
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
            amount=150,
            description='Outcome test',
            category='Outcome category'
        )
        self.manager.load_budget_from_file()
        outcomes = [entry for entry in self.manager.budget if entry['type'] == 'outcome']
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]['amount'], 150)


if __name__ == '__main__':
    unittest.main()