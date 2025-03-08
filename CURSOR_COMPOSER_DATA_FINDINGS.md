# Cursor Composer Data Analysis Findings

## Overview

This report summarizes the findings from analyzing the Cursor Composer conversation data stored in the SQLite database at `~/.config/Cursor/User/globalStorage/state.vscdb`.

## Database Structure

The Cursor application uses an SQLite database to store various types of application data, including Cursor Composer conversations. The database contains:

- **2 Tables** were found in the database
- **Items Table**: A key-value storage table containing application state data
- The table contains over **600 Composer-related entries**

## Conversation Data Structure

Each Cursor Composer conversation is stored with the following structure:

```json
{
  "composerId": "unique-uuid-for-conversation",
  "richText": "serialized rich text content of user's question",
  "hasLoaded": true,
  "text": "plain text version of question",
  "conversation": [
    {
      "type": 1,  // user message
      "bubbleId": "unique-id",
      "content": {
        // message content
      }
    },
    {
      "type": 2,  // AI response
      "bubbleId": "unique-id",
      "content": {
        // response content
      }
    }
    // additional messages
  ],
  "status": "completed|none",
  "context": {
    // context information like file paths, active files, etc.
  }
}
```

## Key Findings

1. **Conversation Storage Location**: 
   - Cursor Composer conversations are definitively stored in the SQLite database at `~/.config/Cursor/User/globalStorage/state.vscdb`
   - They are NOT stored in plain text or JSON files in the log directories, contrary to the documentation

2. **Data Format**:
   - Each conversation has a unique UUID identifier
   - Conversations are stored with rich text formatting
   - Many conversation entries are empty/initialized but unused
   - Some conversations contain full message history including both user queries and AI responses

3. **Data Volume**:
   - Over 600 conversation entries were found
   - Many appear to be template entries without actual conversation content
   - Conversation IDs follow a UUID format (e.g., `cbe8a9e3-8f82-4b42-867a-18241155590f`)

4. **Context Information**:
   - Conversations include context about files open in the editor
   - Some contain information about the workspace being used
   - Context appears to help the AI generate responses relevant to the code

## Accessing Your Conversations

To access your full conversation history:

1. **Using the Extract Script**:
   - The provided Python script can extract all conversations
   - Run with `--output` to save to a JSON file: `./extract_cursor_conversations.py --output conversations.json`

2. **Manual Database Access**:
   - Use SQLite tools to query the database directly:
   ```bash
   sqlite3 ~/.config/Cursor/User/globalStorage/state.vscdb
   SELECT * FROM items WHERE key LIKE 'composerData:%' LIMIT 10;
   ```

3. **Backing Up Conversations**:
   - Regularly backup the `state.vscdb` file to preserve your conversation history
   - Consider exporting important conversations using the script

## Conclusion

The analysis confirms that Cursor Composer conversations are stored in a SQLite database rather than in log files. This database contains a comprehensive record of your interactions with the AI assistant, including both your queries and the AI's responses, along with contextual information about your workspace.

These findings differ from the information provided in the original documentation, which suggested that logs would be stored in operating system-specific directories like `~/.config/Cursor/logs/composer` on Linux.

For users who wish to access or back up their Cursor Composer conversation history, interacting with the SQLite database (either directly or through the provided script) is the recommended approach. 