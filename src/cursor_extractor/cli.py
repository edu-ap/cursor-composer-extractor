"""
Command-line interface for Cursor Composer Extractor.

This module provides the CLI for extracting Cursor Composer data.
"""

import argparse
import os
import sys
from typing import Dict, Any, List, Optional

from .extractor import CursorExtractor
from .parsers import JsonOutputParser, MarkdownOutputParser
from .utils import get_default_db_path


def parse_args():
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Extract and convert Cursor Composer AI conversations"
    )
    
    parser.add_argument(
        "--db-path",
        help="Path to the Cursor SQLite database",
    )
    
    parser.add_argument(
        "--output-dir",
        help="Directory to save output files",
        default="conversations",
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    
    parser.add_argument(
        "--all-data",
        action="store_true",
        help="Extract all potentially relevant data, not just conversations",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Check if the database exists
    db_path = args.db_path or get_default_db_path()
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at: {db_path}")
        print("Please specify the correct path with --db-path")
        sys.exit(1)
    
    # Create output directory
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Extract data
    with CursorExtractor(db_path=db_path, debug=args.debug) as extractor:
        if args.all_data:
            print("Extracting all potentially relevant data...")
            data = extractor.extract_all_data()
            print(f"Found {len(data)} relevant entries")
            
            # Save data according to format
            if args.format in ["json", "both"]:
                json_dir = os.path.join(output_dir, "json")
                if not os.path.exists(json_dir):
                    os.makedirs(json_dir)
                
                print(f"Saving entries as JSON to {json_dir}/...")
                for i, entry in enumerate(data, 1):
                    JsonOutputParser.save_entry(entry, json_dir)
                    if i % 10 == 0 or i == len(data):
                        print(f"Saved {i}/{len(data)} entries as JSON")
            
            if args.format in ["markdown", "both"]:
                md_dir = os.path.join(output_dir, "markdown")
                if not os.path.exists(md_dir):
                    os.makedirs(md_dir)
                
                print(f"Saving entries as Markdown to {md_dir}/...")
                for i, entry in enumerate(data, 1):
                    parsed_entry = MarkdownOutputParser.parse_entry(entry)
                    MarkdownOutputParser.save_entry(parsed_entry, md_dir)
                    if i % 10 == 0 or i == len(data):
                        print(f"Saved {i}/{len(data)} entries as Markdown")
        else:
            print("Extracting conversations...")
            conversations = extractor.extract_conversations()
            print(f"Found {len(conversations)} conversations")
            
            if not conversations:
                print("No conversations were found in the database.")
                print("Try running with --all-data to extract all potentially relevant data.")
                sys.exit(0)
            
            # Save conversations according to format
            if args.format in ["json", "both"]:
                json_dir = os.path.join(output_dir, "json")
                if not os.path.exists(json_dir):
                    os.makedirs(json_dir)
                
                print(f"Saving conversations as JSON to {json_dir}/...")
                for i, conversation in enumerate(conversations, 1):
                    JsonOutputParser.save_entry({"conversation": conversation}, json_dir)
                    print(f"Saved conversation {i}/{len(conversations)} as JSON")
                
                # Also save all conversations to a single file
                all_file = os.path.join(output_dir, "all_conversations.json")
                JsonOutputParser.save_all(conversations, all_file)
                print(f"Saved all conversations to {all_file}")
            
            if args.format in ["markdown", "both"]:
                md_dir = os.path.join(output_dir, "markdown")
                if not os.path.exists(md_dir):
                    os.makedirs(md_dir)
                
                print(f"Saving conversations as Markdown to {md_dir}/...")
                for i, conversation in enumerate(conversations, 1):
                    parsed = MarkdownOutputParser.parse_conversation(conversation)
                    MarkdownOutputParser.save_conversation(parsed, md_dir)
                    print(f"Saved conversation {i}/{len(conversations)} as Markdown")
        
        print("\nExtraction complete!")
        print(f"Output files are available in the '{output_dir}' directory.")


if __name__ == "__main__":
    main() 