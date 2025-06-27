#!/usr/bin/env python3
import os
import hashlib
import sys

def check_model_integrity(model_path):
    """Check if the model file exists and has a reasonable size"""
    if not os.path.exists(model_path):
        print(f"Error: Model file {model_path} not found!")
        return False
        
    # Check file size
    size_bytes = os.path.getsize(model_path)
    size_mb = size_bytes / (1024 * 1024)
    
    print(f"Model file size: {size_mb:.2f} MB")
    
    if size_mb < 100:
        print(f"Warning: Model file is suspiciously small ({size_mb:.2f} MB)")
        print("This may not be a valid GGUF model file.")
        return False
        
    # Calculate file hash for the first 1MB to check consistency
    print("Calculating model file hash (first 1MB)...")
    m = hashlib.md5()
    with open(model_path, 'rb') as f:
        m.update(f.read(1024 * 1024))
    file_hash = m.hexdigest()
    print(f"Model file hash (first 1MB): {file_hash}")
    
    return True

if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else "phi-2.Q4_K_M.gguf"
    is_valid = check_model_integrity(model_path)
    sys.exit(0 if is_valid else 1)
