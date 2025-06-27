#!/usr/bin/env python3
import os
import sys
import glob

def find_gguf_models(search_dirs=None):
    """Find all GGUF model files in the given directories"""
    if search_dirs is None:
        # Default search locations
        search_dirs = [
            ".",  # Current directory
            "./models",  # Models directory
            "../models",  # Parent models directory
            os.path.expanduser("~/.cache/huggingface/"),  # Huggingface cache
        ]
    
    found_models = []
    
    for directory in search_dirs:
        if os.path.exists(directory):
            # Search for .gguf files recursively
            for path in glob.glob(os.path.join(directory, "**", "*.gguf"), recursive=True):
                size_mb = os.path.getsize(path) / (1024 * 1024)
                found_models.append({
                    "path": path,
                    "size_mb": size_mb
                })
    
    # Sort by size (largest first) as a heuristic for model quality
    found_models.sort(key=lambda x: x["size_mb"], reverse=True)
    
    return found_models

if __name__ == "__main__":
    print("Searching for GGUF model files...")
    models = find_gguf_models()
    
    if not models:
        print("No GGUF model files found.")
        sys.exit(1)
    
    print("\nFound models:")
    for i, model in enumerate(models):
        print(f"{i+1}. {model['path']} ({model['size_mb']:.2f} MB)")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        # Export the first model path
        if models:
            with open("found_model.txt", "w") as f:
                f.write(models[0]["path"])
            print(f"\nExported best model path to found_model.txt: {models[0]['path']}")
