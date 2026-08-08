import ast

# ============================================================
# DANGEROUS PATTERNS
# ============================================================
DANGEROUS_FUNCS = {
    'os', 'subprocess', 'eval', 'exec', '__import__',
    'open', 'shutil', 'sys', 'socket', 'requests'
}

DANGEROUS_ATTRS = {
    'system', 'popen', 'remove', 'rmdir', 'unlink',
    'chmod', 'chown', 'kill', 'exit', 'quit'
}

def scan_code(code: str) -> tuple:
    """
    Scans Python code for dangerous patterns.
    Returns (is_safe: bool, message: str)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"❌ Invalid Python syntax: {e}"
    
    for node in ast.walk(tree):
        # Check for direct dangerous calls (e.g., os.system())
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in DANGEROUS_FUNCS:
                    return False, f"⛔ Blocked: Direct call to '{node.func.id}()'"
            
            elif isinstance(node.func, ast.Attribute):
                # Check for attribute calls (e.g., os.system)
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id in DANGEROUS_FUNCS:
                        return False, f"⛔ Blocked: '{node.func.value.id}.{node.func.attr}()'"
                
                if node.func.attr in DANGEROUS_ATTRS:
                    return False, f"⛔ Blocked: '{node.func.attr}()' call detected."
        
        # Check for dangerous imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in DANGEROUS_FUNCS:
                    return False, f"⛔ Blocked: Import of '{alias.name}'"
        
        if isinstance(node, ast.ImportFrom):
            if node.module in DANGEROUS_FUNCS:
                return False, f"⛔ Blocked: Import from '{node.module}'"
    
    return True, "✅ Code is safe."

def scan_php_java(code: str, language: str) -> tuple:
    """Basic pattern check for PHP/Java dangerous calls."""
    dangerous_patterns = [
        'exec(', 'shell_exec(', 'system(', 'passthru(',
        'Runtime.exec(', 'ProcessBuilder'
    ]
    
    for pattern in dangerous_patterns:
        if pattern in code:
            return False, f"⚠️ Suspicious pattern detected: '{pattern}' in {language} code. Please review manually."
    
    return True, f"✅ No obvious dangerous patterns found in {language} code."