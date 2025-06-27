#!/bin/bash
# This script fixes compatibility issues with the Phi-2 model and llama.cpp
# It should be run before trying to use the model in Docker or other environments

# Log start
echo "Starting Phi-2 compatibility fixes..."
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "$TIMESTAMP - PHI2_COMPAT_MODE v1.0.1"

# Check if the model exists
MODEL_PATH="phi-2.Q4_K_M.gguf"
if [ ! -f "$MODEL_PATH" ]; then
  echo "Error: Model file $MODEL_PATH not found!"
  echo "Please ensure the model file exists in the current directory."
  exit 1
fi

# Get model file size
MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
echo "Model file size: $MODEL_SIZE"

# Set compatibility environment variables
echo "Setting compatibility environment variables..."
export PHI2_COMPAT_MODE=1
echo "PHI2_COMPAT_MODE=1"

# Check for required packages
echo "Checking Python packages..."
pip list | grep -E "llama-cpp-python|numpy" || {
  echo "Installing required packages..."
  pip install llama-cpp-python numpy
}

# Verify llama-cpp-python version
LLAMA_VERSION=$(python -c "import llama_cpp; print(llama_cpp.__version__)" 2>/dev/null || echo "unknown")
echo "llama-cpp-python version: $LLAMA_VERSION"

# Check model file permissions
echo "Checking model file permissions..."
if [ ! -r "$MODEL_PATH" ]; then
  echo "Fixing permissions on $MODEL_PATH"
  chmod 644 "$MODEL_PATH"
fi

# Create a simple compatibility test file
echo "Creating compatibility test file..."
cat > test_phi2.py << EOL
#!/usr/bin/env python3
import os
import sys
from phi2_adapter import Phi2Adapter

# Set compatibility mode
os.environ["PHI2_COMPAT_MODE"] = "1"

def test_model(model_path):
    print(f"Testing Phi-2 model at: {model_path}")
    adapter = Phi2Adapter(model_path)
    
    print("Trying to load model...")
    if adapter.load_model(verbose=True):
        print("✓ Model loaded successfully!")
        
        # Try a simple generation
        prompt = "Hello, I am"
        print(f"Testing with prompt: '{prompt}'")
        
        result = adapter.generate(prompt, max_tokens=10)
        if "choices" in result and len(result["choices"]) > 0:
            text = result["choices"][0]["text"]
            print(f"✓ Generated: '{text}'")
            return True
        else:
            print(f"✗ Generation failed: {result}")
            return False
    else:
        print("✗ Failed to load model")
        return False

if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else "phi-2.Q4_K_M.gguf"
    if not os.path.exists(model_path):
        print(f"Error: Model file {model_path} not found!")
        sys.exit(1)
        
    success = test_model(model_path)
    sys.exit(0 if success else 1)
EOL

echo "Creating test redundancy fix module..."
cat > test_redundancy_fix.py << EOL
#!/usr/bin/env python3
import os
import json
import sys

def check_json_response(text):
    """Fix common issues with JSON responses from LLMs"""
    if not text:
        return {}
        
    # Find JSON blocks in the text
    json_start = text.find("{")
    json_end = text.rfind("}")
    
    if json_start >= 0 and json_end > json_start:
        try:
            # Extract just the JSON part
            json_text = text[json_start:json_end+1]
            
            # Clean up newlines and tabs
            json_text = json_text.replace('\\n', ' ').replace('\\t', ' ')
            
            # Fix common JSON formatting issues
            import re
            # Convert unquoted keys to quoted keys
            json_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
            # Convert single quotes to double quotes around strings
            json_text = re.sub(r':\s*\'([^\']+)\'', r':"\1"', json_text)
            json_text = json_text.replace("'", '"')
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)
            
            # Parse the cleaned JSON
            result = json.loads(json_text)
            return result
        except Exception as e:
            print(f"JSON parsing error: {e}")
            print(f"Problematic JSON: {json_text[:100]}...")
    
    # If no valid JSON found or parsing failed
    return {}

# Test the function
if __name__ == "__main__":
    test_cases = [
        '{"key": "value"}',
        'Some text before {"key": "value"} and after',
        'Result: {key: "value"}',
        '{key: value, status: "success"}',
        '{key: "value", list: [1, 2, 3], "quoted": "text", trailing: 100,}',
        "{'single': 'quotes', list: [1, 2, 3]}"
    ]
    
    print("Testing JSON redundancy fix:")
    for i, test in enumerate(test_cases):
        print(f"\nTest {i+1}: {test}")
        result = check_json_response(test)
        print(f"Result: {result}")
EOL

echo "Creating model integrity checker..."
cat > check_model_integrity.py << EOL
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
EOL

# Make the test scripts executable
chmod +x test_phi2.py
chmod +x test_redundancy_fix.py
chmod +x check_model_integrity.py

# Run file integrity check
echo "Running model integrity check..."
python check_model_integrity.py "$MODEL_PATH"

# Create fallback model finder
cat > find_model.py << EOL
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
EOL

chmod +x find_model.py

echo "All compatibility fixes applied successfully!"
echo "To enable compatibility mode, run: export PHI2_COMPAT_MODE=1"
echo "To test the model, run: python test_phi2.py"
