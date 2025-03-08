#!/bin/bash

# Output markdown file
OUTPUT_FILE="cursor_logs_report.md"

# Possible log directories to check
possible_dirs=(
    "$HOME/.config/Cursor/logs/composer"
    "$HOME/.cursor/logs/composer"
    "$HOME/AppData/Roaming/Cursor/logs/composer"
    "$HOME/Library/Application Support/Cursor/logs/composer"
    "$HOME/.config/Cursor/conversations"
    "$HOME/.config/Cursor/logs"
    "$HOME/Documents/Obsidian Vault/8.week-logs"
)

# Initialize markdown file header
cat > "$OUTPUT_FILE" << EOL
# Cursor Composer Logs Report

Generated on: $(date)

## System Information
- OS: $(uname -a)
- Home Directory: $HOME

## Search Results
EOL

# Flag to track if we found any logs
found_logs=false

# Search for composer logs in common locations
echo "Searching for Cursor Composer logs..." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

for dir in "${possible_dirs[@]}"; do
    echo "### Checking: \`$dir\`" >> "$OUTPUT_FILE"
    
    if [ -d "$dir" ]; then
        echo "✅ Directory exists" >> "$OUTPUT_FILE"
        
        # Count files and directories
        file_count=$(find "$dir" -type f | wc -l)
        dir_count=$(find "$dir" -type d | wc -l)
        total_size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        
        echo "" >> "$OUTPUT_FILE"
        echo "- Contains $file_count files" >> "$OUTPUT_FILE"
        echo "- Contains $dir_count directories" >> "$OUTPUT_FILE"
        echo "- Total size: $total_size" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        # Check if there are actual log files
        log_files=$(find "$dir" -type f -name "*.json" -o -name "*.log" 2>/dev/null | wc -l)
        if [ "$log_files" -gt 0 ]; then
            found_logs=true
            
            # Create table for this directory
            echo "#### Files in \`$dir\`:" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            echo "| Type | Name | Size | Extension | Last Modified |" >> "$OUTPUT_FILE"
            echo "|------|------|------|-----------|---------------|" >> "$OUTPUT_FILE"
            
            # Process each item in the directory
            find "$dir" -type f -o -type d 2>/dev/null | head -50 | while read -r item; do
                # Skip the directory itself
                if [ "$item" = "$dir" ]; then
                    continue
                fi
                
                # Get item type (file or directory)
                if [ -f "$item" ]; then
                    item_type="File"
                    filename=$(basename -- "$item")
                    extension="${filename##*.}"
                    if [ "$extension" = "$filename" ]; then
                        extension="none"
                    fi
                    size=$(stat -c %s "$item" 2>/dev/null)
                    
                    # Format size
                    if [ $size -ge 1048576 ]; then
                        formatted_size="$(awk "BEGIN {printf \"%.2f\", $size/1048576}") MB"
                    elif [ $size -ge 1024 ]; then
                        formatted_size="$(awk "BEGIN {printf \"%.2f\", $size/1024}") KB"
                    else
                        formatted_size="$size bytes"
                    fi
                else
                    item_type="Directory"
                    extension="N/A"
                    formatted_size="N/A"
                fi
                
                # Get item name (relative to log directory)
                relative_path="${item#$dir/}"
                if [ "$relative_path" = "$item" ]; then
                    relative_path=$(basename "$item")
                fi
                
                # Get last modified date
                last_modified=$(stat -c "%y" "$item" 2>/dev/null | cut -d. -f1)
                
                # Append to markdown file
                echo "| $item_type | \`$relative_path\` | $formatted_size | $extension | $last_modified |" >> "$OUTPUT_FILE"
            done
            
            # Add note if there are more files
            if [ "$file_count" -gt 50 ]; then
                echo "" >> "$OUTPUT_FILE"
                echo "> Note: Only showing first 50 items. Total items: $((file_count + dir_count - 1))" >> "$OUTPUT_FILE"
            fi
        else
            echo "❌ No log files found in this directory" >> "$OUTPUT_FILE"
        fi
    else
        echo "❌ Directory does not exist" >> "$OUTPUT_FILE"
    fi
    
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
done

# Check current directory for logs as a fallback
current_dir=$(pwd)
echo "### Checking current directory: \`$current_dir\`" >> "$OUTPUT_FILE"

json_files=$(find "$current_dir" -maxdepth 1 -name "*.json" | wc -l)
if [ "$json_files" -gt 0 ]; then
    echo "✅ Found $json_files JSON files in current directory" >> "$OUTPUT_FILE"
    found_logs=true
    
    # List files in current directory
    echo "" >> "$OUTPUT_FILE"
    echo "#### Files in current directory:" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "| Filename | Size | Last Modified |" >> "$OUTPUT_FILE"
    echo "|----------|------|---------------|" >> "$OUTPUT_FILE"
    
    find "$current_dir" -maxdepth 1 -name "*.json" -o -name "*.log" | while read -r file; do
        filename=$(basename "$file")
        size=$(stat -c %s "$file" 2>/dev/null)
        
        # Format size
        if [ $size -ge 1048576 ]; then
            formatted_size="$(awk "BEGIN {printf \"%.2f\", $size/1048576}") MB"
        elif [ $size -ge 1024 ]; then
            formatted_size="$(awk "BEGIN {printf \"%.2f\", $size/1024}") KB"
        else
            formatted_size="$size bytes"
        fi
        
        last_modified=$(stat -c "%y" "$file" 2>/dev/null | cut -d. -f1)
        echo "| \`$filename\` | $formatted_size | $last_modified |" >> "$OUTPUT_FILE"
    done
else
    echo "❌ No JSON or log files found in current directory" >> "$OUTPUT_FILE"
fi

# Final summary
echo "" >> "$OUTPUT_FILE"
echo "## Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ "$found_logs" = true ]; then
    echo "✅ Cursor logs were found on this system." >> "$OUTPUT_FILE"
else
    echo "❌ No Cursor logs were found in any of the expected locations." >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "Possible reasons:" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "- Cursor may not be installed on this system" >> "$OUTPUT_FILE"
    echo "- Cursor Composer hasn't been used yet" >> "$OUTPUT_FILE"
    echo "- Logs are stored in a non-standard location" >> "$OUTPUT_FILE"
    echo "- Log files may have been deleted" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "## Notes" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- This report was generated on $(date)" >> "$OUTPUT_FILE"
echo "- The script searched in common locations for Cursor logs" >> "$OUTPUT_FILE"
echo "- File sizes are shown in bytes, KB, or MB as appropriate" >> "$OUTPUT_FILE"
echo "- For privacy reasons, you may want to review log contents before sharing" >> "$OUTPUT_FILE"

echo "Cursor logs report has been generated as $OUTPUT_FILE" 