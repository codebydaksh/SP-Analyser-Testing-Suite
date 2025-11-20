"""
Alternative ANTLR4 Setup - Manual Parser Generation

The antlr4 command-line tool requires Java. Follow these steps:

1. Download ANTLR4 JAR:
   https://www.antlr.org/download/antlr-4.13.1-complete.jar

2. Generate Python parser:
   java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -o src/parser/generated -visitor grammar/TSqlLexer.g4 grammar/TSqlParser.g4

3. Or use this Python script to download and run ANTLR4:
"""
import urllib.request
import subprocess
import os
import sys

def setup_antlr4_jar():
    """Download ANTLR4 JAR and generate parser."""
    jar_url = "https://www.antlr.org/download/antlr-4.13.1-complete.jar"
    jar_path = "antlr-4.13.1-complete.jar"
    
    # Download JAR if not exists
    if not os.path.exists(jar_path):
        print(f"Downloading ANTLR4 JAR from {jar_url}...")
        urllib.request.urlretrieve(jar_url, jar_path)
        print(f"Downloaded: {jar_path}")
    
    # Generate parser
    print("\nGenerating Python parser...")
    os.makedirs("src/parser/generated", exist_ok=True)
    
    cmd = [
        "java", "-jar", jar_path,
        "-Dlanguage=Python3",
        "-o", "src/parser/generated",
        "-visitor",
        "grammar/TSqlLexer.g4",
        "grammar/TSqlParser.g4"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("Parser generated successfully!")
        
        # Create __init__.py
        with open("src/parser/generated/__init__.py", 'w') as f:
            f.write("# Generated ANTLR4 parser\n")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Java is installed:")
        print("  - Download from: https://www.oracle.com/java/technologies/downloads/")
        print("  - Or use: winget install Oracle.JDK.21")
        return False

if __name__ == "__main__":
    success = setup_antlr4_jar()
    sys.exit(0 if success else 1)
