import os
import sys
import subprocess
import streamlit as st

# Add the `src` directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.upgrade_project import read_code, upgrade_code, write_code  # Corrected import
from backend.autocoder_enhancer import enhance_enhancer  # Corrected import
from dotenv import load_dotenv
import time
import json
import hashlib

from memory.logger import log_memory, get_edit_history  # Corrected import

from memory.database import initialize_database, save_project_snapshot, get_project_history  # Corrected import
from utils.file_utils import scan_project_directory, format_directory_tree  # Corrected import
from backend.app_generator import generate_app_from_spec  # Corrected import

# Load environment variables
load_dotenv()

# Initialize database
initialize_database()

def set_page_settings():
    st.set_page_config(
        page_title="AI Coding Assistant", 
        layout="wide",
        page_icon="🤖"
    )

def auto_heal_generated(output_dir):
    """
    Automatically fill in any stubs or TODOs in the generated app.
    This is a second-pass enhancement after initial generation.
    """
    try:
        # Step 1: get a flat list of all .py files under output_dir
        tree = scan_project_directory(output_dir)
        flat_files = []
        def _flatten(d, prefix=""):
            for name, sub in d.items():
                path = os.path.join(prefix, name) if prefix else name
                if sub is None:
                    if path.endswith(".py"):
                        flat_files.append(os.path.join(output_dir, path))
                else:
                    _flatten(sub, path)
        _flatten(tree)

        if not flat_files:
            st.error("❌ No Python files found in generated app")
            return

        with st.spinner("🧠 Auto-healing generated app..."):
            for full_path in flat_files:
                # Step 2: read the file’s content
                orig = read_code(full_path).get(full_path, None)
                if orig is None:
                    continue

                # Step 3: upgrade it
                fixed = upgrade_code(
                    { full_path: orig },
                    "Fill in unimplemented methods, remove TODOs, and ensure this file runs without errors.",
                    provider=st.session_state.provider,
                    model=st.session_state.model,
                    temperature=0.2
                )

                # Step 4: write back any fixes (with .bak backup)
                if fixed:
                    write_code(fixed)

        st.success("✅ Auto-healing completed!")
    except Exception as e:
        st.error(f"❌ Auto-healing failed: {e}")

def configure_sidebar():
    st.sidebar.title("⚙️ Settings")
    dark_mode = st.sidebar.checkbox("🌙 Dark Mode", value=True)
    
    st.sidebar.subheader("🧠 AI Configuration")
    provider = st.sidebar.selectbox(
        "Provider",
        ["OpenAI", "DeepSeek"],
        index=0
    )
    
    models = {
        "OpenAI": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "DeepSeek": ["deepseek-coder"]
    }
    
    model = st.sidebar.selectbox(
        "Model", 
        models[provider],
        index=0
    )
    
    temperature = st.sidebar.slider(
        "Temperature", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.3
    )
    
    st.session_state.setdefault("provider", provider)
    st.session_state.setdefault("model", model)
    st.session_state.setdefault("temperature", temperature)
    
    return dark_mode

def apply_dark_mode(dark_mode):
    if dark_mode:
        st.markdown("""
            <style>
            body { background-color: #121212; color: #e0e0e0; }
            .stTextArea textarea { background-color: #1e1e1e; color: #e0e0e0; }
            .stButton>button { 
                background-color: #6a1b9a; 
                color: white; 
                border-radius: 10px;
                padding: 0.5rem 1rem;
            }
            .stButton>button:hover { 
                background-color: #9c4dcc; 
                box-shadow: 0 0 10px #9c4dcc; 
            }
            .css-1aumxhk { background-color: #1e1e1e; }
            .file-tree { 
                background-color: #1e1e1e; 
                padding: 10px; 
                border-radius: 5px; 
                max-height: 400px; 
                overflow-y: auto;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            body { background-color: #ffffff; color: #000000; }
            .stButton>button { 
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 0.5rem 1rem;
            }
            .stButton>button:hover { 
                background-color: #45a049; 
                box-shadow: 0 0 10px #4CAF50; 
            }
            .file-tree { 
                background-color: #f5f5f5; 
                padding: 10px; 
                border-radius: 5px; 
                max-height: 400px; 
                overflow-y: auto;
            }
            </style>
        """, unsafe_allow_html=True)

