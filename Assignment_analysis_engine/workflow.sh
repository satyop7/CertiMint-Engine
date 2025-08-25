#!/bin/bash
# Assignment Validation Workflow
# This script provides a complete workflow for validating academic assignments:
# 1. Reference collection via Wikipedia scraping for the subject
# 2. OCR processing of the assignment document
# 3. Plagiarism detection, AI-content detection, and relevance assessment
# 4. Comprehensive result reporting

set -e  # Exit on error

# Default 
SUBJECT="Engineering"
FILE="None"
ID=""
MAX_RESULTS=10
TIMEOUT=60

MODEL_PATH="phi-2.Q4_K_M.gguf"  
DOWNLOAD_MODEL=false 
HF_TOKEN=""
USE_DOCKER=false  
DETECTION_MODE="strict" 
INFO_JSON="data/info.json"
RESULTS_DIR="result"


# Create necessary directories
mkdir -p data uploads "$RESULTS_DIR"

# Setup validators and required modules
echo "Setting up validator components..."
python3 setup_validators.py
if [ $? -ne 0 ]; then
  echo "Warning: Some validator components could not be setup correctly"
  echo "The system will fall back to basic detection methods"
fi

# Check if info.json exists and use its values
if [ -f "$INFO_JSON" ]; then
  echo "Reading configuration from $INFO_JSON..."
  
  # Extract values from info.json using Python
  JSON_VALUES=$(python3 -c "
import json
import os
try:
    with open('$INFO_JSON', 'r') as f:
        data = json.load(f)
    
    file_name = data.get('File_name', '')
    subject_name = data.get('subject_name', '').strip()
    username = data.get('username', 'unknown')
    
    # Ensure file exists in data folder
    file_path = os.path.join('data', file_name)
    if os.path.exists(file_path):
        print(f'{file_path}|{subject_name}|{username}')
    else:
        print(f'ERROR: File {file_name} not found in data folder')
except Exception as e:
    print(f'ERROR: {str(e)}')
")

  # Process the extracted values
  if [[ $JSON_VALUES == ERROR:* ]]; then
    echo "${JSON_VALUES}"
  else
    # Split the returned string by pipe character
    IFS='|' read -r FILE SUBJECT USERNAME <<< "$JSON_VALUES"
    echo "Using file: $FILE"
    echo "Using subject: $SUBJECT"
    echo "Username: $USERNAME"
    
    # Generate ID using username and timestamp
    ID="${USERNAME}_$(date +%Y%m%d%H%M)"
  fi
fi

print_banner() {
  echo "================================================================================"
  echo "$1"
  echo "================================================================================"
}

print_section() {
  echo ""
  echo "--------------------------------------------------------------------------------"
  echo "$1"
  echo "--------------------------------------------------------------------------------"
}

# Process command-line arguments
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
    # Removed --skip-scrape option - references.json will always be regenerated
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
    --mode)
      DETECTION_MODE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Assignment Validation Workflow - Academic Integrity Assessment Tool"
      echo ""
      echo "Options:"
      echo "  --subject        Subject for Wikipedia reference collection (default: Engineering)"
      echo "  --file           Path to the PDF file to analyze (required)"
      echo "  --id             Assignment ID (default: auto-generated from date and time)"
      echo "  --max-results    Maximum number of Wikipedia references (default: 10)"
      echo "  --timeout        Timeout for Wikipedia scraping in seconds (default: 60)"
      echo "  --model          Path to the LLM model file (default: phi-2.Q4_K_M.gguf)"
      echo "  --download-model Download the model if it doesn't exist (default: false)"
      echo "  --hf-token       Hugging Face token for model download (if needed)"
      echo "  --use-docker     Use Docker for running the workflow (default: false)"
      echo "  --mode           Detection mode: 'strict' or 'standard' (default: strict)"
      echo ""
      echo "Example:"
      echo "  $0 --file assignment.pdf --subject \"Computer Science\""
      echo ""
      exit 0
      ;;
    *)
      echo "Error: Unknown option: $1"
      echo "Use --help for usage information."
      exit 1
      ;;
  esac
done

# Generate ID if not provided
if [ -z "$ID" ]; then
  ID="ASG$(date +%Y%m%d%H%M)"
