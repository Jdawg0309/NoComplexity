import openai, os
from dotenv import load_dotenv
import textwrap

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def break_down(prompt):
    """Break down tasks with enhanced formatting"""
    messages = [
        {
            "role": "system", 
            "content": textwrap.dedent("""
                You are a senior engineer. Break down high-level goals into clear subgoals.
                
                Output format:
                1. [Task 1]
                2. [Task 2]
                3. [Task 3]
                
                Include:
                - Technical steps
                - Required resources
                - Potential challenges
                """)
        },
        {
            "role": "user", 
            "content": f"Break down this task: {prompt}"
        }
    ]
    
    try:
        res = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.4,
            max_tokens=1000
        )
        breakdown = res.choices[0].message.content
        print("\n🔧 Task Breakdown:")
        print(breakdown)
    except openai.APIError as e:
        print(f"❌ OpenAI API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    goal = input("What do you want to build?\n> ")
    if goal.strip():
        break_down(goal)
    else:
        print("❌ Please enter a valid task description")