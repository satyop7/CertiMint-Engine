#!/usr/bin/env python3
import os
import sys
import json
import argparse
import datetime
import subprocess
from pathlib import Path

def execute_command(command, env=None):
    """Execute a shell command and return the output"""
    try:
        print(f"Executing: {command}")
        result = subprocess.run(command, shell=True, check=True, 
                               text=True, capture_output=True, env=env)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        print(f"Error output: {e.stderr}")
        return None

def scrape_phase(subject, sample_file=None, reference_file="data/references.json", max_results=10):
    """Run the web scraping phase with internet access"""
    print("\n" + "="*80)
    print(" PHASE 1: WEB SCRAPING (internet-enabled environment)")
    print("="*80)
    
    command = f"python3 web_scraper.py --subject \"{subject}\" --output \"{reference_file}\" --max-results {max_results}"
    if sample_file:
        command += f" --sample \"{sample_file}\""
    
    output = execute_command(command)
    
    # Verify that references were created
    if os.path.exists(reference_file):
        try:
            with open(reference_file, 'r') as f:
                references = json.load(f)
            print(f"\n✓ Successfully gathered {len(references)} reference sources for subject: {subject}")
            return True
        except json.JSONDecodeError:
            print(f"Error: Reference file exists but contains invalid JSON")
            return False
    else:
        print(f"Error: Web scraping phase failed - {reference_file} not created")
        return False

def sandbox_phase(subject, document_file, assignment_id, reference_file="data/references.json", model_path="models/llama-3-8b-instruct.gguf"):
    """Run the LLM validation phase in a sandboxed environment with no internet access"""
    print("\n" + "="*80)
    print(" PHASE 2: SANDBOX PROCESSING (network-isolated environment)")
    print("="*80)
    
    # Check if files exist
    if not os.path.exists(document_file):
        print(f"Error: Document file not found: {document_file}")
        return False
    
    if not os.path.exists(reference_file):
        print(f"Error: Reference file not found: {reference_file}")
        print("Please run the web scraping phase first")
        return False
    
    # In production, use Docker with --network=none
    # For testing, we'll use environment variables to simulate sandbox
    env = os.environ.copy()
    env["SANDBOX_MODE"] = "true"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    env["LANGCHAIN_TRACING"] = "false"
    
    command = f"python3 main.py --file \"{document_file}\" --subject \"{subject}\" --id \"{assignment_id}\" --model \"{model_path}\" --references \"{reference_file}\""
    
    # For production, uncomment this and comment the above command:
    # command = f"docker run --network=none -v $(pwd):/app llama-sandbox python3 main.py --file {document_file} --subject \"{subject}\" --id \"{assignment_id}\""
    
    output = execute_command(command, env=env)
    
    result_file = f"data/result_{assignment_id}.json"
    if os.path.exists(result_file):
        print(f"\n✓ Processing complete! Results saved to: {result_file}")
        
        # Display a summary of the results
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            print("\n=== VALIDATION RESULTS ===")
            print(f"Status: {result.get('status', 'UNKNOWN')}")
            
            # Plagiarism information
            plagiarism_check = result.get('plagiarism_check', {})
            print(f"Plagiarism: {plagiarism_check.get('plagiarism_percentage', 0)}%")
            
            if plagiarism_check.get('llm_similarity', 0) > 0:
                print(f"LLM-detected similarity: {plagiarism_check.get('llm_similarity', 0)}%")
                
            if plagiarism_check.get('emoji_detected', False):
                emoji_count = plagiarism_check.get('emoji_count', 0)
                print(f"Emoji usage: {emoji_count} emojis found")
                emoji_list = plagiarism_check.get('emoji_list', [])
                if emoji_list:
                    print(f"Sample emojis: {' '.join(emoji_list[:5])}")
            
            # Relevance information
            print(f"Relevance: {result.get('content_validation', {}).get('relevance_score', 0)}/100")
            print(f"Comments: {result.get('content_validation', {}).get('comments', 'No comments')}")
            
            if result.get('status') == 'FAILED':
                print(f"\nFailure reason: {result.get('failure_reason', 'Unknown')}")
                all_reasons = result.get('all_failure_reasons', [])
                if len(all_reasons) > 1:
                    print("All failure reasons:")
                    for i, reason in enumerate(all_reasons, 1):
                        print(f"  {i}. {reason}")
            
            return True
        except json.JSONDecodeError:
            print(f"Error: Result file exists but contains invalid JSON")
            return False
    else:
        print(f"Error: Processing failed - {result_file} not created")
        return False

def main():
    parser = argparse.ArgumentParser(description="Assignment Validation Workflow")
    parser.add_argument("--subject", required=True, help="Subject of the assignment (e.g., 'Computer Science')")
    parser.add_argument("--document", required=True, help="Path to document file (PDF or image)")
    parser.add_argument("--id", default=None, help="Assignment ID (default: auto-generated)")
    parser.add_argument("--reference-file", default="data/references.json", help="Path for reference data JSON file")
    parser.add_argument("--model", default="models/llama-3-8b-instruct.gguf", help="Path to LLM model file")
    parser.add_argument("--sample", default=None, help="Sample text file to extract keywords from")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of sources to scrape")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip the web scraping phase")
    
    args = parser.parse_args()
    
    # Create needed directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # Auto-generate assignment ID if not provided
    if not args.id:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        args.id = f"ASG{timestamp}"
    
    if not args.skip_scrape:
        if not scrape_phase(args.subject, args.sample, args.reference_file, args.max_results):
            print("Web scraping phase failed. Exiting workflow.")
            sys.exit(1)
    else:
        print("Skipping web scraping phase as requested.")
    
    sandbox_result = sandbox_phase(args.subject, args.document, args.id, args.reference_file, args.model)
    if not sandbox_result:
        print("Sandbox processing phase failed.")
        sys.exit(2)
    
    print("\nWorkflow completed successfully!")

if __name__ == "__main__":
    main()
