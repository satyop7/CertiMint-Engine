# CertiMint-Engine
Our video demo : 
(./Untitled video - Made with Clipchamp (1).mp4)


# Assignment Validation System

An intelligent system for validating academic assignments, detecting plagiarism, AI-generated content, and verifying subject relevance.

## Overview

This system provides a complete workflow for validating academic assignments through the following processes:
1. Reference collection via Wikipedia scraping for the specified subject
2. OCR processing of assignment documents (PDF format)
3. Advanced plagiarism detection using multiple techniques
4. AI-generated content detection using pattern recognition
5. Subject relevance validation using keyword analysis
6. Comprehensive result reporting and MongoDB storage

## System Architecture

The system operates in two distinct phases:
1. **Data Collection Phase** (internet access enabled): Web scraping for reference content
2. **Processing Phase** (network isolated/sandbox): OCR extraction, plagiarism checking, and content validation

!

## Enhanced Plagiarism Detection

The system includes advanced AI-generated content detection featuring:

- **Multi-layered detection**: Combines semantic similarity, LLM assessment, and pattern recognition
- **AI Pattern Detection**: Identifies common patterns in AI-generated text such as:
  - Self-references ("As an AI language model...")
  - Formulaic structures (pros/cons, numbered points)
  - Awkward or repetitive phrasing
  - Balanced perspectives ("on one hand... on the other hand")
  - Uniform paragraph structure
- **Strict thresholds**: 
  - Semantic similarity > 40% triggers failure (down from 50%)
  - LLM similarity > 35% triggers failure (down from 40%)
  - Any emoji detection triggers immediate failure
  - Any AI pattern detection triggers immediate failure

### Using the Enhanced Workflow

The recommended way to check assignments is to use our consolidated workflow script:

```bash
./workflow.sh -
```

This script provides:
- Complete reference collection from Wikipedia
- Enhanced AI-generated content detection
- Multiple plagiarism detection mechanisms
- Network isolation for security
- Comprehensive and colorized results summary

Full options:
```
Options:
  --file, -f FILE       PDF file to check (required)
  --subject, -s SUBJECT Subject of the assignment (default: 'Artificial Intelligence')
  --id ID               Assignment ID (generated from filename if not provided)
  --max-results N       Maximum number of references to collect (default: 10)
  --timeout N           Timeout in seconds for web scraping (default: 60)
  --model, -m PATH      Path to the Phi-2 model file (default: phi-2.Q4_K_M.gguf)
  --download-model      Download the model if it doesn't exist (default: false)
  --use-docker, -d      Use Docker for isolation (default: false)
  --skip-scrape         Skip Wikipedia scraping and use existing references.json
  --verbose, -v         Show detailed logging information
```


## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Install system dependencies (for Ubuntu/Debian):
```bash
apt-get update && apt-get install -y poppler-utils chromium-browser
```
4. Download the Phi-2 LLM model:
```bash
wget https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf -O phi-2.Q4_K_M.gguf
```

## Usage

### Basic Workflow

There are two ways to run the workflow:

#### Option 1: Using the run_workflow.sh Script

```bash
# Make the script executable
chmod +x run_workflow.sh

# Run with default parameters (will use data/sample.pdf)
./workflow.sh

# Run with custom parameters
./run_workflow.sh --subject "Mathematics" --file data/sample1.pdf --id MATH12345 --max-results 10 --timeout 300
```

#### Option 2: Using the run.py Python Script

```bash
# Make the script executable
chmod +x run.py

# Run the entire workflow (scraping + sandbox processing)
./run.py --subject "Computer Science" --document data/sample.pdf --id ASG12345
```

### Advanced Usage

You can also run each component separately:

```bash
# Step 1: Only run web scraping with custom parameters
python web_scraper.py --subject "Mathematics" --output data/math_references.json --max-results 10

# Step 2: Only run processing in sandbox with pre-scraped references
python main.py --file data/sample.pdf --subject "Mathematics" --id MATH12345 --references data/math_references.json
```

### Handling Failures

The system is designed to be robust:

- If web scraping fails, the system will attempt to use existing reference data or create mock references
- If the OCR process fails, it will fall back to a simplified OCR implementation
- If the LLM model is unavailable or fails to load, it will use a mock LLM implementation
- Timeouts are implemented to prevent the process from hanging

### API Server

The system can also be deployed as an API server:

```bash
python api_server.py
```

## Sandbox Security

The system implements multiple layers of security to ensure complete network isolation during the LLM processing phase:

### Network Isolation Mechanisms

