#!/usr/bin/env python3
"""
Cursor Composer Conversation Extractor

This script extracts all Cursor Composer conversations from the SQLite database
and saves each one as a separate Markdown file in a 'conversations' directory.

Usage:
    python extract_conversations_to_markdown.py [--db-path PATH]
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
    parser = argparse.ArgumentParser(description='Extract Cursor Composer conversations to Markdown files.')
    parser.add_argument('--db-path', help='Custom path to the SQLite database file')
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

def find_key_value_table(cursor, tables):
    """Find a table that has a key-value structure that might contain composer data."""
    potential_tables = []
    
    for table in tables:
        try:
            # Check if the table has columns that suggest key-value storage
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Look for tables with 'key' and 'value' columns
            if 'key' in column_names and 'value' in column_names:
                potential_tables.append(table)
            # Also check for similar column names
            elif any('key' in col.lower() for col in column_names) and any('value' in col.lower() for col in column_names):
                potential_tables.append(table)
                
        except sqlite3.Error:
            continue
    
    if not potential_tables:
        print("Could not find any key-value tables in the database.")
        return None
    
    print(f"Found potential key-value tables: {', '.join(potential_tables)}")
    
    # Check each potential table for composer data
    for table in potential_tables:
        try:
            # Get column names for this table
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            key_col = next((col[1] for col in columns if 'key' in col[1].lower()), None)
            value_col = next((col[1] for col in columns if 'value' in col[1].lower()), None)
            
            if not key_col or not value_col:
                continue
                
            # Check if this table has composer data
            cursor.execute(f"SELECT {key_col} FROM {table} WHERE {key_col} LIKE '%composer%' OR {key_col} LIKE '%chat%' LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                print(f"Table '{table}' contains composer data")
                return {
                    'table': table,
                    'key_column': key_col,
                    'value_column': value_col
                }
        except sqlite3.Error as e:
            print(f"Error checking table {table}: {e}")
    
    return None

def extract_conversations(cursor, table_info, debug=False):
    """Extract all Cursor Composer conversations from the database."""
    if not table_info:
        return []
        
    table_name = table_info['table']
    key_col = table_info['key_column']
    value_col = table_info['value_column']
    
    try:
        # Query for all composer data entries
        cursor.execute(f"SELECT {key_col}, {value_col} FROM {table_name} WHERE {key_col} LIKE '%composerData:%'")
        rows = cursor.fetchall()
        
        if not rows:
            # Try a different approach if specific prefix not found
            cursor.execute(f"SELECT {key_col}, {value_col} FROM {table_name} WHERE {key_col} LIKE '%composer%' OR {key_col} LIKE '%chat%' OR {key_col} LIKE '%conversation%'")
            rows = cursor.fetchall()
        
        print(f"Found {len(rows)} potential conversation entries")
        
        conversations = []
        for key, value in rows:
            try:
                # Extract ID from key, handling various formats
                if ':' in key:
                    composer_id = key.split(':', 1)[1]
                else:
                    # If no clear ID, generate one based on the key
                    composer_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, key))
                
                # Parse the value as JSON
                data = json.loads(value)
                
                if debug:
                    print(f"Processing entry with key: {key}")
                    print(f"Data type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys in data: {list(data.keys())}")
                
                # Check if data is a dictionary
                if not isinstance(data, dict):
                    if debug:
                        print(f"Skipping entry with key {key}: data is not a dictionary")
                    continue
                
                # Only include entries that have actual conversation data or rich text
                has_conversation = False
                
                # Check if conversation field exists and is a list with items
                if 'conversation' in data and isinstance(data['conversation'], list) and len(data['conversation']) > 0:
                    has_conversation = True
                    
                # Check if richText field exists with content
                has_richtext = 'richText' in data and data['richText']
                
                if has_conversation or has_richtext:
                    conversations.append({
                        'id': composer_id,
                        'data': data
                    })
                elif debug:
                    print(f"Skipping entry with key {key}: no conversation data or rich text found")
                    
            except Exception as e:
                print(f"Error processing conversation {key}: {e}")
                if debug:
                    traceback.print_exc()
                
        return conversations
    except sqlite3.Error as e:
        print(f"Error querying database: {e}")
        if debug:
            traceback.print_exc()
        return []

def clean_text_for_markdown(text):
    """Clean and format text for Markdown."""
    if not text:
        return ""
    
    # Handle HTML entities
    text = html.unescape(text)
    
    # Remove control characters
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')
    
    # Handle code blocks
    # This is a simplified approach - might need to be customized
    text = re.sub(r'```(\w+)\n', r'```\1\n', text)
    
    return text

def convert_rich_text_to_markdown(rich_text):
    """Convert rich text JSON to Markdown."""
    if not rich_text:
        return ""
    
    try:
        # Parse rich text if it's a string
        if isinstance(rich_text, str):
            rich_data = json.loads(rich_text)
        else:
            rich_data = rich_text
        
        # This is a very simplified extraction
        # Full implementation would need to parse the rich text format structure
        # For now we'll just extract text from certain places where it might exist
        
        markdown = ""
        
        # Try to get text from common paths
        if isinstance(rich_data, dict):
            if 'root' in rich_data:
                root = rich_data['root']
                if 'children' in root and len(root['children']) > 0:
                    # Recursively extract text from children
                    for child in root['children']:
                        if 'children' in child:
                            for text_node in child.get('children', []):
                                if isinstance(text_node, dict):
                                    if 'text' in text_node:
                                        markdown += text_node['text'] + "\n"
                                    elif 'detail' in text_node:
                                        # This might be another format type
                                        pass
        
        return markdown.strip()
    except Exception as e:
        return f"Error converting rich text: {e}"

def extract_conversation_text(messages):
    """Extract a readable conversation from the message objects."""
    if not isinstance(messages, list):
        return ""
        
    conversation_text = ""
    
    for msg in messages:
        if not isinstance(msg, dict):
            continue
            
        msg_type = msg.get('type')
        content = msg.get('content', {})
        
        if not isinstance(content, dict):
            content = {}
        
        if msg_type == 1:  # User message
            # Try to extract text from various possible locations
            user_text = content.get('text', '')
            if not user_text and 'richText' in content:
                user_text = convert_rich_text_to_markdown(content['richText'])
            if not user_text:
                user_text = str(content)
                
            conversation_text += f"## User\n\n{clean_text_for_markdown(user_text)}\n\n"
            
        elif msg_type == 2:  # AI response
            ai_text = content.get('text', '')
            if not ai_text and 'richText' in content:
                ai_text = convert_rich_text_to_markdown(content['richText'])
            if not ai_text:
                ai_text = str(content)
                
            conversation_text += f"## Assistant\n\n{clean_text_for_markdown(ai_text)}\n\n"
            
    return conversation_text

def create_markdown_file(conversation, output_dir):
    """Create a markdown file for a single conversation."""
    conv_data = conversation['data']
    conv_id = conversation['id']
    
    # Generate a filename based on ID and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{conv_id[:8]}.md"
    
    # Create the full path
    file_path = os.path.join(output_dir, filename)
    
    # Extract timestamps if available
    timestamp_created = conv_data.get('timestamp', 'Unknown')
    
    # Try to determine a title
    title = "Cursor Composer Conversation"
    user_query = ""
    
    # Try to extract the first user message as title
    if conv_data.get('richText'):
        user_query = convert_rich_text_to_markdown(conv_data['richText'])
    elif conv_data.get('text'):
        user_query = conv_data['text']
    
    if user_query:
        # Take first line or first few words for title
        title_text = user_query.split('\n')[0][:50]
        if title_text:
            title = title_text + ("..." if len(title_text) >= 50 else "")
    
    # Build the markdown content
    markdown_content = f"# {title}\n\n"
    markdown_content += f"**Conversation ID:** {conv_id}\n\n"
    
    # Add the main conversation
    conversation_text = extract_conversation_text(conv_data.get('conversation', []))
    if conversation_text:
        markdown_content += "# Conversation\n\n"
        markdown_content += conversation_text
    
    # Add context info if available
    if 'context' in conv_data and conv_data['context']:
        markdown_content += "# Context\n\n"
        markdown_content += f"```json\n{json.dumps(conv_data['context'], indent=2)}\n```\n\n"
    
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
    
    # Create output directory
    output_dir = "conversations"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Connect to the database and extract conversations
    conn, cursor = connect_to_database(db_path)
    try:
        # Get all tables in the database
        print("Analyzing database structure...")
        tables = get_tables(cursor)
        print(f"Found tables: {', '.join(tables)}")
        
        # Find a table that might contain composer data
        table_info = find_key_value_table(cursor, tables)
        if not table_info:
            print("Could not find a table containing Composer conversation data.")
            print("The database structure may have changed or this database may not contain Composer data.")
            sys.exit(1)
        
        print(f"Using table '{table_info['table']}' with key column '{table_info['key_column']}' and value column '{table_info['value_column']}'")
        
        # Extract conversations
        print("Extracting conversations from database...")
        conversations = extract_conversations(cursor, table_info, debug)
        
        if not conversations:
            print("No conversations with message history were found in the database.")
            sys.exit(0)
        
        print(f"Found {len(conversations)} conversations with message history.")
        
        # Convert and save each conversation
        print("Converting conversations to Markdown...")
        saved_files = []
        for i, conversation in enumerate(conversations, 1):
            try:
                file_path = create_markdown_file(conversation, output_dir)
                saved_files.append(file_path)
                print(f"[{i}/{len(conversations)}] Saved: {file_path}")
            except Exception as e:
                print(f"Error saving conversation {conversation['id']}: {e}")
                if debug:
                    traceback.print_exc()
        
        print(f"\nSuccessfully extracted {len(saved_files)} conversations to {output_dir}/ directory.")
        
    except Exception as e:
        print(f"Error: {e}")
        if debug:
            traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 