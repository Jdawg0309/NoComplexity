import openai
import os
from dotenv import load_dotenv
from pathlib import Path
import re

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_project_structure(response):
    """Parse GPT response into file structure"""
    files = {}
    current_file = None
    current_content = []
    
    for line in response.split('\n'):
        if line.startswith("FILE:"):
            if current_file:
                files[current_file] = '\n'.join(current_content).strip()
                current_content = []
            current_file = line.split("FILE:")[1].strip()
        elif current_file:
            current_content.append(line)
    
    if current_file and current_content:
        files[current_file] = '\n'.join(current_content).strip()
    
    return files

def generate_project(prompt):
    """Generate project with enhanced prompt and parsing"""
    if not prompt.strip():
        print("❌ Please provide a project description")
        return

    system_prompt = """
    You are an expert full-stack developer. Create a project structure and key file content based on the user's spec.
    
    Output format:
    FILE: path/to/filename.ext
    [File content here]
    
    FILE: next/file/path.js
    [File content here]
    
    Important:
    1. Only include essential files
    2. Use realistic code patterns
    3. Include brief comments
    4. Use triple backticks for code blocks
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Project spec:\n\n{prompt}"}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        project = response.choices[0].message.content
        files = parse_project_structure(project)
        
        if not files:
            print("❌ Failed to parse project structure")
            return
            
        output_dir = Path("generated_repo")
        output_dir.mkdir(exist_ok=True)
        
        for path, content in files.items():
            file_path = output_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            print(f"✅ Created: {file_path}")
            
        print(f"\n🎉 Project generated in {output_dir}/")
        
    except openai.APIError as e:
        print(f"❌ OpenAI API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    user_prompt = input("Describe your app (e.g. Flask + SQLite todo app): ")
    generate_project(user_prompt)