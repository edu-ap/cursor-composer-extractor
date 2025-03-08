"""
Utilities for the Cursor Composer Extractor.

This module contains helper functions used by the extractor.
"""

import os
import platform
import json
import re
from typing import Dict, Any, Optional, List
import html


def get_default_db_path() -> str:
    """Get the default path to the Cursor SQLite database.
    
    Returns:
        Path to the Cursor database.
    """
    system = platform.system()
    home_dir = os.path.expanduser("~")
    
    if system == "Windows":
        return os.path.join(os.getenv("APPDATA", ""), "Cursor", "User", "globalStorage", "state.vscdb")
    elif system == "Darwin":  # macOS
        return os.path.join(
            home_dir, "Library", "Application Support", "Cursor", "User", "globalStorage", "state.vscdb"
        )
    else:  # Linux and others
        return os.path.join(home_dir, ".config", "Cursor", "User", "globalStorage", "state.vscdb")


def clean_text_for_markdown(text: str) -> str:
    """Clean and format text for Markdown.
    
    Args:
        text: Text to clean.
        
    Returns:
        Cleaned text.
    """
    if not text:
        return ""
    
    # Handle HTML entities
    text = html.unescape(text)
    
    # Remove control characters
    text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')
    
    # Handle code blocks
    text = re.sub(r'```(\w+)\n', r'```\1\n', text)
    
    return text


def try_extract_text(data: Any) -> str:
    """Try to extract human-readable text from various data structures.
    
    Args:
        data: Data to extract text from.
        
    Returns:
        Extracted text.
    """
    if isinstance(data, str):
        return data
    
    if isinstance(data, dict):
        # Check for common text fields
        for key in ['text', 'content', 'message', 'value', 'richText']:
            if key in data:
                if isinstance(data[key], str):
                    return data[key]
                else:
                    return try_extract_text(data[key])
        
        # Check for conversation array
        if 'conversation' in data and isinstance(data['conversation'], list):
            text = ""
            for item in data['conversation']:
                if isinstance(item, dict):
                    item_text = try_extract_text(item)
                    if item_text:
                        text += item_text + "\n\n"
            return text.strip()
        
        # Look for nested structure with text
        for key, value in data.items():
            if key in ['root', 'children', 'messages', 'content']:
                text = try_extract_text(value)
                if text:
                    return text
    
    if isinstance(data, list):
        text = ""
        for item in data:
            item_text = try_extract_text(item)
            if item_text:
                text += item_text + "\n\n"
        return text.strip()
    
    # Fallback: empty string
    return ""


def convert_rich_text_to_markdown(rich_text: Any) -> str:
    """Convert rich text JSON to Markdown.
    
    Args:
        rich_text: Rich text data.
        
    Returns:
        Markdown text.
    """
    if not rich_text:
        return ""
    
    try:
        # Parse rich text if it's a string
        if isinstance(rich_text, str):
            try:
                rich_data = json.loads(rich_text)
            except json.JSONDecodeError:
                return rich_text
        else:
            rich_data = rich_text
        
        # Extract text from the rich text structure
        markdown = ""
        
        # Try to get text from common paths
        if isinstance(rich_data, dict):
            if 'root' in rich_data:
                root = rich_data['root']
                if 'children' in root and isinstance(root['children'], list):
                    # Recursively extract text from children
                    for child in root['children']:
                        if isinstance(child, dict) and 'children' in child:
                            for text_node in child.get('children', []):
                                if isinstance(text_node, dict):
                                    if 'text' in text_node:
                                        markdown += text_node['text'] + "\n"
                                    elif 'detail' in text_node:
                                        # This might be another format type
                                        pass
        
        return clean_text_for_markdown(markdown.strip())
    except Exception:
        # If anything goes wrong, return empty string
        return ""


def extract_conversation_messages(conversation: List[Dict[str, Any]]) -> str:
    """Extract a readable conversation from message objects.
    
    Args:
        conversation: List of message objects.
        
    Returns:
        Conversation text in Markdown format.
    """
    if not isinstance(conversation, list):
        return ""
    
    conversation_text = ""
    
    for msg in conversation:
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
                user_text = try_extract_text(content)
            
            conversation_text += f"## User\n\n{clean_text_for_markdown(user_text)}\n\n"
        
        elif msg_type == 2:  # AI response
            ai_text = content.get('text', '')
            if not ai_text and 'richText' in content:
                ai_text = convert_rich_text_to_markdown(content['richText'])
            if not ai_text:
                ai_text = try_extract_text(content)
            
            conversation_text += f"## Assistant\n\n{clean_text_for_markdown(ai_text)}\n\n"
    
    return conversation_text


def safe_filename(text: str, max_length: int = 50) -> str:
    """Convert text to a safe filename.
    
    Args:
        text: Text to convert.
        max_length: Maximum length of the filename.
        
    Returns:
        Safe filename.
    """
    # Remove invalid characters
    safe_text = re.sub(r'[^\w\-\.]', '_', text)
    
    # Truncate if necessary
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length]
    
    # Ensure it doesn't start with a dot
    if safe_text.startswith('.'):
        safe_text = '_' + safe_text[1:]
    
    return safe_text 