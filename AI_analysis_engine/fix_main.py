"""
Fix the syntax error in main.py
"""
import os

def fix_main_py():
    """Fix the syntax error in main.py"""
    # Read the original file
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'r') as f:
        lines = f.readlines()
    
    # Add import at the top of the file
    import_added = False
    new_lines = []
    for line in lines:
        if 'import socket' in line and not import_added:
            new_lines.append(line)
            new_lines.append('import enhanced_detection\n')
            import_added = True
        else:
            new_lines.append(line)
    
    # Write the fixed file
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'w') as f:
        f.writelines(new_lines)
    
    return "Added enhanced_detection import to main.py"

if __name__ == "__main__":
    fix_main_py()