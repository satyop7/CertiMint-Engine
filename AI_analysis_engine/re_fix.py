import re

def fix_main_py():
    """
    This function adds the missing re import to main.py
    """
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'r') as f:
        content = f.read()
    
    # Add re import if not present
    if 'import re' not in content:
        content = content.replace(
            'import socket',
            'import socket\nimport re'
        )
    
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'w') as f:
        f.write(content)
    
    return "Added re import to main.py"

if __name__ == "__main__":
    fix_main_py()