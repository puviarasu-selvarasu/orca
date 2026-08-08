import os
import subprocess
from pathlib import Path

# ============================================================
# SANDBOX CONFIGURATION
# ============================================================
SANDBOX_ROOT = Path("C:/ORCA/generated_projects/")
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)

# ============================================================
# FILE OPERATIONS
# ============================================================
def safe_write_file(relative_path: str, content: str) -> str:
    """Write a file inside the sandbox directory."""
    full_path = SANDBOX_ROOT / relative_path
    
    # Security: Prevent path traversal (e.g., ../../windows/system32)
    try:
        full_path.resolve().relative_to(SANDBOX_ROOT.resolve())
    except ValueError:
        return "⛔ Blocked: Attempted to write outside the sandbox."
    
    # Create parent directories
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the file
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return f"✅ Created: {relative_path}"

def safe_read_file(relative_path: str) -> str:
    """Read a file inside the sandbox directory."""
    full_path = SANDBOX_ROOT / relative_path
    
    try:
        full_path.resolve().relative_to(SANDBOX_ROOT.resolve())
    except ValueError:
        return "⛔ Blocked: Attempted to read outside the sandbox."
    
    if not full_path.exists():
        return f"❌ File not found: {relative_path}"
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()

def safe_list_dir(relative_path: str = ".") -> list:
    """List contents of a directory inside the sandbox."""
    full_path = SANDBOX_ROOT / relative_path
    
    try:
        full_path.resolve().relative_to(SANDBOX_ROOT.resolve())
    except ValueError:
        return ["⛔ Blocked: Attempted to access outside the sandbox."]
    
    if not full_path.exists():
        return [f"❌ Directory not found: {relative_path}"]
    
    return [str(p.relative_to(SANDBOX_ROOT)) for p in full_path.iterdir()]

# ============================================================
# COMMAND EXECUTION (Whitelisted)
# ============================================================
ALLOWED_COMMANDS = [
    # Python ecosystem
    'pip', 'python', 'django-admin', 
    # Node ecosystem
    'npm', 'npx', 'node',
    # PHP / Laravel
    'php', 'composer', 'artisan', 
    # Java / Spring Boot
    'java', 'javac', 'mvn', 'gradle', 'jar',
    # General utilities
    'git', 'echo', 'dir', 'ls', 'mkdir', 'touch'
]


def safe_execute_command(command: str, timeout: int = 30) -> str:
    """Execute a command inside the sandbox with a timeout."""
    # Split command into parts
    parts = command.strip().split()
    if not parts:
        return "❌ Empty command."
    
    # Check if the command is whitelisted
    if parts[0] not in ALLOWED_COMMANDS:
        return f"⛔ Blocked: '{parts[0]}' is not in the allowed commands list."
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(SANDBOX_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        return f"⛔ Command timed out after {timeout} seconds."
    except Exception as e:
        return f"⛔ Error executing command: {str(e)}"