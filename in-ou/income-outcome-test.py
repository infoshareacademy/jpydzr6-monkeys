import unittest
import os
from datetime import datetime
from income_outcome import Transactions, Operations
from account import db, Account


class TestTransactions(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_operations.db'
        self.test_table = 'operations'

        # Initialize test database
        db.init(self.test_db)
        db.connect()
        db.create_tables([Account, Operations])

        # Create a test account
        self.test_account = Account.create(
            account_number="123456",
            account_name="Test Account",
            balance=0,
            currency_id="PLN"
        )

        # Initialize Transactions
        self.transactions = Transactions(db_name=self.test_db, table_name=self.test_table)
        self.transactions.create_table()

    def tearDown(self):
        db.drop_tables([Account, Operations])
        db.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_budget_entry(self):
        self.transactions.add_budget_entry(
            account_id=self.test_account.account_id,
            entry_type="income",
            amount=100.50,
            description="Test income",
            category="Test category"
        )

        operations = Operations.select().where(Operations.account_id == self.test_account.account_id)
        self.assertEqual(operations.count(), 1)
        op = operations.first()
        self.assertEqual(op.entry_type, "income")
        self.assertEqual(op.amount, 10050)  # Stored in grosze
        self.assertEqual(op.description, "Test income")
        self.assertEqual(op.category, "Test category")

    def test_delete_budget_entry(self):
        operation = Operations.create(
            entry_type="income",
            amount=10000,
            description="To delete",
            category="Test",
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            account_id=self.test_account.account_id
        )

        self.transactions.delete_budget_entry(entry_id=operation.id)

        operations = Operations.select().where(Operations.account_id == self.test_account.account_id)
        self.assertEqual(operations.count(), 0)

    def test_show_budget_summary(self):
        self.transactions.add_budget_entry(
            account_id=self.test_account.account_id,
            entry_type="income",
            amount=200,
            description="Test income",
            category="Category1"
        )
        self.transactions.add_budget_entry(
            account_id=self.test_account.account_id,
            entry_type="outcome",
            amount=50,
            description="Test outcome",
            category="Category2"
        )

        # Reload transactions
        self.transactions.load_budget_from_file()

        income = sum(entry['amount'] for entry in self.transactions.transactions if entry['type'] == 'income')
        outcome = sum(entry['amount'] for entry in self.transactions.transactions if entry['type'] == 'outcome')
        balance = income - outcome

        self.assertEqual(income, 200)
        self.assertEqual(outcome, 50)
        self.assertEqual(balance, 150)

    def test_edit_budget_entry(self):
        operation = Operations.create(
            entry_type="income",
            amount=10000,
            description="Initial description",
            category="Initial category",
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            account_id=self.test_account.account_id
        )

        self.transactions.edit_budget_entry(
            entry_id=operation.id,
            new_entry_type="outcome",
            new_amount=75.50,
            new_description="Updated description",
            new_category="Updated category"
        )

        updated_operation = Operations.get_by_id(operation.id)
        self.assertEqual(updated_operation.entry_type, "outcome")
        self.assertEqual(updated_operation.amount, 7550)
        self.assertEqual(updated_operation.description, "Updated description")
        self.assertEqual(updated_operation.category, "Updated category")

    def test_show_incomes(self):
        self.transactions.add_budget_entry(
            account_id=self.test_account.account_id,
            entry_type="income",
            amount=300,
            description="Income test",
            category="Income category"
        )

        # Reload transactions
        self.transactions.load_budget_from_file()

        incomes = [entry for entry in self.transactions.transactions if entry['type'] == 'income']
        self.assertEqual(len(incomes), 1)
        self.assertEqual(incomes[0]['amount'], 300)

    def test_show_outcomes(self):
        self.transactions.add_budget_entry(
            account_id=self.test_account.account_id,
            entry_type="outcome",
            amount=150,
            description="Outcome test",
            category="Outcome category"
        )

        # Reload transactions
        self.transactions.load_budget_from_file()

        outcomes = [entry for entry in self.transactions.transactions if entry['type'] == 'outcome']
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]['amount'], 150)


if __name__ == "__main__":
    unittest.main()