fi

# Validate file input
if [ "$FILE" = "None" ]; then
  echo "Error: No file specified in arguments or info.json"
  echo "Please provide a valid file path with --file option or update info.json"
  exit 1
elif [ ! -f "$FILE" ]; then
  echo "Error: File not found: $FILE"
  echo "Please provide a valid file path with --file option or update info.json"
  exit 1
fi

# Check model file
if [ ! -f "$MODEL_PATH" ]; then
  print_section "CHECKING MODEL FILE"
  echo "Model not found at: $MODEL_PATH"
  
  if [ "$DOWNLOAD_MODEL" = true ]; then
    echo "Attempting to download the model..."
    
    MODEL_DIR=$(dirname "$MODEL_PATH")
    mkdir -p "$MODEL_DIR"
    
    if ! command -v huggingface-cli &> /dev/null; then
      echo "huggingface-cli not found. Please install it with: pip install huggingface_hub"
      echo "Then try again, or download the model manually."
      exit 1
    fi
    
    if [ ! -z "$HF_TOKEN" ]; then
      export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
      echo "Using provided Hugging Face token for authentication"
    fi
    
    # Download using huggingface-cli
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
  print_section "USING EXISTING PHI-2 MODEL"
  echo "Found model at: $MODEL_PATH"
fi

OUTPUT_FILE="data/references.json"

# PHASE 1: Reference Collection
# Always regenerate references.json
print_banner "PHASE 1: REFERENCE COLLECTION"
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

echo "Using reference data from: $OUTPUT_FILE"

# Format reference data
echo "Formatting reference data for processing..."
python3 -c "
import json
with open('$OUTPUT_FILE', 'r') as f:
    wiki_data = json.load(f)
formatted_data = []
for item in wiki_data:
    # Build a comprehensive content string with all available data
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

print(f'Successfully formatted {len(formatted_data)} reference articles')

# Print summary of the scraped data
for i, item in enumerate(formatted_data):
    title = item.get('title', 'Unknown title')
    url = item.get('url', 'No URL')
    content = item.get('content', '')
    content_preview = content[:100] + '...' if len(content) > 100 else content
    print(f'\\nArticle {i+1}: {title}')
    print(f'Source: {url}')
"

# PHASE 2: Document Processing and Analysis
print_banner "PHASE 2: ASSIGNMENT VALIDATION"
echo "Subject: $SUBJECT"
echo "File: $FILE"
echo "Assignment ID: $ID"
echo "Detection mode: $DETECTION_MODE"

# Set environment variables for offline operation
export LANGCHAIN_TRACING=false
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export SANDBOX_MODE=true

# Set detection mode
if [ "$DETECTION_MODE" = "strict" ]; then
  export STRICT_DETECTION=1
  echo "Using strict detection thresholds for AI-generated content"
else
  export STRICT_DETECTION=0
  echo "Using standard detection thresholds"
fi

# Check if Docker should be used
if [ "$USE_DOCKER" = true ]; then
  print_section "RUNNING IN DOCKER CONTAINER"
  
  # Get absolute paths for Docker volume mounts
  CURRENT_DIR=$(pwd)
  ABS_MODEL_PATH=$(realpath $MODEL_PATH)
  ABS_FILE_PATH=$(realpath $FILE)
  ABS_OUTPUT_PATH=$(realpath $OUTPUT_FILE)
  
  # Check if Docker image exists, build if needed
  if ! docker image inspect llm-sandbox-phi2:latest &>/dev/null; then
    echo "Docker image not found. Building image first..."
    ./docker_setup.sh
  fi
  
  # Apply Phi-2 compatibility fix for Docker
  echo "Applying Phi-2 model architecture fix for Docker..."
  if [ -f "phi2_compatibility_fix.sh" ]; then
    ./phi2_compatibility_fix.sh
  else
    echo "Warning: phi2_compatibility_fix.sh not found. Docker may encounter model architecture errors."
  fi
  
  # Run the command in Docker with network isolation
  echo "Running in network-isolated Docker container..."
  docker run --network=none \
    -v "$CURRENT_DIR:/app" \
    -v "$ABS_MODEL_PATH:/app/$(basename $MODEL_PATH)" \
    -v "$ABS_FILE_PATH:/app/$(basename $FILE)" \
    -v "$ABS_OUTPUT_PATH:/app/$(basename $OUTPUT_FILE)" \
    -e LANGCHAIN_TRACING=false \
    -e TRANSFORMERS_OFFLINE=1 \
    -e HF_HUB_OFFLINE=1 \
    -e SANDBOX_MODE=true \
    -e STRICT_DETECTION=$STRICT_DETECTION \
    -e PHI2_COMPAT_MODE=1 \
    --rm \
    llm-sandbox-phi2:latest \
    python3 main.py --file "/app/$(basename $FILE)" --subject "$SUBJECT" --id "$ID" --model "/app/$(basename $MODEL_PATH)" --references "/app/$(basename $OUTPUT_FILE)"