def choose_path(label="📂 Path to file or folder"):
    """
    Let the user enter or paste a path; store it in session_state.
    """
    key = label.replace(" ", "_")
    path = st.text_input(label, st.session_state.get(key, ""))
    if path and os.path.exists(path):
        st.session_state[key] = path
    return st.session_state.get(key, "")


def perform_upgrade(file_path, upgrade_instruction):
    try:
        files = read_code(file_path)
        if not files:
            st.error("❌ No valid files found")
            return None, files
            
        with st.spinner("🧠 Applying AI upgrades..."):
            upgraded = upgrade_code(
                files, 
                upgrade_instruction,
                provider=st.session_state.provider,
                model=st.session_state.model,
                temperature=st.session_state.temperature
            )
            if upgraded:
                write_code(upgraded)
                
                # Save project snapshot
                project_hash = save_project_snapshot(file_path, files, upgraded)
                st.session_state["last_project_hash"] = project_hash
                
        return upgraded, files
    except Exception as e:
        st.error(f"⚠️ Upgrade failed: {e}")
        # Attempt self-healing
        with st.spinner("🛠️ Attempting self-healing..."):
            try:
                fixed = self_heal_upgrade(file_path, upgrade_instruction, str(e))
                if fixed:
                    st.success("✅ Self-healing successful!")
                    return fixed, files
            except Exception as heal_error:
                st.error(f"❌ Self-healing failed: {heal_error}")
        return None, None

def self_heal_upgrade(file_path, upgrade_instruction, error_message):
    """Attempt to automatically fix upgrade errors"""
    try:
        files = read_code(file_path)
        if not files:
            return None
            
        # Create healing prompt
        prompt = f"""
        The following error occurred while trying to upgrade the code:
        {error_message}
        
        Original upgrade instruction:
        {upgrade_instruction}
        
        Please diagnose the issue and provide corrected code.
        """
        
        # Attempt to fix with AI
        fixed = upgrade_code(
            files, 
            prompt,
            provider=st.session_state.provider,
            model=st.session_state.model,
            temperature=0.1  # Low temperature for precise fixes
        )
        
        if fixed:
            write_code(fixed)
            return fixed
    except Exception:
        return None

def display_upgrade_preview(original, upgraded):
    """Show diff between original and upgraded code"""
    for fname, new_content in upgraded.items():
        orig_content = original.get(fname, "")
        
        st.subheader(f"🔧 {fname}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Original")
            st.code(orig_content, language='python')
            
        with col2:
            st.caption("Upgraded")
            st.code(new_content, language='python')
            
        # Log to memory
        try:
            log_memory(orig_content, new_content)
        except Exception as e:
            st.warning(f"🔍 Could not log edit: {e}")

def show_generator_page():
    """Allow the user to spin up a brand-new app from a spec, auto-heal, lint, and preview/enhance files."""
    st.header("🛠️ App Generator")
    spec = st.text_area("📋 Enter your app’s specification", height=200)

    if st.button("🚀 Generate App", use_container_width=True):
        if st.session_state.provider == "OpenAI" and not os.getenv("OPENAI_API_KEY"):
            st.error("❌ OPENAI_API_KEY not set")
        elif not spec.strip():
            st.warning("⚠️ Please enter a specification")
        else:
            try:
                with st.spinner("Generating project…"):
                    output_dir = generate_app_from_spec(spec)
                    # second-pass fill in any stubs
                    auto_heal_generated(output_dir)
                    # lint & auto-fix
                    tree_tmp = scan_project_directory(output_dir)
                    flat_tmp = []
                    def _flatten(d, prefix=""):
                        for name, sub in d.items():
                            path = os.path.join(prefix, name) if prefix else name
                            if sub is None:
                                flat_tmp.append(path)
                            else:
                                _flatten(sub, path)
                    _flatten(tree_tmp)
                    errors = lint_and_test(output_dir)
                    if errors:
                        with st.spinner("Fixing lint errors…"):
                            for rel in flat_tmp:
                                full = os.path.join(output_dir, rel)
                                content = open(full, encoding='utf-8').read()
                                fixed = upgrade_code(
                                    {full: content},
                                    f"Flake8 errors:\n{errors}\nPlease correct them.",
                                    provider=st.session_state.provider,
                                    model=st.session_state.model,
                                    temperature=0.1
                                )
                                if fixed:
                                    for p, new in fixed.items():
                                        relp = os.path.relpath(p, output_dir)
                                        write_file(relp, output_dir, new)
                st.success(f"🎉 Project generated in `{output_dir}`")
                st.session_state["generated_app"] = output_dir
            except Exception as e:
                st.error(f"❌ Generation failed: {e}")

    # If we have a generated app, show its tree + let the user preview/enhance individual files
    base = st.session_state.get("generated_app")
    if base:
        tree = scan_project_directory(base)
        flat_files = []
        def _flatten(d, prefix=""):
            for name, sub in d.items():
                path = os.path.join(prefix, name) if prefix else name
                if sub is None:
                    flat_files.append(path)
                else:
                    _flatten(sub, path)
        _flatten(tree)

        with st.expander("📂 Generated Project Structure", expanded=True):
            st.markdown(format_directory_tree(tree), unsafe_allow_html=True)

        choice = st.selectbox("🔍 Preview a generated file", [""] + flat_files)
        if choice:
            full_path = os.path.join(base, choice)
            content = open(full_path, encoding='utf-8').read()
            st.code(content, language='python')

            if st.button("🧬 Enhance this file", key="enhance_gen_file"):
                prompt = st.text_area(
                    "💡 Enhancement prompt",
                    "Fill in unimplemented methods, remove TODOs, and ensure this file runs without errors.",
                    key="gen_enhance_prompt"
                )
                with st.spinner("Enhancing…"):
                    fixed = upgrade_code(
                        { full_path: content },
                        prompt,
                        provider=st.session_state.provider,
                        model=st.session_state.model,
                        temperature=0.2
                    )
                    if fixed:
                        for p, new in fixed.items():
                            rel = os.path.relpath(p, base)
                            write_file(rel, base, new)
                        st.success("✅ File enhanced!")
                        st.experimental_rerun()

