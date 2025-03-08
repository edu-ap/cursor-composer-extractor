#!/usr/bin/env python3
"""
Cursor Data Extractor

This script extracts all potential conversation-related data from the Cursor SQLite database
and saves each entry as a separate Markdown or JSON file.

Usage:
    python extract_all_cursor_data.py [--db-path PATH] [--format FORMAT]
"""

import sqlite3
import json
import os
import sys
import argparse
import re
import html
from datetime import datetime
from pathlib import Path
import uuid
import traceback

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract all conversation-related data from Cursor database.')
    parser.add_argument('--db-path', help='Custom path to the SQLite database file')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both',
                        help='Output format: json, markdown, or both (default)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    return parser.parse_args()

def connect_to_database(db_path):
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        print(f"Database path: {db_path}")
        sys.exit(1)

def get_tables(cursor):
    """Get all tables in the database."""
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        return [table[0] for table in tables]
    except sqlite3.Error as e:
        print(f"Error getting tables: {e}")
        return []

def extract_all_data(cursor, tables, debug=False):
    """Extract all potential conversation data from all tables."""
    all_data = []
    keywords = [
        'composer', 'chat', 'conversation', 'claude', 'ai', 'assistant', 
        'gpt', 'prompt', 'message', 'response', 'dialog', 'talk', 'llm'
    ]
    
    for table in tables:
        try:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if debug:
                print(f"Table '{table}' has columns: {column_names}")
            
            # Check if this looks like a key-value table
            if ('key' in column_names and 'value' in column_names) or any('key' in col.lower() for col in column_names):
                # Find the key and value columns
                key_col = next((col for col in column_names if col.lower() == 'key'), 
                              next((col for col in column_names if 'key' in col.lower()), None))
                
                value_cols = [col for col in column_names if col.lower() != key_col.lower()]
                
                if not key_col or not value_cols:
                    if debug:
                        print(f"Skipping table '{table}': couldn't identify key/value columns")
                    continue
                
                # Build the query to find all potentially relevant entries
                query_parts = []
                for keyword in keywords:
                    query_parts.append(f"{key_col} LIKE '%{keyword}%'")
                
                query = f"SELECT {key_col}, {', '.join(value_cols)} FROM {table} WHERE {' OR '.join(query_parts)}"
                
                if debug:
                    print(f"Executing query: {query}")
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                if debug:
                    print(f"Found {len(rows)} potential entries in table '{table}'")
                
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
                    
                    all_data.append(entry)
            
            # Check if there are other columns that might contain chat data
            chat_cols = []
            for col in column_names:
                for keyword in keywords:
                    if keyword.lower() in col.lower():
                        chat_cols.append(col)
                        break
            
            if chat_cols and debug:
                print(f"Found potential chat columns in '{table}': {chat_cols}")
                
            # If we found chat-related columns, extract those rows
            if chat_cols:
                cursor.execute(f"SELECT * FROM {table} LIMIT 100")
                rows = cursor.fetchall()
                
                for row in rows:
                    entry = {
                        'table': table,
                        'key': f"row_{table}_{uuid.uuid4().hex[:8]}",
                        'data': {}
                    }
                    
                    for i, col in enumerate(column_names):
                        entry['data'][col] = row[i]
                    
                    all_data.append(entry)
                
        except sqlite3.Error as e:
            if debug:
                print(f"Error processing table '{table}': {e}")
                traceback.print_exc()
    
    return all_data

def save_as_json(entry, output_dir):
    """Save an entry as a JSON file."""
    # Generate filename
    safe_key = re.sub(r'[^\w\-]', '_', entry['key'])
    filename = f"{entry['table']}_{safe_key}.json"
    file_path = os.path.join(output_dir, filename)
    
    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(entry, f, indent=2)
    
    return file_path

def try_extract_text(data, debug=False):
    """Try to extract human-readable text from various data structures."""
    if isinstance(data, str):
        return data
    
    if isinstance(data, dict):
        # Check for common text fields
        for key in ['text', 'content', 'message', 'value', 'richText']:
            if key in data:
                if isinstance(data[key], str):
                    return data[key]
                else:
                    return try_extract_text(data[key], debug)
        
        # Check for conversation array
        if 'conversation' in data and isinstance(data['conversation'], list):
            text = ""
            for item in data['conversation']:
                if isinstance(item, dict):
                    item_text = try_extract_text(item, debug)
                    if item_text:
                        text += item_text + "\n\n"
            return text.strip()
        
        # Look for nested structure with text
        for key, value in data.items():
            if key in ['root', 'children', 'messages', 'content']:
                text = try_extract_text(value, debug)
                if text:
                    return text
    
    if isinstance(data, list):
        text = ""
        for item in data:
            item_text = try_extract_text(item, debug)
            if item_text:
                text += item_text + "\n\n"
        return text.strip()
    
    # Fallback: just stringify
    if debug:
        print(f"Couldn't extract text from data type: {type(data)}")
    return str(data)