1. **Docker Network Isolation**: The container runs with `--network=none` flag for complete network isolation
2. **Environment Variables**: Force libraries to operate in offline mode
3. **Network Monitoring**: Active tcpdump monitoring tracks any unauthorized network activity
4. **Isolation Verification**: Socket connection tests at startup verify proper isolation
5. **Clear Security Alerts**: Immediate warnings if any isolation breach is detected

### Test Environment Setup

For testing without Docker, use environment variables to simulate sandbox:
```bash
export SANDBOX_MODE=true
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
```

### Production Deployment

For production, the system enforces Docker with network isolation:
```bash
# Build the Docker image
docker build -t llama-sandbox .

# Run with default parameters (network isolation is enforced)
docker run --network=none -v $(pwd)/data:/app/data -v $(pwd)/models:/app/models llama-sandbox

# Run with custom parameters
docker run --network=none \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  llama-sandbox python main.py \
  --file data/sample.pdf --subject "Computer Science" --id ASG12345

# Run the workflow script (automatically enforces network isolation in sandbox phase)
docker run \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  llama-sandbox ./run_workflow.sh --file data/sample.pdf --subject "Computer Science"
```

**Note**: In production, you should run only the sandbox processing phase in the Docker container with `--network=none`. The web scraping phase should be done separately outside the container, with its results mounted into the container.

## Files and Directory Structure

- `run.py`: Main workflow script that orchestrates both phases
- `web_scraper.py`: Collects reference content from the web
- `ocr_processor.py`: Extracts text from PDFs and images
- `llm_sandbox.py`: Performs sandboxed LLM analysis
- `main.py`: Orchestrates the validation process
- `api_server.py`: FastAPI server for web interface
- `Dockerfile`: Container definition for isolated execution
- `models/`: Directory for storing LLM models
- `data/`: Directory for storing reference data and results

## Output Format

Results are saved as JSON files with the following structure:

```json
{
  "subject": "history",
  "assignment_id": "Vicky_202506241137",
  "timestamp": "2025-06-24T11:37:27.432288",
  "sandbox_mode": true,
  "status": "FAILED",
  "ocr_text_preview": "Assignment on Artificial Intelligence Author: Sambhranta Ghosh Artificial Intelligence (Al) is a rapidly advancing field that involves the simulation of human intelligence in machines. Al systems are ...",
  "ocr_text_length": 1312,
  "plagiarism_check": {
    "plagiarism_detected": true,
    "plagiarism_percentage": 66.35512081582458,
    "ai_patterns_detected": false,
    "ai_confidence": 12.482437721561968,
    "ai_patterns": {
      "explicit_patterns": [],
      "feature_scores": {
        "paragraph_consistency": 15.926493108728945,
        "sentence_variety": 63.52419512002124,
        "lexical_diversity": 69.18604651162791,
        "repetitive_patterns": 0,
        "structural_patterns": 0
      }
    },
    "semantic_similarity": 0,
    "statistical_similarity": 62.80425489231134,
    "ngram_similarity": 0,
    "emoji_detected": false,
    "emoji_count": 0,
    "emoji_list": [],
    "top_features_score": 66.35512081582458,
    "subject_mismatch": true
  },
  "content_validation": {
    "status": "FAILED",
    "relevance_score": 10,
    "comments": "Document contains 'artificial intelligence' which is unrelated to history"
  },
  "ai_detection": {
    "ai_patterns_detected": false,
    "ai_confidence": 12.482437721561968,
    "patterns": {
      "explicit_patterns": [],
      "feature_scores": {
        "paragraph_consistency": 15.926493108728945,
        "sentence_variety": 63.52419512002124,
        "lexical_diversity": 69.18604651162791,
        "repetitive_patterns": 0,
        "structural_patterns": 0
      }
    }
  },
  "failure_reason": "Subject-content mismatch: Paper claims to be about 'history' but contains content about 'unknown' - clear indication of AI-generated content",
  "all_failure_reasons": [
    "Subject-content mismatch: Paper claims to be about 'history' but contains content about 'unknown' - clear indication of AI-generated content",
    "High plagiarism detected (66.35512081582458%)"
  ],
  "username": "Vicky"
}
```

## Using the Wikipedia Scraper

The project includes a dedicated Wikipedia scraper for retrieving high-quality reference information:

```bash
# Basic usage
python wikipedia_scraper.py --query "Machine Learning" --max-results 3

# Show the browser window (non-headless mode)
python wikipedia_scraper.py --query "Artificial Intelligence" --no-headless

# Custom output location
python wikipedia_scraper.py --query "Computer Science" --output data/my_results.json
```

The Wikipedia scraper will:
1. Search for your query on Wikipedia
2. Process either direct article matches or search results
3. Extract article content, introductions, and infobox data
4. Save comprehensive results to a JSON file


