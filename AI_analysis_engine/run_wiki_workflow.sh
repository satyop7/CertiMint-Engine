#!/bin/bash
# This script implements the Wikipedia-based AI Validation workflow:
# 1. Run Wikipedia scraper to collect reference content for the subject
# 2. Run the main validation pipeline in sandbox mode with network isolation
# Both steps enforce a clear separation between data collection and analysis

set -e  # Exit on error


mkdir -p data

# Default values
SUBJECT="Engineering"
FILE="None"
ID=""
MAX_RESULTS=10
TIMEOUT=60
SKIP_SCRAPE=false
MODEL_PATH="phi-2.Q4_K_M.gguf"  
DOWNLOAD_MODEL=false 
HF_TOKEN=""  # Set your Hugging Face token here or pass via --hf-token
USE_DOCKER=false  # Changed default to false (no Docker)


while [[ $# -gt 0 ]]; do
  case $1 in
    --subject)
      SUBJECT="$2"
      shift 2
      ;;
    --file)
      FILE="$2"
      shift 2
      ;;
    --id)
      ID="$2"
      shift 2
      ;;
    --max-results)
      MAX_RESULTS="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --skip-scrape)
      SKIP_SCRAPE=true
      shift
      ;;
    --model)
      MODEL_PATH="$2"
      shift 2
      ;;
    --download-model)
      DOWNLOAD_MODEL=true
      shift
      ;;
    --hf-token)
      HF_TOKEN="$2"
      shift 2
      ;;
    --use-docker)
      USE_DOCKER=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--subject \"Subject\"] [--file path/to/file.pdf] [--id ID] [--max-results N] [--timeout SEC] [--skip-scrape] [--model MODEL_PATH] [--download-model] [--hf-token TOKEN] [--use-docker]"
      echo ""
      echo "Options:"
      echo "  --subject        Subject for Wikipedia scraping (default: Engineering)"
      echo "  --file           Path to the PDF file to analyze (required)"
      echo "  --id             Assignment ID (default: generated from date and time)"
      echo "  --max-results    Maximum number of Wikipedia results (default: 10)"
      echo "  --timeout        Timeout for Wikipedia scraping in seconds (default: 60)"
      echo "  --skip-scrape    Skip Wikipedia scraping and use existing references.json"
      echo "  --model          Path to the LLM model file (default: phi-2.Q4_K_M.gguf in root directory)"
      echo "  --download-model Download the model if it doesn't exist (default: false)"
      echo "  --hf-token       Hugging Face token for model download (if needed)"
      echo "  --use-docker     Use Docker for running the workflow (default: false)"
      echo "  --use-docker     Run with Docker network isolation (more secure but may have compatibility issues)"
      echo ""
      echo "Note: By default, the script uses the Phi-2 model file located at phi-2.Q4_K_M.gguf in the project root."
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--subject \"Subject\"] [--file path/to/file.pdf] [--id ID] [--max-results N] [--timeout SEC] [--skip-scrape] [--model MODEL_PATH] [--download-model] [--hf-token TOKEN] [--use-docker]"
      echo ""
      echo "Note: By default, the script uses the Phi-2 model file located at phi-2.Q4_K_M.gguf in the project root without Docker."
      echo "Use --help for more information."
      exit 1
      ;;
  esac
done

# Generate ID 
if [ -z "$ID" ]; then
  ID="ASG$(date +%Y%m%d%H%M)"
fi


if [ "$FILE" = "None" ]; then
  echo "Error: No file specified"
  echo "Please provide a valid file path with --file option"
  exit 1
elif [ ! -f "$FILE" ]; then
  echo "Error: File not found: $FILE"
  echo "Please provide a valid file path with --file option"
  exit 1
fi


if [ ! -f "$MODEL_PATH" ]; then
  echo "========================================================"
  echo "CHECKING MODEL FILE"
  echo "========================================================"
  
  echo " Model not found at: $MODEL_PATH"
  
 
  if [ "$DOWNLOAD_MODEL" = true ]; then
    echo "Attempting to download the model..."
    
  
    MODEL_DIR=$(dirname "$MODEL_PATH")
    
  
    mkdir -p "$MODEL_DIR"
    
   
    if ! command -v huggingface-cli &> /dev/null; then
      echo " huggingface-cli not found. Please install it with: pip install huggingface_hub"
      echo "Then try again, or download the model manually."
      exit 1
    fi
    
    
    if [ ! -z "$HF_TOKEN" ]; then
      export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
      echo "Using provided Hugging Face token for authentication"
    fi
    
    # Use huggingface-cli to download
    echo "Downloading using huggingface-cli..."
    huggingface-cli download TheBloke/phi-2-GGUF phi-2.Q4_K_M.gguf --local-dir "$(dirname "$MODEL_PATH")" --local-dir-use-symlinks False
    
    # Check if download was successful
    if [ $? -eq 0 ]; then
      echo "Model downloaded successfully to $MODEL_PATH"
    else
      echo "Failed to download model"
      echo "Please ensure your Hugging Face token is valid or download the model manually."
      exit 1
    fi
  else
    echo "Error: Model file not found and download is disabled."
    echo "Please check the path to your model file or enable download with --download-model"
    exit 1
  fi
