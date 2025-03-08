"""
Tests for the extractor module.
"""

import unittest
import os
import tempfile
import json
import sqlite3
from unittest.mock import patch, MagicMock

from src.cursor_extractor.extractor import CursorExtractor


class TestCursorExtractor(unittest.TestCase):
    """Tests for the CursorExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary SQLite database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create a test database with sample data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create test tables
        cursor.execute('CREATE TABLE ItemTable (key TEXT, value TEXT)')
        cursor.execute('CREATE TABLE AnotherTable (id INTEGER, name TEXT)')
        
        # Insert test data
        cursor.execute(
            "INSERT INTO ItemTable VALUES (?, ?)",
            ("composerData:test-id", json.dumps({
                "composerId": "test-id",
                "richText": "Test rich text",
                "conversation": [
                    {"type": 1, "content": {"text": "User message"}},
                    {"type": 2, "content": {"text": "AI response"}}
                ]
            }))
        )
        
        conn.commit()
        conn.close()
        
        # Create the extractor with the test database
        self.extractor = CursorExtractor(db_path=self.db_path)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Close the extractor connection
        if self.extractor.conn:
            self.extractor.close()
        
        # Delete the temporary database
        os.unlink(self.db_path)
    
    def test_connect(self):
        """Test connecting to the database."""
        self.extractor.connect()
        self.assertIsNotNone(self.extractor.conn)
        self.assertIsNotNone(self.extractor.cursor)
    
    def test_get_tables(self):
        """Test getting tables from the database."""
        tables = self.extractor.get_tables()
        self.assertIn('ItemTable', tables)
        self.assertIn('AnotherTable', tables)
    
    def test_find_key_value_tables(self):
        """Test finding key-value tables."""
        tables = self.extractor.get_tables()
        key_value_tables = self.extractor.find_key_value_tables(tables)
        
        self.assertEqual(len(key_value_tables), 1)
        self.assertEqual(key_value_tables[0]['table'], 'ItemTable')
        self.assertEqual(key_value_tables[0]['key_column'], 'key')
    
    def test_extract_conversations(self):
        """Test extracting conversations."""
        conversations = self.extractor.extract_conversations()
        
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0]['id'], 'test-id')
        self.assertEqual(len(conversations[0]['data']['conversation']), 2)


if __name__ == '__main__':
    unittest.main() 