else
  # Run locally with environment variable isolation
  print_section "RUNNING LOCALLY WITH ENVIRONMENT ISOLATION"
  
  # Set environment variables for Phi-2 compatibility
  export PHI2_COMPAT_MODE=1
  
  echo "Running validation with Phi-2 model..."
  python3 main.py --file "$FILE" --subject "$SUBJECT" --id "$ID" --model "$MODEL_PATH" --references "$OUTPUT_FILE"
fi

# Check if the command was successful
if [ $? -eq 0 ]; then
  # PHASE 3: Present Results
  print_banner "PHASE 3: VALIDATION RESULTS"
  echo "Processing completed successfully!"
  
  # Original result files
  RESULT_FILE="data/result_${ID}.json"
  OCR_FILE="data/ocr_text_${ID}.txt"
  
  # Destination files in results directory with username included
  DEST_RESULT_FILE="${RESULTS_DIR}/result_${USERNAME}_${ID}.json"
  DEST_OCR_FILE="${RESULTS_DIR}/ocr_text_${USERNAME}_${ID}.txt"
  
  if [ -f "$RESULT_FILE" ]; then
    # Add username to the JSON result file
    echo "Adding username to result JSON..."
    python3 -c "
import json
import os

result_file = '$RESULT_FILE'
username = '$USERNAME'
dest_result_file = '$DEST_RESULT_FILE'