else
  echo "========================================================"
  echo "USING EXISTING PHI-2 MODEL"
  echo "========================================================"
  echo " Found model at: $MODEL_PATH"
fi

OUTPUT_FILE="data/references.json"

#levle1
if [ "$SKIP_SCRAPE" = false ]; then
  echo "========================================================"
  echo "PHASE 1: WIKIPEDIA SCRAPING (Internet-enabled environment)"
  echo "========================================================"
  echo "Subject: $SUBJECT"
  echo "Max results: $MAX_RESULTS"
  echo "Timeout: ${TIMEOUT}s"

 
  echo "Running Wikipedia scraper with timeout of ${TIMEOUT}s..."
  
  timeout $TIMEOUT python3 wikipedia_scraper.py --query "$SUBJECT" --output $OUTPUT_FILE --max-results $MAX_RESULTS || {
    echo "Wikipedia scraping timed out or failed after ${TIMEOUT}s"
    echo "Retrying without timeout..."
    
   
    python3 wikipedia_scraper.py --query "$SUBJECT" --output $OUTPUT_FILE --max-results $MAX_RESULTS
    
   
    if [ -s "$OUTPUT_FILE" ]; then
      echo "Successfully retrieved reference data on retry."
    else
      echo "Error: Could not retrieve data from Wikipedia for subject: $SUBJECT"
      echo "Please check your internet connection and try again."
      exit 1
    fi
  }
else
  echo "========================================================"
  echo "SKIPPING PHASE 1: Using existing reference data"
  echo "========================================================"
  
  # Check if reference file exists when skipping scrape
  if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Reference file not found: $OUTPUT_FILE"
    echo "Cannot skip scraping phase without an existing reference file"
    exit 1
  fi
  
  echo "Using existing reference data from: $OUTPUT_FILE"
fi


echo "Formatting Wikipedia data for sandbox processing..."
python3 -c "
import json
with open('$OUTPUT_FILE', 'r') as f:
    wiki_data = json.load(f)
formatted_data = []
for item in wiki_data:
    # Build a more comprehensive content string with all available data
    content_parts = []
    
    # Always include the introduction
    intro = item.get('introduction', '')
    if intro:
        content_parts.append(intro)
    
    # Include infobox data
    infobox = item.get('infobox', {})
    if infobox:
        infobox_text = '\\n'.join([f'{k}: {v}' for k, v in infobox.items()])
        content_parts.append(infobox_text)
    
    # Include section content if available
    section_content = item.get('section_content', {})
    if section_content:
        for section, content in section_content.items():
            if content and len(content) > 10:  # Only include non-empty sections
                content_parts.append(f'== {section} ==\\n{content}')
    
    # Include raw sections list as fallback
    sections = item.get('sections', [])
    if sections and not section_content:
        content_parts.append('\\n'.join(sections))
    
    # Create the formatted entry with comprehensive content
    formatted_data.append({
        'url': item.get('url', ''),
        'title': item.get('title', ''),
        'content': '\\n\\n'.join(content_parts)
    })
    
with open('$OUTPUT_FILE', 'w') as f:
    json.dump(formatted_data, f, indent=2)

print(f'Successfully formatted {len(formatted_data)} Wikipedia articles with enhanced content')

# Print summary of the scraped data
for i, item in enumerate(formatted_data):
    title = item.get('title', 'Unknown title')
    url = item.get('url', 'No URL')
    content = item.get('content', '')
    content_preview = content[:150] + '...' if len(content) > 150 else content
    print(f'\\nArticle {i+1}: {title}')
    print(f'Source: {url}')
    print(f'Content preview: {content_preview}')
"

# Print Phase 1 summary
echo ""
echo "=== PHASE 1 SUMMARY ==="
echo "Wikipedia scraping status: SUCCESS"
python3 -c "
import json
import os