def save_as_markdown(entry, output_dir, debug=False):
    """Save an entry as a Markdown file."""
    # Generate filename
    safe_key = re.sub(r'[^\w\-]', '_', entry['key'])
    filename = f"{entry['table']}_{safe_key}.md"
    file_path = os.path.join(output_dir, filename)
    
    # Generate title
    title = entry['key']
    if len(title) > 50:
        title = title[:47] + '...'
    
    # Build markdown content
    markdown_content = f"# {title}\n\n"
    markdown_content += f"**Table:** {entry['table']}\n\n"
    markdown_content += f"**Key:** {entry['key']}\n\n"
    
    # Try to extract readable text
    for col, value in entry['data'].items():
        markdown_content += f"## {col}\n\n"
        
        # Try to convert to readable format
        if isinstance(value, (dict, list)):
            # Try to extract text first
            text = try_extract_text(value, debug)
            if text and len(text) > 5:  # Only include if we got meaningful text
                markdown_content += f"{text}\n\n"
            
            # Include full JSON structure
            markdown_content += f"```json\n{json.dumps(value, indent=2)}\n```\n\n"
        else:
            markdown_content += f"{value}\n\n"
    
    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return file_path

def main():
    args = parse_arguments()
    debug = args.debug
    
    # Set the database path
    if args.db_path:
        db_path = args.db_path
    else:
        db_path = os.path.expanduser("~/.config/Cursor/User/globalStorage/state.vscdb")
    
    print(f"Looking for Cursor database at: {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        print("Please check if Cursor is installed or specify a different path with --db-path")
        sys.exit(1)
    
    # Create output directories
    output_format = args.format
    
    if output_format in ['json', 'both']:
        json_dir = "cursor_data_json"
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)
            print(f"Created JSON output directory: {json_dir}")
    
    if output_format in ['markdown', 'both']:
        markdown_dir = "cursor_data_markdown"
        if not os.path.exists(markdown_dir):
            os.makedirs(markdown_dir)
            print(f"Created Markdown output directory: {markdown_dir}")
    
    # Connect to the database and extract data
    conn, cursor = connect_to_database(db_path)
    try:
        # Get all tables
        print("Analyzing database structure...")
        tables = get_tables(cursor)
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Extract all potentially relevant data
        print("Extracting all potential conversation data...")
        all_data = extract_all_data(cursor, tables, debug)
        
        if not all_data:
            print("No conversation-related data was found in the database.")
            sys.exit(0)
        
        print(f"Found {len(all_data)} potentially relevant entries.")
        
        # Save data in requested format(s)
        json_files = []
        markdown_files = []
        
        if output_format in ['json', 'both']:
            print(f"Saving entries as JSON files to {json_dir}/...")
            for i, entry in enumerate(all_data, 1):
                try:
                    file_path = save_as_json(entry, json_dir)
                    json_files.append(file_path)
                    if i % 10 == 0:
                        print(f"Saved {i}/{len(all_data)} entries as JSON")
                except Exception as e:
                    if debug:
                        print(f"Error saving entry as JSON: {e}")
                        traceback.print_exc()
        
        if output_format in ['markdown', 'both']:
            print(f"Saving entries as Markdown files to {markdown_dir}/...")
            for i, entry in enumerate(all_data, 1):
                try:
                    file_path = save_as_markdown(entry, markdown_dir, debug)
                    markdown_files.append(file_path)
                    if i % 10 == 0:
                        print(f"Saved {i}/{len(all_data)} entries as Markdown")
                except Exception as e:
                    if debug:
                        print(f"Error saving entry as Markdown: {e}")
                        traceback.print_exc()
        
        # Summary
        print("\nExtraction summary:")
        if output_format in ['json', 'both']:
            print(f"- Saved {len(json_files)} entries as JSON files in {json_dir}/")
        if output_format in ['markdown', 'both']:
            print(f"- Saved {len(markdown_files)} entries as Markdown files in {markdown_dir}/")
        
    except Exception as e:
        print(f"Error: {e}")
        if debug:
            traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 