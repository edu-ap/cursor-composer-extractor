#!/usr/bin/env python3
"""
Cursor Composer Database Extractor

This script connects to the Cursor SQLite database and extracts potential conversation
data from it. It looks for keys related to Composer, chat, or conversations.

Usage:
    python extract_cursor_conversations.py [--output OUTPUT_FILE]

Options:
    --output OUTPUT_FILE    Save results to a JSON file instead of displaying on screen
"""

import sqlite3
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract Cursor Composer conversations from the SQLite database.')
    parser.add_argument('--output', help='Output file to save results (JSON format)')
    parser.add_argument('--db-path', help='Custom path to the SQLite database file')
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

def get_database_info(cursor):
    """Get basic information about the database."""
    # Get SQLite version
    cursor.execute("SELECT sqlite_version();")
    version = cursor.fetchone()[0]
    
    # Get database size
    db_size = os.path.getsize(db_path)
    db_size_mb = db_size / (1024 * 1024)
    
    # Get table counts
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    table_count = cursor.fetchone()[0]
    
    return {
        "sqlite_version": version,
        "database_size_bytes": db_size,
        "database_size_mb": round(db_size_mb, 2),
        "table_count": table_count
    }

def list_tables(cursor):
    """List all tables in the database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

def extract_conversation_data(cursor, tables):
    """Extract potential conversation data from the database."""
    results = {}
    
    # Common table names for key-value storage in Electron apps
    possible_kv_tables = ['items', 'ItemTable', 'keyvaluepairs', 'storage', 'state']
    
    # Keywords to look for in keys
    keywords = ['composer', 'chat', 'conversation', 'claude', 'gpt', 'cursor', 'ai', 'assistant']
    
    # Search in each table
    for table in tables:
        table_data = {"schema": [], "conversation_data": []}
        
        # Get table schema
        try:
            cursor.execute(f"PRAGMA table_info({table});")
            schema = cursor.fetchall()
            table_data["schema"] = [col[1] for col in schema]  # Get column names
            
            # Check if this might be a key-value table
            if table.lower() in possible_kv_tables or ('key' in table_data["schema"] and 'value' in table_data["schema"]):
                # For key-value tables, search for keys matching our keywords
                query = f"SELECT key, value FROM {table} WHERE " + " OR ".join([f"key LIKE '%{kw}%'" for kw in keywords])
                cursor.execute(query)
                rows = cursor.fetchall()
                
                if rows:
                    for key, value in rows:
                        try:
                            # Try to parse the value as JSON
                            parsed_value = json.loads(value)
                            table_data["conversation_data"].append({
                                "key": key,
                                "value_type": "json",
                                "value": parsed_value
                            })
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, store as text with a preview
                            preview = str(value)[:200] + "..." if value and len(str(value)) > 200 else value
                            table_data["conversation_data"].append({
                                "key": key,
                                "value_type": "text",
                                "value_preview": preview
                            })
            else:
                # For other tables, look for columns with conversation-like names
                conversation_cols = [col for col in table_data["schema"] if any(kw in col.lower() for kw in keywords)]
                if conversation_cols:
                    query = f"SELECT * FROM {table} LIMIT 10"
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    if rows:
                        # Extract data from the relevant columns
                        col_indices = [table_data["schema"].index(col) for col in conversation_cols]
                        for row in rows:
                            row_data = {}
                            for idx in col_indices:
                                col_name = table_data["schema"][idx]
                                row_data[col_name] = row[idx]
                            table_data["conversation_data"].append(row_data)
        except sqlite3.Error as e:
            table_data["error"] = str(e)
        
        # Only include tables with actual conversation data
        if table_data["conversation_data"]:
            results[table] = table_data
    
    return results

def generate_report(db_info, tables, conversation_data):
    """Generate a comprehensive report about the database and extracted data."""
    report = {
        "extraction_time": datetime.now().isoformat(),
        "database_info": db_info,
        "tables_found": tables,
        "conversation_data": conversation_data
    }
    
    # Add a summary section
    tables_with_data = len(conversation_data.keys())
    total_conversations = sum(len(data["conversation_data"]) for data in conversation_data.values())
    
    report["summary"] = {
        "tables_with_conversation_data": tables_with_data,
        "total_conversation_items": total_conversations
    }
    
    return report

def display_report(report):
    """Display the report in a readable format on the console."""
    print("\n" + "="*80)
    print(f"CURSOR DATABASE ANALYSIS REPORT - {report['extraction_time']}")
    print("="*80)
    
    print(f"\nDatabase Info:")
    print(f"  SQLite Version: {report['database_info']['sqlite_version']}")
    print(f"  Database Size: {report['database_info']['database_size_mb']} MB")
    print(f"  Total Tables: {report['database_info']['table_count']}")
    
    print(f"\nTables with Conversation Data: {report['summary']['tables_with_conversation_data']}")
    print(f"Total Conversation Items Found: {report['summary']['total_conversation_items']}")
    
    for table, data in report["conversation_data"].items():
        print(f"\n{'-'*80}")
        print(f"TABLE: {table}")
        print(f"Schema: {', '.join(data['schema'])}")
        print(f"Found {len(data['conversation_data'])} conversation items:")
        
        for i, item in enumerate(data["conversation_data"], 1):
            print(f"\n  Item {i}:")
            if "key" in item:
                print(f"    Key: {item['key']}")
                if item['value_type'] == 'json':
                    print(f"    Value Type: JSON")
                    print(f"    Preview: {str(item['value'])[:150]}...")
                else:
                    print(f"    Value Type: Text")
                    print(f"    Preview: {item['value_preview']}")
            else:
                for k, v in item.items():
                    preview = str(v)[:150] + "..." if v and len(str(v)) > 150 else v
                    print(f"    {k}: {preview}")
    
    print("\n" + "="*80)
    print("End of Report")
    print("="*80)

def save_to_file(report, output_path):
    """Save the report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {output_path}")

if __name__ == "__main__":
    args = parse_arguments()
    
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
    
    # Connect to the database
    print("Connecting to database...")
    conn, cursor = connect_to_database(db_path)
    
    try:
        # Extract data
        print("Getting database information...")
        db_info = get_database_info(cursor)
        
        print("Listing tables...")
        tables = list_tables(cursor)
        
        print(f"Found {len(tables)} tables. Searching for conversation data...")
        conversation_data = extract_conversation_data(cursor, tables)
        
        # Generate and output report
        report = generate_report(db_info, tables, conversation_data)
        
        if args.output:
            save_to_file(report, args.output)
        else:
            display_report(report)
            
        print("\nTIP: To save the results to a file, run:")
        print(f"python {os.path.basename(__file__)} --output cursor_conversations.json")
            
    except Exception as e:
        print(f"Error during extraction: {e}")
    finally:
        conn.close()
        print("\nDatabase connection closed.") 