if os.path.exists('$OUTPUT_FILE') and os.path.getsize('$OUTPUT_FILE') > 0:
    try:
        with open('$OUTPUT_FILE', 'r') as f:
            data = json.load(f)
        
        print(f'Articles scraped: {len(data)}')
        
        for i, item in enumerate(data):
            title = item.get('title', 'Unknown')
            url = item.get('url', 'No URL')
            content = item.get('content', '')
            preview = content[:100] + '...' if len(content) > 100 else content
            
            print(f'\\nArticle {i+1}: {title}')
            print(f'Source: {url}')
            print(f'Preview: \"{preview}\"')
    except Exception as e:
        print(f'Error processing reference data: {e}')
        print('Scraping status: PARTIAL (data format issues)')
else:
    print('Articles scraped: 0')
    print('Scraping status: FAILED (no data collected)')
"

# Step 2: Run in sandboxed mode (NO internet)
#echo "========================================================"
#echo "PHASE 2: SANDBOX PROCESSING (No internet access)"
#echo "========================================================"
echo "Running in network sandbox mode..."
echo "Subject: $SUBJECT"
echo "File: $FILE"
echo "Assignment ID: $ID"

# Deactivate networking by setting environment variables
# These will also be passed to the Docker container
export LANGCHAIN_TRACING=false
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1

# Check if Docker should be used for network isolation
if [ "$USE_DOCKER" = true ]; then
  echo "Using Docker for network isolation and sandboxing..."
  
  # Enhanced AI content detection is enabled:
  # - Stricter semantic similarity threshold (40% instead of 50%)
  # - Stricter LLM similarity threshold (35% instead of 40%)
  # - Pattern-based AI-generated content detection
  # - Emoji detection
  # This ensures the highest level of academic integrity checking
  
  # Run the main Python script in the network-isolated Docker container
  echo "Running the main processing pipeline with Phi-2 model in network-isolated Docker container..."
  echo "Using model: $MODEL_PATH (NO mock fallback allowed)"

  # Get the absolute path to the current directory and files
  CURRENT_DIR=$(pwd)
  ABS_MODEL_PATH=$(realpath $MODEL_PATH)
  ABS_FILE_PATH=$(realpath $FILE)
  ABS_OUTPUT_PATH=$(realpath $OUTPUT_FILE)
  
  # Ensure Docker image exists or build it
  if ! docker image inspect llm-sandbox-phi2:latest &>/dev/null; then
    echo "Docker image not found. Building image first..."
    ./docker_setup.sh
  fi

  echo "Setting up Docker container with network isolation (--network=none)"
  
  # Check if our fix script exists and create it if needed
  if [ ! -f "phi2_docker_fix.sh" ]; then
    echo "Fix scripts missing! Running setup to create them..."
    echo "Error: phi2_docker_fix.sh not found. Please run it manually first."
    echo "If you don't have this file, please create it or get it from the repository."
    exit 1
  fi
  
  # Run the fix script to ensure everything is set up
  echo "Applying Phi-2 model architecture fix..."
  ./phi2_docker_fix.sh

  echo "Using Phi-2 compatibility fixes to avoid 'unknown model architecture: phi2' error"
  # Create a temporary script to install compatible llama-cpp-python and fix model loading issue
  cat > docker_run_fix.sh << 'EOL'
#!/bin/bash
set -e
echo "====================================================="
echo "FIXING PHI-2 MODEL ARCHITECTURE ERROR"
echo "====================================================="
echo "Installing a compatible version of llama-cpp-python without model_type parameter..."
pip uninstall -y llama-cpp-python
# Specifically install an older version that doesn't validate model architecture
pip install --no-cache-dir llama-cpp-python==0.1.68

# Create a direct model loading script that doesn't use model architecture
cat > direct_model_loader.py << 'EOF'
#!/usr/bin/env python3
from llama_cpp import Llama
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)8s] %(name)s - %(message)s')
logger = logging.getLogger("direct_model_loader")

def load_model(model_path):
    """Load model without specifying architecture type"""
    logger.info(f"Loading model from: {model_path}")
    try:
        # Load with minimal parameters - no architecture specification
        model = Llama(
            model_path=model_path,
            n_ctx=512,
            n_batch=1,
            verbose=True
        )
        logger.info("Model loaded successfully!")
        return model
    except Exception as e:
        logger.error(f"Model loading error: {e}")
        return None

if __name__ == "__main__":
    model_path = "phi-2.Q4_K_M.gguf"
    model = load_model(model_path)
    if model:
        print("✓ Model test: Success!")
        result = model("Hello", max_tokens=5)
        print(result["choices"][0]["text"])
    else:
        print("✗ Model test: Failed!")
