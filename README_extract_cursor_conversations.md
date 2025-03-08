# Cursor Composer Database Extractor

A Python utility for extracting and analyzing conversation data from Cursor's SQLite database.

## Overview

The Cursor Composer Database Extractor analyzes the SQLite database where Cursor stores its data, intelligently searching for and extracting conversation history, AI interactions, and other content from Cursor Composer. This tool helps you access your Cursor conversations for backup, review, or analysis purposes.

## Prerequisites

- Python 3.6 or higher
- SQLite3 (command-line tool)

### Installing SQLite (if not already installed)

On Ubuntu/Debian:
```bash
sudo apt install sqlite3
```

On macOS:
```bash
brew install sqlite
```

On Windows:
- Download the precompiled binaries from [SQLite website](https://www.sqlite.org/download.html)
- Or install via Chocolatey: `choco install sqlite`

## Installation

No special installation is required. Just download the script and make it executable:

```bash
chmod +x extract_cursor_conversations.py
```

## Usage

### Basic Usage

Run the script with default settings to scan the standard Cursor database location and display results in the terminal:

```bash
./extract_cursor_conversations.py
```

### Save Results to a File

To save the extraction results as a JSON file for further analysis:

```bash
./extract_cursor_conversations.py --output cursor_conversations.json
```

### Specify a Custom Database Path

If your Cursor database is in a non-standard location:

```bash
./extract_cursor_conversations.py --db-path /path/to/your/state.vscdb
```

### Combined Options

```bash
./extract_cursor_conversations.py --db-path /path/to/state.vscdb --output results.json
```

## Output Format

The script produces a structured report with the following sections:

1. **Database Information**:
   - SQLite version
   - Database size
   - Table count

2. **Tables List**:
   - All tables found in the database

3. **Conversation Data**:
   - Organized by table
   - Shows table schema
   - Lists conversation items with previews
   - Parses JSON content when possible

4. **Summary Statistics**:
   - Number of tables with conversation data
   - Total number of conversation items found

## How It Works

The script follows these steps to extract Cursor Composer conversation data:

1. **Connects to the SQLite database** where Cursor stores its data
2. **Analyzes the database structure** to identify tables and their schemas
3. **Searches for conversation-related data** by looking for:
   - Tables with "key-value" patterns (common in Electron apps)
   - Keys containing relevant terms (composer, chat, conversation, claude, etc.)
   - Column names related to conversations
4. **Parses and extracts the data**, handling both text and JSON formats
5. **Generates a comprehensive report** which can be displayed or saved to a file

## Script Structure

The script is organized into the following functions:

- `parse_arguments()`: Processes command-line arguments
- `connect_to_database()`: Establishes connection to the SQLite database
- `get_database_info()`: Retrieves basic information about the database
- `list_tables()`: Enumerates all tables in the database
- `extract_conversation_data()`: Core function that searches for and extracts conversation data
- `generate_report()`: Compiles the extracted data into a structured report
- `display_report()`: Formats and displays the report in the terminal
- `save_to_file()`: Saves the report to a JSON file

## Troubleshooting

### Database Not Found

If you get a "Database not found" error:
- Verify that Cursor is installed on your system
- Check if the database exists at the default location
- Use the `--db-path` option to specify the correct path

### Permission Issues

If you encounter permission errors:
- Ensure you have read permissions for the database file
- The SQLite database may be locked if Cursor is currently running

### No Conversation Data Found

If the script runs but doesn't find any conversation data:
- You may not have used Cursor Composer yet
- The database might be using a different storage pattern
- Try examining a backup of the database: `~/.config/Cursor/User/globalStorage/state.vscdb.backup`

## Limitations

- The script is designed for Cursor's current database structure and may need updates if Cursor changes its storage format
- Very large JSON objects may be truncated in the terminal display (but will be complete in the saved JSON file)
- The script cannot extract conversations that have been explicitly deleted by the user

## License

This script is provided "as is" without warranties or conditions of any kind. You are free to modify and distribute it according to your needs.

## Acknowledgments

- This tool was created to help users access their own conversation data stored in Cursor
- It is not affiliated with or endorsed by the official Cursor development team 