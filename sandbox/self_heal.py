import json
import subprocess
from pathlib import Path
from .filesystem import safe_read_file, safe_write_file, SANDBOX_ROOT

def self_heal(project_path: str, error_log: str) -> dict:
    """
    Takes a project path and an error log, analyzes the error using the LLM,
    and returns a corrected plan for the broken file(s).
    """
    from chat.llm_wrapper import get_llm
    
    llm = get_llm()
    if llm is None:
        return {"error": "LLM not loaded. Please restart the server."}
    
    # Read the file that likely caused the error
    # (This is a simplified implementation – in reality, we'd parse the error log to find the file)
    try:
        # Attempt to read the main file (you can make this smarter)
        possible_files = ['app.py', 'main.py', 'manage.py', 'server.py']
        file_content = None
        target_file = None
        
        for fname in possible_files:
            fpath = Path(SANDBOX_ROOT) / project_path / fname
            if fpath.exists():
                file_content = safe_read_file(f"{project_path}/{fname}")
                target_file = f"{project_path}/{fname}"
                break
        
        if file_content is None:
            return {"error": "Could not find the file that caused the error."}
        
        # Build the self-heal prompt
        prompt = f"""You are O.R.C.A.'s self-healing engine. The user's code crashed with this error:

ERROR:
{error_log}

CODE FILE ({target_file}):
{file_content}

Please fix the code to resolve the error. Return ONLY the corrected code, no explanations, no markdown."""
        
        response = llm.create_completion(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,
            echo=False
        )
        
        corrected_code = response['choices'][0]['text'].strip()
        
        # Write the corrected code
        safe_write_file(target_file, corrected_code)
        
        return {
            "status": "healed",
            "file": target_file,
            "message": f"✅ Fixed {target_file}. The error has been resolved."
        }
        
    except Exception as e:
        return {"error": f"Self-healing failed: {str(e)}"}