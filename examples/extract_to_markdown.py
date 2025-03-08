#!/usr/bin/env python3
"""
Example script that extracts Cursor Composer conversations and saves them as Markdown files.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cursor_extractor.extractor import CursorExtractor
from src.cursor_extractor.parsers import MarkdownOutputParser


def main():
    """Extract conversations and save them as Markdown files."""
    # Create output directory
    output_dir = "example_conversations"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Extract conversations
    with CursorExtractor(debug=True) as extractor:
        print("Extracting conversations...")
        conversations = extractor.extract_conversations()
        print(f"Found {len(conversations)} conversations")
        
        if not conversations:
            print("No conversations found.")
            return
        
        # Save conversations as Markdown
        print(f"Saving conversations as Markdown to {output_dir}/...")
        for i, conversation in enumerate(conversations, 1):
            parsed = MarkdownOutputParser.parse_conversation(conversation)
            file_path = MarkdownOutputParser.save_conversation(parsed, output_dir)
            print(f"Saved conversation {i}/{len(conversations)} to {file_path}")
    
    print("\nExtraction complete!")
    print(f"Output files are available in the '{output_dir}' directory.")


if __name__ == "__main__":
    main() 