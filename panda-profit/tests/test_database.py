import unittest
import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db,
    get_connection,
    add_expense_category,
    get_all_expense_categories,
    delete_expense_category,
    DB_PATH
)


class TestExpenseCategories(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a test database before running tests."""
        # Use a test database
        global DB_PATH
        cls.test_db_path = os.path.join(os.path.dirname(__file__), 'test_panda_profit.db')

        # Patch the DB_PATH in the database module
        import database
        database.DB_PATH = cls.test_db_path
        global DB_PATH
        DB_PATH = cls.test_db_path

        init_db()

    @classmethod
    def tearDownClass(cls):
        """Remove test database after all tests."""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def setUp(self):
        """Clear expense_categories table before each test."""
        conn = get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM expense_categories')
        conn.commit()
        conn.close()

    def test_add_expense_category(self):
        """Test adding a new expense category."""
        category_id = add_expense_category('Packaging', 'supplies')
        self.assertIsNotNone(category_id)
        self.assertIsInstance(category_id, int)

    def test_get_all_expense_categories(self):
        """Test retrieving all expense categories."""
        add_expense_category('Packaging', 'supplies')
        add_expense_category('Shipping', 'shipping')

        categories = get_all_expense_categories()
        self.assertEqual(len(categories), 2)
        self.assertEqual(categories[0]['name'], 'Packaging')
        self.assertEqual(categories[1]['name'], 'Shipping')

    def test_delete_expense_category(self):
        """Test deleting an expense category."""
        category_id = add_expense_category('Packaging', 'supplies')
        delete_expense_category(category_id)

        categories = get_all_expense_categories()
        self.assertEqual(len(categories), 0)

    def test_category_has_required_fields(self):
        """Test that category has all required fields."""
        add_expense_category('Packaging', 'supplies')

        categories = get_all_expense_categories()
        category = categories[0]

        self.assertIn('id', category)
        self.assertIn('name', category)
        self.assertIn('category_type', category)
        self.assertIn('created_at', category)
        self.assertIn('updated_at', category)

    def test_default_categories_created(self):
        """Test that default categories are created during init."""
        # Reinitialize to populate defaults
        init_db()

        categories = get_all_expense_categories()
        # Should have at least some default categories
        self.assertGreater(len(categories), 0)


if __name__ == '__main__':
    unittest.main()
