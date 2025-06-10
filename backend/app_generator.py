# backend/app_generator.py

import os
import textwrap
import logging
from pathlib import Path
from dotenv import load_dotenv
import openai
from openai import OpenAI, APIError
import re

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def break_down_task(prompt: str) -> str:
    """
    Break down a high-level goal into clear subgoals.
    Returns the breakdown as a string.
    """
    system_prompt = textwrap.dedent("""
        You are a senior engineer. Break down high-level goals into clear subgoals.

        Output format:
        1. [Task 1]
        2. [Task 2]
        3. [Task 3]

        Include:
        - Technical steps
        - Required resources
        - Potential challenges
    """).strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"Break down this task: {prompt}"}
    ]

    try:
        res = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.4,
            max_tokens=1000
        )
        breakdown = res.choices[0].message.content.strip()
        logger.info("Task breakdown:\n%s", breakdown)
        return breakdown
    except APIError as e:
        logger.error("OpenAI API error during breakdown: %s", e)
    except Exception as e:
        logger.error("Unexpected error during breakdown: %s", e)
    return ""

def parse_project_structure(response: str) -> dict:
    """
    More robust parser: first try fenced blocks, then fallback to FILE: headers.
    Returns { relative_path: content }.
    """
    result = {}

    # 1) Look for blocks like:
    #    FILE: path/to/file.ext
    #    ```[lang]
    #    code...
    #    ```
    fence_pattern = re.compile(
        r"FILE:\s*(?P<fname>.+?)\s*?\n```(?:[^\n]*)?\n(?P<code>[\s\S]*?)\n```",
        re.MULTILINE
    )
    for m in fence_pattern.finditer(response):
        fname = m.group("fname").strip()
        code  = m.group("code").rstrip()
        result[fname] = code

    if result:
        return result

    # 2) Fallback: split on lines starting with FILE:
    lines = response.splitlines()
    curr = None
    buf  = []
    for line in lines:
        if line.strip().upper().startswith("FILE:"):
            if curr:
                result[curr] = "\n".join(buf).strip()
            curr = line.split(":",1)[1].strip()
            buf = []
        elif curr:
            buf.append(line)
    if curr and buf:
        result[curr] = "\n".join(buf).strip()

    if not result:
        # 3) Debug: log raw GPT output to help tune your prompt
        logger.error("Failed to parse project structure. Raw response:\n%s", response)

    return result

def generate_app_from_spec(spec: str, output_dir: str = "generated_app") -> Path:
    """
    Given an English specification, break it down, then call GPT to scaffold:
    - Logs the breakdown
    - Writes files under output_dir
    - Returns the Path to that directory
    """
    # 1. Break down the spec into subgoals
    breakdown = break_down_task(spec)

    # 2. Prepare the system prompt including breakdown
    system_prompt = textwrap.dedent(f"""
        You are an expert full-stack developer.
        Here is the project specification:

        {spec}

        And here is a suggested breakdown of tasks:

        {breakdown}

        Based on that, create a complete project structure with essential file contents.
        Output **only** in this format:

          FILE: path/to/filename.ext
          [file contents here]

        Use realistic code patterns, include brief comments, and skip any extraneous files.
    """).strip()

    # 3. Call the API to generate scaffold
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": "Please output the project files as specified above."}
        ],
        temperature=0.3,
        max_tokens=3000
    )

    project_text = resp.choices[0].message.content
    files = parse_project_structure(project_text)
    if not files:
        raise RuntimeError("Failed to parse project structure from GPT response")

    # 4. Write files to disk
    out_dir = Path(output_dir)
    out_dir.mkdir(exist_ok=True)
    for rel_path, content in files.items():
        target = out_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info("Wrote %s", target)

    return out_dir