try:
    with open(result_file, 'r') as f:
        result_data = json.load(f)
    
    # Add username to the result data
    result_data['username'] = username
    
    # Write the modified result to the destination file
    with open(dest_result_file, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    print(f'Username \"{username}\" added to result JSON')
except Exception as e:
    print(f'Error updating result JSON: {e}')
    # If error, just copy the file without modification
    import shutil
    shutil.copy(result_file, dest_result_file)
"
    # Copy OCR file to destination
    cp "$OCR_FILE" "$DEST_OCR_FILE"
    
    echo "Results saved to: $DEST_RESULT_FILE (Username: $USERNAME)"
    echo "OCR text saved to: $DEST_OCR_FILE (Username: $USERNAME)"
    
    # Display summarized results
    python3 -c "
import json
import os

result_file = '$RESULT_FILE'
username = '$USERNAME'
if os.path.exists(result_file):
    try:
        with open(result_file, 'r') as f:
            result = json.load(f)
        
        print('\\n=== SUMMARY ===')
        print(f'Overall Status: {result.get(\"status\", \"UNKNOWN\")}')
        print(f'Username: {result.get(\"username\", \"$USERNAME\")}')
        print(f'Subject: {result.get(\"subject\", \"Unknown\")}')
        print(f'Document ID: {result.get(\"id\", \"Unknown\")}')
        
        # Display plagiarism results
        plagiarism_check = result.get('plagiarism_check', {})
        print(f'\\n=== PLAGIARISM CHECK ===')
        print(f'Semantic Similarity: {plagiarism_check.get(\"plagiarism_percentage\", 0):.1f}%')
        print(f'LLM Similarity: {plagiarism_check.get(\"llm_similarity\", 0):.1f}%')
        
        # Check for emoji usage
        if plagiarism_check.get('emoji_detected', False):
            emoji_count = plagiarism_check.get('emoji_count', 0)
            emoji_list = plagiarism_check.get('emoji_list', [])
            print(f'Emoji Usage: {emoji_count} emojis detected')
            if emoji_list:
                print(f'Sample Emojis: {\", \".join(emoji_list[:5])}')
        
        # Check for AI patterns
        if plagiarism_check.get('ai_patterns_detected', False):
            ai_patterns = plagiarism_check.get('ai_patterns', [])
            if isinstance(ai_patterns, dict):
                # Handle the case where ai_patterns is a dictionary
                patterns_list = ai_patterns.get('patterns', [])
                print(f'AI Patterns: {len(patterns_list)} patterns detected')
                for i, pattern in enumerate(patterns_list[:3], 1):
                    print(f'  {i}. {pattern}')
            elif isinstance(ai_patterns, list):
                # Handle the case where ai_patterns is a list
                print(f'AI Patterns: {len(ai_patterns)} patterns detected')
                for i, pattern in enumerate(ai_patterns[:3], 1):
                    print(f'  {i}. {pattern}')
        
        # Display content validation
        content_validation = result.get('content_validation', {})
        print(f'\\n=== CONTENT VALIDATION ===')
        print(f'Relevance Score: {content_validation.get(\"relevance_score\", 0):.1f}%')
        print(f'Status: {content_validation.get(\"status\", \"Unknown\")}')
        print(f'Comments: {content_validation.get(\"comments\", \"No comments\")}')
        
        # Display failure reasons if any
        if result.get('status') == 'FAILED':
            print('\\n=== FAILURE REASONS ===')
            
            # Primary failure reason
            main_reason = result.get('failure_reason')
            if main_reason:
                print(f'- {main_reason}')
            
            # Additional failure reasons
            all_reasons = result.get('all_failure_reasons', [])
            if all_reasons and (not main_reason or len(all_reasons) > 1):
                for reason in all_reasons:
                    if reason != main_reason:
                        print(f'- {reason}')
        
        print('\\n=== END OF REPORT ===')
    except Exception as e:
        print(f'Error processing results: {e}')
        import traceback
        traceback.print_exc()
else:
    print(f'Result file not found: {result_file}')
"
  else
    echo "Warning: Result file not found: $RESULT_FILE"
  fi
else
  print_banner "PROCESSING FAILED"
  echo "The validation process encountered an error."
  echo "Please check the logs above for more information."
  exit 1
fi

# Print completion timestamp
print_banner "WORKFLOW COMPLETED: $(date)"

# Ensure pymongo is installed for database upload
if ! python3 -c "import pymongo" &> /dev/null; then
  print_section "INSTALLING REQUIRED PACKAGES"
  echo "Installing pymongo for database upload..."
  pip install pymongo[srv] --quiet
fi

# Clean up data directory
print_section "CLEANING UP DATA DIRECTORY"
echo "Cleaning up all files from data directory except info.json..."

# Keep only info.json in the data directory
find data -type f ! -name "info.json" -exec rm -f {} \;
echo "✓ Data directory cleaned - only info.json remains"

echo "Results are available in the $RESULTS_DIR directory for future reference."
echo "Initializing database connection and uploading results to MongoDB..."

# Upload result to MongoDB
python3 -c "
import json
import os
import pymongo
from pymongo import MongoClient
import datetime

# MongoDB connection string
connection_string = 'mongodb+srv://sambhranta1123:SbGgIK3dZBn9uc2r@cluster0.jjcc5or.mongodb.net/'
db_name = 'certimint'
collection_name = 'assignments'

result_file = '$DEST_RESULT_FILE'
username = '$USERNAME'

try:
    # Connect to MongoDB
    print('Connecting to MongoDB...')
    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]
    
    # Load result JSON
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            result_data = json.load(f)
        
        # Add upload timestamp
        result_data['upload_timestamp'] = datetime.datetime.now().isoformat()
        
        # Insert document into MongoDB
        print('Uploading result to MongoDB...')
        insert_result = collection.insert_one(result_data)
        
        print(f'Successfully uploaded result to MongoDB (Document ID: {insert_result.inserted_id})')
    else:
        print(f'Error: Result file not found: {result_file}')
    
except Exception as e:
    print(f'Error uploading to MongoDB: {e}')
    import traceback
    traceback.print_exc()
"

