# Cursor Composer Extractor

Extract your Cursor Composer AI conversations and save them as Markdown or JSON files for backup, analysis, or sharing.

## Overview

Cursor Composer Extractor is a tool that allows you to access, extract, and convert your AI conversations from [Cursor](https://cursor.sh/), the AI-powered code editor. The tool looks for conversation data in Cursor's SQLite database and converts it to readable formats.

## Features

- 🔍 Extract conversations from Cursor's SQLite database
- 📝 Convert rich text to Markdown
- 💾 Save as individual files or combined documents
- 🔎 Find where Cursor stores your conversation data
- 🔄 Support for multiple output formats (JSON, Markdown)
- 🧩 Extract even partial or incomplete conversations
- 🔧 Works with Cursor v2023 and newer

## Repository Structure

```
cursor-composer-extractor/
├── src/
│   └── cursor_extractor/
│       ├── __init__.py       # Package initialization
│       ├── extractor.py      # Core extraction functionality
│       ├── utils.py          # Helper functions 
│       ├── parsers.py        # Output format parsers
│       └── cli.py            # Command-line interface
├── tests/
│   ├── __init__.py           # Test package initialization
│   ├── test_extractor.py     # Tests for extractor module
│   └── test_parsers.py       # Tests for parsers module
├── examples/
│   ├── extract_to_markdown.py  # Example of extracting to Markdown
│   └── analyze_conversations.py # Example of analyzing conversations
├── extract_cursor_conversations.py  # Original extraction script
├── extract_all_cursor_data.py      # Comprehensive extraction script
├── list_cursor_logs.sh             # Bash script for finding logs
├── README.md                 # This file
├── LICENSE                   # MIT license
├── .gitignore                # Git ignore file
├── requirements.txt          # Package dependencies
└── setup.py                  # Package installation script
```

## Installation

### Prerequisites

- Python 3.6 or higher
- SQLite3

### Install from GitHub

```bash
# Clone the repository
git clone https://github.com/edu-ap/cursor-composer-extractor.git

# Navigate to the directory
cd cursor-composer-extractor

# Install dependencies
pip install -r requirements.txt
```

### Install as a Python Package

```bash
# Install directly from GitHub
pip install git+https://github.com/edu-ap/cursor-composer-extractor.git

# Or install after cloning
git clone https://github.com/edu-ap/cursor-composer-extractor.git
cd cursor-composer-extractor
pip install -e .
```

## Getting Started

### Using the Library

```python
from cursor_extractor.extractor import CursorExtractor
from cursor_extractor.parsers import MarkdownOutputParser

# Initialize the extractor
extractor = CursorExtractor()

# Extract conversations
conversations = extractor.extract_conversations()

# Save as Markdown
output_dir = "my_conversations"
for conversation in conversations:
    parsed = MarkdownOutputParser.parse_conversation(conversation)
    MarkdownOutputParser.save_conversation(parsed, output_dir)
```

### Using the Command Line

The package includes a command-line interface:

```bash
# Extract conversations to Markdown
python -m cursor_extractor extract --format markdown --output-dir my_conversations

# Extract all data to JSON
python -m cursor_extractor extract-all --format json
```

### Example Scripts

Run the provided examples to see the tool in action:

```bash
# Extract conversations to Markdown
python examples/extract_to_markdown.py

# Analyze your conversations
python examples/analyze_conversations.py
```

## Usage

The repository also includes several standalone scripts for different use cases:

### 1. Extract All Cursor Data

This script extracts all potential conversation data from the Cursor database:

```bash
python extract_all_cursor_data.py
```

Options:
- `--db-path PATH`: Custom path to the SQLite database file
- `--format {json,markdown,both}`: Output format (default: both)
- `--debug`: Enable debug output

### 2. Extract Conversations

This script focuses on extracting only conversation data:

```bash
python extract_cursor_conversations.py
```

Options:
- `--db-path PATH`: Custom path to the SQLite database file
- `--output FILE`: Save results to a JSON file

### 3. List Cursor Logs

This Bash script helps locate and analyze Cursor log files:

```bash
./list_cursor_logs.sh
```

## Generated Files

When running this tool, several files and directories will be created:

- `cursor_data_json/`: Contains extracted conversation data in JSON format
- `cursor_data_markdown/`: Contains extracted conversation data in Markdown format
- `conversations/`: Default directory for conversation exports
- `cursor_logs_report.md`: Report on Cursor log files found on your system
- `cursor_conversations.json`: Aggregated collection of all conversations

These files are excluded from version control via .gitignore as they contain your personal data. You should manually back up any important extracted conversations.

## How It Works

Cursor Composer conversations are stored in an SQLite database, typically located at:

- **Windows**: `%APPDATA%\Cursor\User\globalStorage\state.vscdb`
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb`
- **Linux**: `~/.config/Cursor/User/globalStorage/state.vscdb`

This tool:
1. Connects to the database
2. Searches for tables that might contain conversation data
3. Extracts the data and parses the JSON structures
4. Converts the data to readable formats (Markdown and/or JSON)
5. Saves the output to files

## File Structure

Each conversation is stored with information like:
- A unique conversation ID
- The conversation history (user and AI messages)
- Context information (file paths, active files, etc.)
- Rich text content

## Troubleshooting

### Database not found

If the script cannot find your Cursor database:
1. Check if Cursor is installed on your system
2. Use the `--db-path` option to specify the correct location
3. Look for the database file manually in the locations mentioned above

### Permission errors

If you encounter permission errors:
1. Make sure Cursor is closed
2. Check if you have read permissions for the database file

### No conversations found

If no conversations are found:
1. You may not have used Cursor Composer yet
2. Your version of Cursor might use a different storage structure
3. Conversations might have been cleared

## License

MIT © [edu-ap](https://github.com/edu-ap) 2025

## Disclaimer

This tool is not affiliated with or endorsed by Cursor. It is an independent project created to help users access their own data stored in Cursor's database.

The tool does not send any data over the internet - all processing is done locally on your machine.