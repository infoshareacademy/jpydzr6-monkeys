import unittest
import os
from datetime import datetime
from income_outcome import Transactions

class TestTransactions(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_budget.db'
        self.test_table = 'test_operations'
        self.manager = Transactions(db_name=self.test_db, table_name=self.test_table)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_budget_entry(self):
        self.manager.add_budget_entry(
            account_id=1,
            entry_type='income',
            amount=100.50,
            description='Test income',
            category='Test category'
        )
        self.assertEqual(len(self.manager.transactions), 1)
        self.assertEqual(self.manager.transactions[0]['type'], 'income')
        self.assertEqual(self.manager.transactions[0]['amount'], 100.50)
        self.assertEqual(self.manager.transactions[0]['description'], 'Test income')
        self.assertEqual(self.manager.transactions[0]['category'], 'Test category')

    def test_delete_budget_entry(self):
        self.manager.add_budget_entry(
            account_id=1,
            entry_type='income',
            amount=50,
            description='To delete',
            category='Test'
        )
        self.manager.delete_budget_entry(1)
        self.assertEqual(len(self.manager.transactions), 0)

    def test_show_budget_summary(self):
        self.manager.add_budget_entry(
            account_id=1,
            entry_type='income',
            amount=200,
            description='Test income',
            category='Category1'
        )
        self.manager.add_budget_entry(
            account_id=1,
            entry_type='outcome',
            amount=50,
            description='Test outcome',
            category='Category2'
        )
        income = sum(entry['amount'] for entry in self.manager.transactions if entry['type'] == 'income')
        outcome = sum(entry['amount'] for entry in self.manager.transactions if entry['type'] == 'outcome')
        balance = income - outcome

        self.assertEqual(income, 200)
        self.assertEqual(outcome, 50)
        self.assertEqual(balance, 150)

    def test_edit_budget_entry(self):
        self.manager.add_budget_entry(
            account_id=1,
            entry_type='income',
            amount=100,
            description='Initial description',
            category='Initial category'
        )

        # Edytujemy wpis bezpośrednio w self.manager.transactions
        entry = self.manager.transactions[0]
        entry['type'] = 'outcome'
        entry['amount'] = 75.50
        entry['description'] = 'Updated description'
        entry['category'] = 'Updated category'
        entry['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.manager.save_budget_to_file()
        self.manager.load_budget_from_file()

        edited_entry = self.manager.transactions[0]
        self.assertEqual(edited_entry['type'], 'outcome')
        self.assertEqual(edited_entry['amount'], 75.50)
        self.assertEqual(edited_entry['description'], 'Updated description')
        self.assertEqual(edited_entry['category'], 'Updated category')

    def test_show_incomes(self):
        self.manager.add_budget_entry(
            account_id=1,
            entry_type='income',
            amount=300,
            description='Income test',
            category='Income category'
        )
        incomes = [entry for entry in self.manager.transactions if entry['type'] == 'income']
        self.assertEqual(len(incomes), 1)
        self.assertEqual(incomes[0]['amount'], 300)

    def test_show_outcomes(self):
        self.manager.add_budget_entry(
            account_id=1,
            entry_type='outcome',
            amount=150,
            description='Outcome test',
            category='Outcome category'
        )
        outcomes = [entry for entry in self.manager.transactions if entry['type'] == 'outcome']
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]['amount'], 150)


if __name__ == '__main__':
    unittest.main()
