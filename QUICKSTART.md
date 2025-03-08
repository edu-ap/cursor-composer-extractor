# Cursor Composer Extractor - Quick Start Guide

This guide provides quick instructions to get started with the Cursor Composer Database Extractor on Ubuntu.

## 1. Install SQLite

The script requires SQLite to be installed on your system. Run:

```bash
sudo apt install sqlite3
```

## 2. Make the Script Executable

Make sure the script is executable by running:

```bash
chmod +x extract_cursor_conversations.py
```

## 3. Run the Script

### Basic Usage
To run the script and view the results in the terminal:

```bash
./extract_cursor_conversations.py
```

### Save Results to a File
To save the results to a JSON file for further analysis:

```bash
./extract_cursor_conversations.py --output cursor_data.json
```

## 4. Common Issues

### SQLite Not Found
If you encounter an error about SQLite not being found, install it using the command in step 1.

### Permission Denied
If you get a permission error when trying to access the database:

```bash
# Make sure Cursor is closed
# Backup the database first
cp ~/.config/Cursor/User/globalStorage/state.vscdb ~/cursor_db_backup.db

# Then try running the script again
```

### Database Not Found
If the database is not found in the default location:

1. Check if Cursor is installed
2. Look for the database in alternative locations:
   ```bash
   find ~/.config -name "state.vscdb" 2>/dev/null
   ```
3. Use the custom path option if found:
   ```bash
   ./extract_cursor_conversations.py --db-path /path/to/your/state.vscdb
   ```

## 5. Next Steps

- Check the full README for detailed information
- Examine the JSON output in a text editor or use `jq` for advanced filtering:
  ```bash
  sudo apt install jq
  cat cursor_data.json | jq '.conversation_data'
  ```
- Consider backing up your Cursor database regularly to preserve your conversations 