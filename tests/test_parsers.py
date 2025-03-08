"""
Tests for the parsers module.
"""

import unittest
import tempfile
import os
import json
import shutil
from pathlib import Path

from src.cursor_extractor.parsers import JsonOutputParser, MarkdownOutputParser


class TestJsonOutputParser(unittest.TestCase):
    """Tests for the JsonOutputParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a sample entry
        self.sample_entry = {
            'table': 'TestTable',
            'key': 'test-key',
            'data': {
                'value': {
                    'conversation': [
                        {'type': 1, 'content': {'text': 'User message'}},
                        {'type': 2, 'content': {'text': 'AI response'}}
                    ]
                }
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_parse_entry(self):
        """Test parsing an entry."""
        parsed = JsonOutputParser.parse_entry(self.sample_entry)
        self.assertEqual(parsed, self.sample_entry)
    
    def test_save_entry(self):
        """Test saving an entry as a JSON file."""
        file_path = JsonOutputParser.save_entry(self.sample_entry, self.temp_dir)
        
        self.assertTrue(os.path.exists(file_path))
        
        # Check the content
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_entry = json.load(f)
        
        self.assertEqual(saved_entry, self.sample_entry)
    
    def test_save_all(self):
        """Test saving all entries to a single file."""
        entries = [self.sample_entry, self.sample_entry]
        output_file = os.path.join(self.temp_dir, 'all_entries.json')
        
        saved_file = JsonOutputParser.save_all(entries, output_file)
        
        self.assertTrue(os.path.exists(saved_file))
        
        # Check the content
        with open(saved_file, 'r', encoding='utf-8') as f:
            saved_entries = json.load(f)
        
        self.assertEqual(len(saved_entries), 2)
        self.assertEqual(saved_entries, entries)


class TestMarkdownOutputParser(unittest.TestCase):
    """Tests for the MarkdownOutputParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a sample conversation
        self.sample_conversation = {
            'id': 'test-id',
            'data': {
                'richText': 'Test query',
                'conversation': [
                    {'type': 1, 'content': {'text': 'User message'}},
                    {'type': 2, 'content': {'text': 'AI response'}}
                ],
                'context': {'file': 'test.py'}
            }
        }
        
        # Create a sample entry
        self.sample_entry = {
            'table': 'TestTable',
            'key': 'test-key',
            'data': {
                'value': 'Test value'
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_parse_conversation(self):
        """Test parsing a conversation."""
        parsed = MarkdownOutputParser.parse_conversation(self.sample_conversation)
        
        self.assertEqual(parsed['id'], 'test-id')
        self.assertEqual(parsed['title'], 'Test query')
        self.assertIsNotNone(parsed['conversation_text'])
        self.assertEqual(parsed['context_info'], {'file': 'test.py'})
    
    def test_save_conversation(self):
        """Test saving a conversation as a Markdown file."""
        parsed = MarkdownOutputParser.parse_conversation(self.sample_conversation)
        file_path = MarkdownOutputParser.save_conversation(parsed, self.temp_dir)
        
        self.assertTrue(os.path.exists(file_path))
        
        # Check the content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('# Test query', content)
        self.assertIn('**Conversation ID:** test-id', content)
        self.assertIn('## User', content)
        self.assertIn('## Assistant', content)
        self.assertIn('# Context', content)
        self.assertIn('"file": "test.py"', content)
    
    def test_parse_entry(self):
        """Test parsing an entry."""
        parsed = MarkdownOutputParser.parse_entry(self.sample_entry)
        
        self.assertEqual(parsed['table'], 'TestTable')
        self.assertEqual(parsed['key'], 'test-key')
        self.assertEqual(parsed['title'], 'test-key')
        self.assertEqual(len(parsed['sections']), 1)
        self.assertEqual(parsed['sections'][0]['title'], 'value')
    
    def test_save_entry(self):
        """Test saving an entry as a Markdown file."""
        parsed = MarkdownOutputParser.parse_entry(self.sample_entry)
        file_path = MarkdownOutputParser.save_entry(parsed, self.temp_dir)
        
        self.assertTrue(os.path.exists(file_path))
        
        # Check the content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('# test-key', content)
        self.assertIn('**Table:** TestTable', content)
        self.assertIn('## value', content)
        self.assertIn('Test value', content)


if __name__ == '__main__':
    unittest.main() 