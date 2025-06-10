import os
import re
import argparse
import logging
import openai
from openai import OpenAI
from typing import Dict, Union
from memory.logger import log_edit

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("autocoder.log"),
        logging.StreamHandler()
    ]
)

VALID_EXTENSIONS = (".py", ".html", ".css", ".js", ".ts", ".jsx", ".tsx", ".md", ".txt")
MAX_FILE_SIZE = 100000  # 100KB

def is_valid_file(filepath: str) -> bool:
    """Check if file should be processed"""
    if filepath.startswith((".", "__")):
        return False
    if filepath.endswith("~"):
        return False
    if not filepath.endswith(VALID_EXTENSIONS):
        return False
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        logging.warning(f"Skipping large file: {filepath}")
        return False
    return True

def read_code(path: str) -> Dict[str, str]:
    """
    Read a single file or all valid files from a directory.
    Returns dictionary of {file_path: content}
    """
    files = {}
    
    if os.path.isdir(path):
        for dp, _, filenames in os.walk(path):
            for f in filenames:
                full_path = os.path.join(dp, f)
                if is_valid_file(full_path):
                    try:
                        files[full_path] = read_file(full_path)
                    except Exception as e:
                        logging.error(f"Error reading {full_path}: {str(e)}")
        if not files:
            logging.error(f"❌ No valid files found in directory: {path}")
    elif os.path.isfile(path) and is_valid_file(path):
        files[path] = read_file(path)
    else:
        logging.error(f"❌ Path not found or invalid file: {path}")
        
    return files

def read_file(filepath: str) -> str:
    """Safely read a file and return its content"""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write_code(updates: Dict[str, str]) -> None:
    """Write updated content back to each file with backup"""
    for fname, content in updates.items():
        # Create backup
        backup_path = f"{fname}.bak"
        if os.path.exists(fname) and not os.path.exists(backup_path):
            os.rename(fname, backup_path)
            
        # Write new content
        with open(fname, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"✅ Updated {fname}")

def upgrade_code(
    files: Dict[str, str], 
    upgrade_instruction: str,
    provider: str = "OpenAI",
    model: str = "gpt-4-turbo",
    temperature: float = 0.3
) -> Dict[str, str]:
    """
    Send files and instruction to AI, return updated versions.
    Handles token limits by processing in chunks.
    """
    if not files:
        logging.error("❌ No files to upgrade")
        return {}
        
    if not upgrade_instruction.strip():
        logging.error("❌ Empty upgrade instruction")
        return files

    # Prepare system message
    system_msg = {
        "role": "system", 
        "content": "You are an expert full-stack developer. Apply requested upgrades to the provided code."
    }
    
    # Build messages with files
    messages = [system_msg]
    token_count = 1000  # Start with system message tokens
    
    for fname, content in files.items():
        file_msg = f"File: {fname}\n\n{content}"
        file_tokens = len(file_msg.split())  # Approximate token count
        
        # Check token limit (GPT-4-turbo has 128K context)
        if token_count + file_tokens > 120000:
            logging.warning(f"⚠️ Token limit reached. Processing {len(messages)-1} files.")
            break
            
        messages.append({"role": "user", "content": file_msg})
        token_count += file_tokens
    
    # Add upgrade instruction
    upgrade_msg = {
        "role": "user",
        "content": (
            "Apply these upgrades across all files:\n"
            f"{upgrade_instruction}\n\n"
            "Respond format for each file:\n"
            "File: path/to/file.ext\n"
            "```\n<updated code>\n```\n"
            "Important: Only return updated files."
        )
    }
    messages.append(upgrade_msg)
    
    try:
        if provider == "DeepSeek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            client = openai.OpenAI(api_key=api_key)
            
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=4000
        )
        output = response.choices[0].message.content
        return parse_response(output, files)
    except Exception as e:
        logging.exception(f"❌ Error from {provider} API")
        raise

def parse_response(gpt_output: str, original_files: Dict[str, str]) -> Dict[str, str]:
    """
    Extract new code blocks from GPT output with improved parsing
    """
    result = {}
    pattern = r"File:\s*(.*?)\n```(?:[^\n]*)?\n([\s\S]*?)\n```"
    blocks = re.findall(pattern, gpt_output, re.DOTALL)
    
    if not blocks:
        logging.warning("⚠️ No code blocks found. Trying fallback parsing.")
        # Fallback: Look for FILE: headers
        current_file = None
        current_content = []
        
        for line in gpt_output.split('\n'):
            if line.startswith("File:") or line.startswith("FILE:"):
                if current_file:
                    result[current_file] = '\n'.join(current_content).strip()
                    current_content = []
                current_file = line.split(":", 1)[1].strip()
            elif current_file:
                current_content.append(line)
                
        if current_file and current_content:
            result[current_file] = '\n'.join(current_content).strip()
    else:
        for fname, content in blocks:
            fname = fname.strip()
            result[fname] = content.strip()

    # Add files that weren't modified
    for fname in original_files:
        if fname not in result:
            logging.warning(f"⚠️ No update found for {fname}. Keeping original.")
            result[fname] = original_files[fname]
        else:
            # Log the edit to memory
            log_edit(fname, result[fname])

    return result

def parse_args():
    parser = argparse.ArgumentParser(description="Upgrade code files using AI.")
    parser.add_argument("--path", required=True, help="Path to file or directory")
    parser.add_argument("--upgrade", required=True, help="Upgrade instruction")
    parser.add_argument("--provider", default="OpenAI", help="AI provider (OpenAI or DeepSeek)")
    parser.add_argument("--model", default="gpt-4-turbo", help="Model to use")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if not os.getenv("OPENAI_API_KEY") and args.provider == "OpenAI":
        logging.error("❌ OPENAI_API_KEY environment variable not set.")
        exit(1)
    if not os.getenv("DEEPSEEK_API_KEY") and args.provider == "DeepSeek":
        logging.error("❌ DEEPSEEK_API_KEY environment variable not set.")
        exit(1)

    files = read_code(args.path)
    if not files:
        logging.error("❌ No files to process. Exiting.")
        exit(1)
        
    updated_files = upgrade_code(
        files, 
        args.upgrade,
        provider=args.provider,
        model=args.model
    )
    if updated_files:
        write_code(updated_files)
        logging.info("✅ Upgrade completed successfully")
    else:
        logging.error("❌ Upgrade failed. No changes made.")