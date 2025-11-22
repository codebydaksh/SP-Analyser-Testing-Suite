"""
Remove all emojis from Python and Markdown files
"""
import re
from pathlib import Path

# Emoji pattern - matches most common emoji ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\u2600-\u26FF"          # Miscellaneous Symbols
    "\u2700-\u27BF"          # Dingbats
    "]+",
    flags=re.UNICODE
)

def remove_emojis_from_file(filepath):
    """Remove emojis from a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        cleaned_content = EMOJI_PATTERN.sub('', content)
        
        if cleaned_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Remove emojis from all Python and Markdown files"""
    root = Path('.')
    patterns = ['**/*.py', '**/*.md']
    
    modified_files = []
    
    for pattern in patterns:
        for filepath in root.glob(pattern):
            # Skip __pycache__, .git, venv directories
            if any(part in filepath.parts for part in ['__pycache__', '.git', 'venv', 'node_modules']):
                continue
            
            if remove_emojis_from_file(filepath):
                modified_files.append(str(filepath))
                print(f"Cleaned: {filepath}")
    
    print(f"\nTotal files cleaned: {len(modified_files)}")
    return modified_files

if __name__ == '__main__':
    main()
