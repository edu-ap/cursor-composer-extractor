"""
Parsers for Cursor Composer data.

This module contains parsers for different data formats found in Cursor's database.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from .utils import (
    clean_text_for_markdown,
    convert_rich_text_to_markdown,
    extract_conversation_messages,
    try_extract_text,
    safe_filename
)


class JsonOutputParser:
    """Parser for JSON output."""
    
    @staticmethod
    def parse_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an entry for JSON output.
        
        Args:
            entry: Entry dictionary.
            
        Returns:
            Parsed entry.
        """
        return entry
    
    @staticmethod
    def save_entry(entry: Dict[str, Any], output_dir: str) -> str:
        """Save an entry as a JSON file.
        
        Args:
            entry: Entry dictionary.
            output_dir: Output directory.
            
        Returns:
            Path to the saved file.
        """
        # Generate filename
        safe_key = safe_filename(entry['key'])
        filename = f"{entry['table']}_{safe_key}.json"
        file_path = os.path.join(output_dir, filename)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entry, f, indent=2)
        
        return file_path
    
    @staticmethod
    def save_all(entries: List[Dict[str, Any]], output_file: str) -> str:
        """Save all entries to a single JSON file.
        
        Args:
            entries: List of entry dictionaries.
            output_file: Output file path.
            
        Returns:
            Path to the saved file.
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2)
        
        return output_file


class MarkdownOutputParser:
    """Parser for Markdown output."""
    
    @staticmethod
    def parse_conversation(conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a conversation for Markdown output.
        
        Args:
            conversation: Conversation dictionary.
            
        Returns:
            Parsed conversation.
        """
        conv_data = conversation['data']
        conv_id = conversation['id']
        
        # Try to determine a title
        title = "Cursor Composer Conversation"
        user_query = ""
        
        # Try to extract the first user message as title
        if 'richText' in conv_data:
            user_query = convert_rich_text_to_markdown(conv_data['richText'])
        elif 'text' in conv_data:
            user_query = conv_data['text']
        
        if user_query:
            # Take first line or first few words for title
            title_text = user_query.split('\n')[0][:50]
            if title_text:
                title = title_text + ("..." if len(title_text) >= 50 else "")
        
        # Extract conversation messages
        conversation_text = ""
        if 'conversation' in conv_data and isinstance(conv_data['conversation'], list):
            conversation_text = extract_conversation_messages(conv_data['conversation'])
        
        # Extract context info
        context_info = None
        if 'context' in conv_data and conv_data['context']:
            context_info = conv_data['context']
        
        return {
            'id': conv_id,
            'title': title,
            'conversation_text': conversation_text,
            'context_info': context_info
        }
    
    @staticmethod
    def save_conversation(parsed_conversation: Dict[str, Any], output_dir: str) -> str:
        """Save a parsed conversation as a Markdown file.
        
        Args:
            parsed_conversation: Parsed conversation dictionary.
            output_dir: Output directory.
            
        Returns:
            Path to the saved file.
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conv_id = parsed_conversation['id']
        filename = f"{timestamp}_{conv_id[:8]}.md"
        file_path = os.path.join(output_dir, filename)
        
        # Build the markdown content
        markdown_content = f"# {parsed_conversation['title']}\n\n"
        markdown_content += f"**Conversation ID:** {parsed_conversation['id']}\n\n"
        
        # Add the main conversation
        if parsed_conversation['conversation_text']:
            markdown_content += "# Conversation\n\n"
            markdown_content += parsed_conversation['conversation_text']
        
        # Add context info if available
        if parsed_conversation['context_info']:
            markdown_content += "# Context\n\n"
            markdown_content += f"```json\n{json.dumps(parsed_conversation['context_info'], indent=2)}\n```\n\n"
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return file_path
    
    @staticmethod
    def parse_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Parse an entry for Markdown output.
        
        Args:
            entry: Entry dictionary.
            
        Returns:
            Parsed entry.
        """
        # Generate title
        title = entry['key']
        if len(title) > 50:
            title = title[:47] + '...'
        
        content_sections = []
        
        # Process each column
        for col, value in entry['data'].items():
            section = {'title': col}
            
            # Try to convert to readable format
            if isinstance(value, (dict, list)):
                # Try to extract text first
                text = try_extract_text(value)
                if text and len(text) > 5:  # Only include if we got meaningful text
                    section['text'] = text
                
                # Include full JSON structure
                section['json'] = json.dumps(value, indent=2)
            else:
                section['text'] = str(value)
            
            content_sections.append(section)
        
        return {
            'table': entry['table'],
            'key': entry['key'],
            'title': title,
            'sections': content_sections
        }
    
    @staticmethod
    def save_entry(parsed_entry: Dict[str, Any], output_dir: str) -> str:
        """Save a parsed entry as a Markdown file.
        
        Args:
            parsed_entry: Parsed entry dictionary.
            output_dir: Output directory.
            
        Returns:
            Path to the saved file.
        """
        # Generate filename
        safe_key = safe_filename(parsed_entry['key'])
        filename = f"{parsed_entry['table']}_{safe_key}.md"
        file_path = os.path.join(output_dir, filename)
        
        # Build markdown content
        markdown_content = f"# {parsed_entry['title']}\n\n"
        markdown_content += f"**Table:** {parsed_entry['table']}\n\n"
        markdown_content += f"**Key:** {parsed_entry['key']}\n\n"
        
        # Add each section
        for section in parsed_entry['sections']:
            markdown_content += f"## {section['title']}\n\n"
            
            if 'text' in section:
                markdown_content += f"{section['text']}\n\n"
            
            if 'json' in section:
                markdown_content += f"```json\n{section['json']}\n```\n\n"
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return file_path 