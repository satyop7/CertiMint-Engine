"""
Replace main.py with the fixed version
"""
import os
import shutil

def replace_main():
    """Replace main.py with the fixed version"""
    # Backup original main.py
    shutil.copy('/home/rick/projects/llama-sandbox-clean/main.py', 
                '/home/rick/projects/llama-sandbox-clean/main.py.bak')
    
    # Replace with fixed version
    shutil.copy('/home/rick/projects/llama-sandbox-clean/main_fixed.py', 
                '/home/rick/projects/llama-sandbox-clean/main.py')
    
    return "Replaced main.py with fixed version"

if __name__ == "__main__":
    print(replace_main())