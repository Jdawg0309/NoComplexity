# src/backend/autocoder_enhancer.py

from .upgrade_project import read_code, upgrade_code, write_code
import logging
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def enhance_enhancer(
    file_path: str, 
    upgrade_instruction: str,
    provider: str = "OpenAI",
    model: str = "gpt-4-turbo",
    temperature: float = 0.3
) -> str:
    """
    Uses AI to enhance the given enhancer script.
    Returns detailed success/error message.
    """
    try:
        original_code = read_code(file_path)
        enhanced_code = upgrade_code(
            original_code, 
            upgrade_instruction,
            provider=provider,
            model=model,
            temperature=temperature
        )
        write_code(enhanced_code)
        return f"✅ Enhancement successful for {file_path}"
    except FileNotFoundError:
        return f"❌ File not found: {file_path}"
    except PermissionError:
        return f"❌ Permission denied for: {file_path}"
    except Exception as e:
        logging.exception("Enhancement failed")
        return f"❌ Enhancement failed: {str(e)}"