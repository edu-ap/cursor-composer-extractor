#!/usr/bin/env python3
"""
Example script that extracts and analyzes Cursor Composer conversations.
This shows how to use the library for custom analysis.
"""

import os
import sys
import json
from pathlib import Path
from collections import Counter
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cursor_extractor.extractor import CursorExtractor
from src.cursor_extractor.utils import try_extract_text


def count_messages(conversation):
    """Count user and assistant messages in a conversation."""
    user_messages = 0
    assistant_messages = 0
    
    if 'conversation' in conversation['data'] and isinstance(conversation['data']['conversation'], list):
        for msg in conversation['data']['conversation']:
            if msg.get('type') == 1:  # User message
                user_messages += 1
            elif msg.get('type') == 2:  # Assistant message
                assistant_messages += 1
    
    return user_messages, assistant_messages


def analyze_topics(conversations):
    """Analyze conversation topics based on user queries."""
    topics = []
    
    for conversation in conversations:
        # Get the first user message as the topic
        data = conversation['data']
        
        # Try to extract text from richText
        user_query = ""
        if 'richText' in data:
            user_query = try_extract_text(data['richText'])
        elif 'text' in data:
            user_query = data['text']
        
        # If we found text, add the first line as a topic
        if user_query:
            first_line = user_query.split('\n')[0]
            if first_line:  # Only add non-empty topics
                topics.append(first_line[:50])  # Truncate long topics
    
    # Count topic frequency
    topic_counter = Counter(topics)
    return topic_counter.most_common(10)  # Return top 10 topics


def main():
    """Extract and analyze conversations."""
    # Extract conversations
    with CursorExtractor(debug=True) as extractor:
        print("Extracting conversations...")
        conversations = extractor.extract_conversations()
        print(f"Found {len(conversations)} conversations")
        
        if not conversations:
            print("No conversations found.")
            return
        
        # Analyze conversations
        print("\nAnalyzing conversations...")
        
        # Count total messages
        total_user_messages = 0
        total_assistant_messages = 0
        
        for conversation in conversations:
            user_msgs, assistant_msgs = count_messages(conversation)
            total_user_messages += user_msgs
            total_assistant_messages += assistant_msgs
        
        # Get top topics
        top_topics = analyze_topics(conversations)
        
        # Create report directory
        report_dir = "conversation_analysis"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        # Generate report
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "total_user_messages": total_user_messages,
            "total_assistant_messages": total_assistant_messages,
            "average_user_messages_per_conversation": round(total_user_messages / len(conversations), 2) if conversations else 0,
            "average_assistant_messages_per_conversation": round(total_assistant_messages / len(conversations), 2) if conversations else 0,
            "top_topics": [{"topic": topic, "count": count} for topic, count in top_topics]
        }
        
        # Save report as JSON
        report_file = os.path.join(report_dir, "conversation_analysis.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        # Save report as Markdown
        markdown_report = f"""# Cursor Composer Conversation Analysis

Generated at: {report['generated_at']}

## Summary

- **Total Conversations**: {report['total_conversations']}
- **Total User Messages**: {report['total_user_messages']}
- **Total Assistant Messages**: {report['total_assistant_messages']}
- **Average User Messages per Conversation**: {report['average_user_messages_per_conversation']}
- **Average Assistant Messages per Conversation**: {report['average_assistant_messages_per_conversation']}

## Top Topics

| Topic | Count |
|-------|-------|
{chr(10).join([f"| {topic['topic']} | {topic['count']} |" for topic in report['top_topics']])}

"""
        
        markdown_file = os.path.join(report_dir, "conversation_analysis.md")
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"\nAnalysis complete!")
        print(f"Reports saved to:")
        print(f"- JSON: {report_file}")
        print(f"- Markdown: {markdown_file}")


if __name__ == "__main__":
    main() 