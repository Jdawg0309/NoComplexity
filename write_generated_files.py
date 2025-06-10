import os
from pathlib import Path
import re

def parse_generated_content(content):
    """Parse generated content with improved error handling"""
    blocks = []
    current_file = None
    current_content = []
    
    # Try different delimiters
    for line in content.split('\n'):
        if line.startswith("FILE:") or line.startswith("File:") or line.startswith("### "):
            if current_file:
                blocks.append((current_file, "\n".join(current_content).strip()))
                current_content = []
            current_file = re.split(r"FILE:|File:|###", line, 1)[-1].strip()
        elif current_file:
            current_content.append(line)
    
    if current_file and current_content:
        blocks.append((current_file, "\n".join(current_content).strip()))
    
    return blocks

def main():
    input_path = "multi_output/generated.txt"
    
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        blocks = parse_generated_content(content)
        
        if not blocks:
            print("⚠️ No file blocks found. Trying alternative parsing.")
            # Fallback: Split by triple backticks
            blocks = re.findall(r"```.*?\n(.*?)```", content, re.DOTALL)
            if blocks:
                print(f"⚠️ Found {len(blocks)} code blocks without filenames")
                # Create numbered files
                for i, code_block in enumerate(blocks):
                    filepath = f"generated_{i+1}.txt"
                    Path(filepath).write_text(code_block.strip(), encoding="utf-8")
                    print(f"✅ Created: {filepath}")
                return
            else:
                print("❌ No valid content found. Writing entire file.")
                with open("full_output.txt", "w") as out_f:
                    out_f.write(content)
                print("✅ Created: full_output.txt")
                return
                
        # Process parsed blocks
        for filepath, code in blocks:
            try:
                path = Path(filepath)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(code, encoding="utf-8")
                print(f"✅ Created: {filepath}")
            except Exception as e:
                print(f"⚠️ Failed to write {filepath}: {str(e)}")
                
        print(f"\n🎉 Successfully created {len(blocks)} files")
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")

if __name__ == "__main__":
    main()