import subprocess


import os

def write_file(rel_path: str, base_dir: str, content: str) -> None:
    """
    Write `content` to file at `base_dir/rel_path`, creating directories if needed.
    """
    full_path = os.path.join(base_dir, rel_path)
    # Ensure the directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    # Write the content
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)


def lint_and_test(base_dir: str) -> str:
    """
    Run Flake8 and pytest on `base_dir`.
    Returns a combined error report, or empty string if all pass.
    """
    reports = []

    # 1) Flake8 linting
    lint = subprocess.run(
        ['flake8', base_dir],
        capture_output=True,
        text=True
    )
    if lint.returncode != 0:
        reports.append("🔍 Lint errors:\n" + lint.stdout)

    # 2) Pytest (discover tests under base_dir)
    test = subprocess.run(
        ['pytest', base_dir, '--maxfail=1', '--disable-warnings'],
        capture_output=True,
        text=True
    )
    if test.returncode != 0:
        reports.append("🧪 Test failures:\n" + test.stdout + test.stderr)

    return "\n\n".join(reports)


def show_project_browser(project_path):
    """Display project directory structure with real-time updates"""
    st.subheader("🌐 Project Structure")
    
    if not project_path or not os.path.exists(project_path):
        st.warning("⚠️ Please select a valid project path")
        return
        
    # Scan project directory
    project_tree = scan_project_directory(project_path)
    formatted_tree = format_directory_tree(project_tree)
    
    # Display with expandable sections
    with st.expander("📁 Project Tree", expanded=True):
        st.markdown(f"<div class='file-tree'>{formatted_tree}</div>", unsafe_allow_html=True)
    
    # Show file count stats
    file_count = sum(1 for _ in os.walk(project_path))
    st.caption(f"📊 {file_count} files in project")

