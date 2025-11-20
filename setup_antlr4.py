"""
ANTLR4 T-SQL Parser Setup Script
Downloads grammar files and generates Python parser
"""
import urllib.request
import os
import subprocess
import sys

GRAMMAR_BASE_URL = "https://raw.githubusercontent.com/antlr/grammars-v4/master/sql/tsql/"
GRAMMAR_FILES = [
    "TSqlLexer.g4",
    "TSqlParser.g4"
]

def download_grammar_files():
    """Download T-SQL grammar files from ANTLR grammars-v4 repository."""
    print("Downloading T-SQL grammar files...")
    
    os.makedirs("grammar", exist_ok=True)
    
    for filename in GRAMMAR_FILES:
        url = GRAMMAR_BASE_URL + filename
        output_path = os.path.join("grammar", filename)
        
        print(f"  Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, output_path)
            print(f"  Downloaded: {output_path}")
        except Exception as e:
            print(f"  ERROR downloading {filename}: {e}")
            return False
    
    print("Grammar files downloaded successfully.\n")
    return True

def install_antlr4_tools():
    """Install ANTLR4 tools."""
    print("Installing ANTLR4 tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "antlr4-tools"])
        print("ANTLR4 tools installed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR installing ANTLR4 tools: {e}")
        return False

def generate_parser():
    """Generate Python parser from grammar files."""
    print("Generating Python parser...")
    
    os.makedirs("src/parser/generated", exist_ok=True)
    
    try:
        # Try using antlr4 command directly
        cmd = [
            "antlr4",
            "-Dlanguage=Python3",
            "-o", "src/parser/generated",
            "-visitor",
            "grammar/TSqlLexer.g4",
            "grammar/TSqlParser.g4"
        ]
        
        subprocess.check_call(cmd)
        print("Parser generated successfully.\n")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"ERROR generating parser: {e}")
        print("\nAlternative: You may need to manually run:")
        print("  java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -o src/parser/generated -visitor grammar/*.g4")
        return False

def create_init_files():
    """Create __init__.py files in generated directory."""
    print("Creating __init__.py files...")
    
    init_path = "src/parser/generated/__init__.py"
    os.makedirs(os.path.dirname(init_path), exist_ok=True)
    
    with open(init_path, 'w') as f:
        f.write("# Generated ANTLR4 parser files\n")
    
    print(f"Created: {init_path}\n")

def main():
    """Main setup function."""
    print("=" * 60)
    print("ANTLR4 T-SQL Parser Setup")
    print("=" * 60 + "\n")
    
    # Step 1: Download grammar files
    if not download_grammar_files():
        print("\nSetup failed at grammar download step.")
        return False
    
    # Step 2: Install ANTLR4 tools
    if not install_antlr4_tools():
        print("\nSetup failed at ANTLR4 tools installation step.")
        print("You may need to install manually or use Java-based ANTLR4.")
        return False
    
    # Step 3: Generate parser
    if not generate_parser():
        print("\nSetup failed at parser generation step.")
        print("Please check ANTLR4 installation.")
        return False
    
    # Step 4: Create init files
    create_init_files()
    
    print("=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
