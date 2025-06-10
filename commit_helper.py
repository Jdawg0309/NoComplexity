import subprocess, openai, os
from dotenv import load_dotenv
import re

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_git_diff():
    """Get staged git diff with error handling"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"], 
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command error: {e.stderr}")
        return ""
    except FileNotFoundError:
        print("❌ Git not found. Make sure Git is installed.")
        return ""

def generate_commit_message(diff):
    """Generate commit message with GPT with enhanced prompt"""
    if not diff.strip():
        return "No changes detected"

    prompt = f"""
    Write a clear, concise git commit message following these rules:
    1. Start with an imperative verb (Add, Fix, Update, Refactor, etc.)
    2. Limit to 50 characters
    3. Use conventional commit format: <type>(<scope>): <description>
    
    Changes:
    {diff}
    """
    
    try:
        res = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        message = res.choices[0].message.content.strip()
        # Clean up message
        message = re.sub(r'^"|"$', '', message)  # Remove quotes
        return message[:72]  # Git commit message line length limit
    except openai.APIError as e:
        print(f"❌ OpenAI API error: {e}")
        return "Update code changes"

if __name__ == "__main__":
    diff = get_git_diff()
    if not diff.strip():
        print("⚠️ No staged changes detected.")
    else:
        print("\n📋 Changes detected:")
        print(diff[:500] + ("..." if len(diff) > 500 else ""))
        msg = generate_commit_message(diff)
        print(f"\n🔧 Suggested commit message:\n\n{msg}")