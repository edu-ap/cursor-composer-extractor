"""
Extractor module for Cursor Composer data.

This module contains the main functionality for extracting conversation data
from the Cursor SQLite database.
"""

import os
import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from .utils import get_default_db_path


class CursorExtractor:
    """Class for extracting data from Cursor's SQLite database."""

    def __init__(self, db_path: Optional[str] = None, debug: bool = False):
        """Initialize the extractor.
        
        Args:
            db_path: Path to the SQLite database. If None, uses the default path.
            debug: Whether to print debug information.
        """
        self.db_path = db_path or get_default_db_path()
        self.debug = debug
        self.conn = None
        self.cursor = None
        self.keywords = [
            'composer', 'chat', 'conversation', 'claude', 'ai', 'assistant', 
            'gpt', 'prompt', 'message', 'response', 'dialog', 'talk', 'llm'
        ]
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def connect(self):
        """Connect to the SQLite database."""
        if self.debug:
            print(f"Connecting to database at: {self.db_path}")
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        if self.debug:
            print("Connected to database")
        
        return self.cursor
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def get_tables(self) -> List[str]:
        """Get all tables in the database.
        
        Returns:
            List of table names.
        """
        if not self.cursor:
            self.connect()
        
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()
            return [table[0] for table in tables]
        except sqlite3.Error as e:
            if self.debug:
                print(f"Error getting tables: {e}")
            return []
    
    def find_key_value_tables(self, tables: List[str]) -> List[Dict[str, str]]:
        """Find tables that have a key-value structure.
        
        Args:
            tables: List of tables to check.
            
        Returns:
            List of dictionaries with table, key_column, and value_column.
        """
        if not self.cursor:
            self.connect()
        
        key_value_tables = []
        
        for table in tables:
            try:
                # Get column info
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = self.cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Check if this looks like a key-value table
                if ('key' in column_names and 'value' in column_names) or any('key' in col.lower() for col in column_names):
                    # Find the key and value columns
                    key_col = next((col for col in column_names if col.lower() == 'key'), 
                                next((col for col in column_names if 'key' in col.lower()), None))
                    
                    value_cols = [col for col in column_names if col.lower() != key_col.lower()]
                    
                    if key_col and value_cols:
                        # Try to find a row with one of our keywords
                        for keyword in self.keywords:
                            query = f"SELECT {key_col} FROM {table} WHERE {key_col} LIKE '%{keyword}%' LIMIT 1"
                            self.cursor.execute(query)
                            if self.cursor.fetchone():
                                key_value_tables.append({
                                    'table': table,
                                    'key_column': key_col,
                                    'value_columns': value_cols
                                })
                                break
            except sqlite3.Error as e:
                if self.debug:
                    print(f"Error checking table {table}: {e}")
        
        return key_value_tables
    
    def extract_data(self, table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract data from a key-value table.
        
        Args:
            table_info: Dictionary with table, key_column, and value_columns.
            
        Returns:
            List of dictionaries with extracted data.
        """
        if not self.cursor:
            self.connect()
        
        extracted_data = []
        table = table_info['table']
        key_col = table_info['key_column']
        value_cols = table_info['value_columns']
        
        try:
            # Build query to find all potentially relevant entries
            query_parts = []
            for keyword in self.keywords:
                query_parts.append(f"{key_col} LIKE '%{keyword}%'")
            
            query = f"SELECT {key_col}, {', '.join(value_cols)} FROM {table} WHERE {' OR '.join(query_parts)}"
            
            if self.debug:
                print(f"Executing query: {query}")
            
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            if self.debug:
                print(f"Found {len(rows)} potentially relevant entries in table '{table}'")
            
            # Process each row
            for row in rows:
                key = row[0]
                values = row[1:]
                
                entry = {
                    'table': table,
                    'key': key,
                    'data': {}
                }
                
                # Try to parse as JSON
                for i, val in enumerate(values):
                    col_name = value_cols[i]
                    
                    try:
                        if isinstance(val, str) and (val.startswith('{') or val.startswith('[')):
                            entry['data'][col_name] = json.loads(val)
                        else:
                            entry['data'][col_name] = val
                    except json.JSONDecodeError:
                        entry['data'][col_name] = val
                
                extracted_data.append(entry)
            
        except sqlite3.Error as e:
            if self.debug:
                print(f"Error extracting data from table {table}: {e}")
        
        return extracted_data
    
    def extract_all_data(self) -> List[Dict[str, Any]]:
        """Extract all potentially relevant data from the database.
        
        Returns:
            List of dictionaries with extracted data.
        """
        if not self.cursor:
            self.connect()
        
        all_data = []
        
        # Get all tables
        tables = self.get_tables()
        if self.debug:
            print(f"Found tables: {', '.join(tables)}")
        
        # Find key-value tables
        key_value_tables = self.find_key_value_tables(tables)
        if self.debug:
            print(f"Found {len(key_value_tables)} key-value tables")
        
        # Extract data from each key-value table
        for table_info in key_value_tables:
            table_data = self.extract_data(table_info)
            all_data.extend(table_data)
        
        return all_data
    
    def extract_conversations(self) -> List[Dict[str, Any]]:
        """Extract only conversation data from the database.
        
        Returns:
            List of dictionaries with conversation data.
        """
        all_data = self.extract_all_data()
        conversations = []
        
        for entry in all_data:
            # Check if this is a composer data entry
            if 'composerData:' in entry['key']:
                data = entry['data'].get('value', {})
                
                # Try to parse the value as JSON if it's a string
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                
                # Check if it has conversation data
                if isinstance(data, dict) and 'conversation' in data and isinstance(data['conversation'], list) and data['conversation']:
                    conversations.append({
                        'id': entry['key'].split(':', 1)[1] if ':' in entry['key'] else str(uuid.uuid4()),
                        'data': data
                    })
        
        return conversations 