def show_autocoder_page():
    st.header("⚙️ Autocoder Upgrade Tool")
    
    # Path selection via Streamlit
    file_path = choose_path("📂 Path to file or folder")
    
    # Show project browser if a directory is selected
    if file_path and os.path.isdir(file_path):
        show_project_browser(file_path)
                
    # Upgrade instruction
    upgrade_options = [
        "Improve readability",
        "Add dark theme",
        "Refactor into functions",
        "Convert to class-based structure",
        "Document with comments",
        "Optimize for performance"
    ]
    
    selected_upgrade = st.selectbox("💡 Suggested Upgrades", upgrade_options)
    custom_upgrade = st.text_area(
        "🎯 Custom upgrade instruction:",
        value=selected_upgrade,
        height=100
    )
    
    # Execute upgrade
    if st.button("🚀 Apply Upgrade", use_container_width=True):
        if st.session_state.provider == "OpenAI" and not os.getenv("OPENAI_API_KEY"):
            st.error("❌ OPENAI_API_KEY not set in .env file")
        elif st.session_state.provider == "DeepSeek" and not os.getenv("DEEPSEEK_API_KEY"):
            st.error("❌ DEEPSEEK_API_KEY not set in .env file")
        elif not file_path or not os.path.exists(file_path):
            st.warning("⚠️ Please select a valid file or folder")
        else:
            upgraded, original = perform_upgrade(file_path, custom_upgrade)
            if upgraded:
                st.success("🎉 Upgrade completed successfully!")
                st.balloons()
                
                # Show preview
                with st.expander("📝 Upgrade Preview"):
                    display_upgrade_preview(original, upgraded)
                
                # Record history
                history_entry = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "path": file_path,
                    "instruction": custom_upgrade,
                    "files": list(upgraded.keys())
                }
                st.session_state.setdefault("edit_history", []).append(history_entry)
                
    # History section
    st.subheader("📜 Edit History")
    if st.session_state.get("edit_history"):
        for i, entry in enumerate(reversed(st.session_state.edit_history)):
            with st.expander(f"{entry['timestamp']} - {entry['path']}"):
                st.write(f"**Instruction:** {entry['instruction']}")
                st.write(f"**Files modified:** {len(entry['files'])}")
                if st.button(f"View details {i}", key=f"details_{i}"):
                    st.json(entry)
    else:
        st.info("No edit history yet")
        
    # Project memory
    if st.session_state.get("last_project_hash"):
        st.subheader("💾 Project Memory")
        project_history = get_project_history(st.session_state.last_project_hash)
        if project_history:
            for snapshot in project_history[-3:]:
                st.caption(f"{snapshot['timestamp']} - {snapshot['operation']}")
        else:
            st.info("No project history recorded")


def enhance_autocoder_ui():
    st.header("🧬 Enhance the Enhancer (Meta-Upgrades)")
    
    with st.form("enhance_form"):
        file_to_enhance = st.text_input(
            "📄 File to Enhance", 
            value="backend/upgrade_project.py"
        )
        
        instruction = st.text_area(
            "💡 Enhancement Prompt", 
            value="Refactor the code, add inline comments, and improve error handling.",
            height=150
        )
        
        submitted = st.form_submit_button("🔧 Enhance")
        
    if submitted:
        if not file_to_enhance or not os.path.exists(file_to_enhance):
            st.warning("⚠️ Please enter a valid file path")
        else:
            with st.spinner("🧠 Applying meta-upgrades..."):
                result = enhance_enhancer(
                    file_to_enhance, 
                    instruction,
                    provider=st.session_state.provider,
                    model=st.session_state.model,
                    temperature=st.session_state.temperature
                )
                st.success(result)

def main():
    set_page_settings()
    dark_mode = configure_sidebar()
    apply_dark_mode(dark_mode)
    
    # Initialize session state
    st.session_state.setdefault("selected_path", "")
    st.session_state.setdefault("last_project_hash", None)
    
    # Navigation
    st.sidebar.title("📂 Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["🧠 Autocoder", "🧬 Enhancer", "🛠️ Generator", "📚 Project History", "ℹ️ About"],
        label_visibility="collapsed"
    )
    
    if page == "🧠 Autocoder":
        show_autocoder_page()
    elif page == "🧬 Enhancer":
        enhance_autocoder_ui()
    elif page == "📚 Project History":
        st.title("Project History")
        if st.session_state.get("selected_path"):
            project_history = get_edit_history(st.session_state.selected_path)
            if project_history:
                for entry in project_history:
                    with st.expander(f"{entry['timestamp']} - {entry['file_path']}"):
                        st.code(entry['content'], language='python')
            else:
                st.info("No history for this project")
        else:
            st.info("Select a project to view history")
    elif page == "🛠️ Generator":
        show_generator_page()
    elif page == "ℹ️ About":
        st.title("About Autocoder")
        st.markdown("""
        ### AI-Powered Code Enhancement Tool
            
        **Features:**
        - Upgrade existing codebases with AI (OpenAI & DeepSeek)
        - Real-time project directory visualization
        - Project history and memory retention
        - Self-healing error correction
        - Generate new projects from specifications
            
        **How to use:**
        1. Select a file or folder
        2. Choose an upgrade or enter custom instructions
        3. Apply the AI-powered upgrades
        4. Review and commit changes
        """)

if __name__ == "__main__":
    main()