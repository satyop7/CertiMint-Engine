"""
Fix the syntax error in main.py by directly examining the file
"""
import os

def fix_syntax():
    """Fix the syntax error in main.py"""
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'r') as f:
        lines = f.readlines()
    
    # Find the problematic line
    for i, line in enumerate(lines):
        if 'import enhanced_detection' in line:
            print(f"Found problematic import at line {i+1}")
            # Check if it's inside a try block
            j = i - 1
            while j >= 0 and 'try:' not in lines[j]:
                j -= 1
            
            if j >= 0 and 'try:' in lines[j]:
                print(f"Found try block at line {j+1}")
                # Remove the import from inside the try block
                lines[i] = ''
                
                # Add import at the top of the file
                for k, line in enumerate(lines):
                    if 'import socket' in line:
                        lines.insert(k+1, 'import enhanced_detection\n')
                        print(f"Added import after line {k+1}")
                        break
            break
    
    # Write the fixed file
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'w') as f:
        f.writelines(lines)
    
    return "Fixed syntax error in main.py"

if __name__ == "__main__":
    fix_syntax()