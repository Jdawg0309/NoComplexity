import openai, os
from dotenv import load_dotenv
import re
import datetime
import sqlite3
import os

from ..utils.file_utils import read_file
from ..memory.database import initialize_database
import openai
import os
from dotenv import load_dotenv
import re
import datetime
import sqlite3

from utils.file_utils import read_file
from memory.database import initialize_database

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_response(response):
    """Parse GPT response into files dictionary"""
    files = {}
    current_file = None
    content_lines = []
    
    for line in response.split('\n'):
        if line.startswith("FILE:"):
            if current_file:
                files[current_file] = '\n'.join(content_lines).strip()
                content_lines = []
            current_file = line.split("FILE:", 1)[1].strip()
        elif current_file:
            content_lines.append(line)
    
    if current_file and content_lines:
        files[current_file] = '\n'.join(content_lines).strip()
    
    return files

def generate_structure(prompt):
    """Generate project structure with enhanced prompt"""
    if not prompt.strip():
        print("❌ Please provide a project description")
        return

    messages = [
        {
            "role": "system",
            "content": """You are an expert software engineer. Break projects into files with full contents.
            
            Rules:
            1. Only output FILE: and content blocks
            2. Use realistic file paths
            3. Include essential implementation
            4. Use comments for clarity
            5. Format code properly"""
        },
        {
            "role": "user",
            "content": f"Project description:\n\n{prompt}"
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.4,
            max_tokens=3000
        )

        output = response.choices[0].message.content.strip()
        files = parse_response(output)
        
        if not files:
            print("❌ Failed to parse file structure")
            return
            
        os.makedirs("multi_output", exist_ok=True)
        for path, content in files.items():
            file_path = os.path.join("multi_output", path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
            print(f"✅ Created: {file_path}")
            
        print("\n🎉 Project structure generated successfully!")
        
    except openai.APIError as e:
        print(f"❌ OpenAI API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    spec = input("Describe the app structure you want:\n> ")
    generate_structure(spec)