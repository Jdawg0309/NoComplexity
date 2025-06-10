# backend/app_generator.py

import os
import openai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_project_structure(response: str) -> dict:
    """
    Turn a GPT response of the form:
    
      FILE: path/to/file.ext
      <file contents>
    
    into a { relative_path: content } dict.
    """
    files = {}
    current_file = None
    buffer = []

    for line in response.splitlines():
        if line.startswith("FILE:"):
            if current_file:
                files[current_file] = "\n".join(buffer).strip()
                buffer = []
            current_file = line.split("FILE:",1)[1].strip()
        elif current_file is not None:
            buffer.append(line)

    if current_file and buffer:
        files[current_file] = "\n".join(buffer).strip()

    return files

def generate_app_from_spec(spec: str, output_dir: str = "generated_app") -> Path:
    """
    Given a plain-English app spec, calls GPT to build a minimal
    project structure, writes it under `output_dir/`, and returns
    the Path to that directory.
    """
    system_prompt = """
You are an expert full-stack developer. Create a project structure and essential file contents
based on the user’s specification. 

Output **only** in this format:

  FILE: path/to/filename.ext
  [file contents here]

Use realistic code patterns, include brief comments, and skip any extraneous files.
"""

    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Specification:\n\n{spec}"}
        ],
        temperature=0.3,
        max_tokens=3000
    )

    project_text = resp.choices[0].message.content
    files = parse_project_structure(project_text)  # :contentReference[oaicite:0]{index=0}

    if not files:
        raise RuntimeError("Failed to parse project structure from GPT response")

    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    for rel_path, content in files.items():
        target = out / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return out