EOF

# Create a wrapper script that uses our direct loader
cat > run_without_arch.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import argparse
import time

def main():
    # Parse the original arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--document", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reference-file", required=True)
    parser.add_argument("--skip-scrape", action="store_true")
    
    args, unknown = parser.parse_known_args()
    
    # Set required environment variables
    os.environ["LANGCHAIN_TRACING"] = "false"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["SANDBOX_MODE"] = "true"
    
    # Force using the Docker-compatible mode
    os.environ["PHI2_COMPAT_MODE"] = "1"
    # Add direct model loading flag
    os.environ["USE_DIRECT_MODEL_LOADER"] = "1"
    
    # Test model loading first
    print("Testing direct model loading...")
    os.system("python3 direct_model_loader.py")
    
    # Construct command with all arguments
    cmd_args = []
    for arg, value in vars(args).items():
        if arg == "skip_scrape" and value:
            cmd_args.append("--skip-scrape")
        elif value is not None and arg != "skip_scrape":
            cmd_args.append(f"--{arg.replace('_', '-')} {value}")
    
    command = f"python3 run.py {' '.join(cmd_args)}"
    print(f"Executing: {command}")
    os.system(command)

if __name__ == "__main__":
    main()
EOF

chmod +x run_without_arch.py
echo "Ready to execute with compatibility wrapper"

# Run the original command with all arguments
exec "$@"
EOL

  chmod +x docker_run_fix.sh
  
  echo "Running in Docker with compatibility fixes for the phi-2 model architecture..."
  # Mount our fix script into the container
  docker run --network=none \
    -v "$CURRENT_DIR:/app" \
    -v "$ABS_MODEL_PATH:/app/$(basename $MODEL_PATH)" \
    -v "$ABS_FILE_PATH:/app/$(basename $FILE)" \
    -v "$ABS_OUTPUT_PATH:/app/$(basename $OUTPUT_FILE)" \
    -v "$CURRENT_DIR/phi2_docker_fix.sh:/app/phi2_docker_fix.sh" \
    -v "$CURRENT_DIR/direct_phi2_loader.py:/app/direct_phi2_loader.py" \
    -v "$CURRENT_DIR/docker_run_patch.py:/app/docker_run_patch.py" \
    -w /app \
    -e LANGCHAIN_TRACING=false \
    -e TRANSFORMERS_OFFLINE=1 \
    -e HF_HUB_OFFLINE=1 \
    -e PHI2_COMPAT_MODE=1 \
    -e USE_DIRECT_MODEL_LOADER=1 \
    --rm \
    llm-sandbox-phi2:latest \
    /bin/sh -c "chmod +x /app/phi2_docker_fix.sh && /app/phi2_docker_fix.sh && python3 run.py --document \"/app/$(basename $FILE)\" --subject \"$SUBJECT\" --id \"$ID\" --model \"/app/$(basename $MODEL_PATH)\" --reference-file \"/app/$(basename $OUTPUT_FILE)\" --skip-scrape"
else
  # Run without Docker (less secure, only environment variable isolation)
  echo "Running the main processing pipeline with Phi-2 model using environment variable isolation..."
  echo "Using local mode with offline environment variables"
  echo "Using model: $MODEL_PATH (NO mock fallback allowed)"

  # Set environment variables to enforce offline mode (same as in llm_sandbox.py)
  export LANGCHAIN_TRACING=false
  export TRANSFORMERS_OFFLINE=1
  export HF_HUB_OFFLINE=1
  export PHI2_COMPAT_MODE=1
  export USE_DIRECT_MODEL_LOADER=1
  
  echo "Setting model path: $MODEL_PATH"
  
  echo "================================================================================
 PHASE 2: SANDBOX PROCESSING (network-isolated environment)
================================================================================
Executing: python3 main.py --file \"$FILE\" --subject \"$SUBJECT\" --id \"$ID\" --model \"$MODEL_PATH\" --references \"$OUTPUT_FILE\""

  python3 run.py --document "$FILE" --subject "$SUBJECT" --id "$ID" --model "$MODEL_PATH" --reference-file "$OUTPUT_FILE" --skip-scrape
fi

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo " Processing completed successfully!"
  echo "Results saved to: data/result_${ID}.json"
  echo "Full OCR text saved to: data/ocr_text_${ID}.txt"
else
  echo " Processing failed - the Phi-2 model is required and no mock implementation is allowed."
  echo "Please ensure the Phi-2 model file exists and is valid."
  exit 1
fi

# Print completion timestamp
echo "Workflow completed at: $(date)"
