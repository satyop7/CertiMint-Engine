"""
Run the assignment validation with our enhanced detection
"""
import os
import json
import logging
from main import AssignmentValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_validation')

def run_validation():
    """Run the assignment validation"""
    # Load info.json
    with open('data/info.json', 'r') as f:
        info = json.load(f)
    
    subject = info.get('subject_name', 'Chemistry')
    assignment_id = info.get('assignmentID', 'Vicky_202506261947')
    file_name = info.get('File_name', '115761336171248824586_Introduction_to_Quantum_Mechanics.pdf')
    file_path = f"data/{file_name}"
    
    # Print validation header
    print("=" * 80)
    print(f"ASSIGNMENT VALIDATION")
    print("=" * 80)
    print(f"Subject: {subject}")
    print(f"File: {file_path}")
    print(f"Assignment ID: {assignment_id}")
    print(f"Detection mode: {'strict' if info.get('strict_ai_detection', False) else 'standard'}")
    print("Using Groq API for content validation")
    print("-" * 80)
    
    # Initialize validator
    model_path = "models/llama-3-8b-instruct.gguf"
    if not os.path.exists(model_path):
        model_path = "models/phi-2.gguf"  # Fallback model
    
    validator = AssignmentValidator(model_path)
    
    # Run validation
    result = validator.process_assignment(file_path, subject, assignment_id)
    
    # Print results
    print("\nRESULTS:")
    print("-" * 80)
    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Plagiarism: {result.get('plagiarism_check', {}).get('plagiarism_percentage', 0)}%")
    print(f"Relevance: {result.get('content_validation', {}).get('relevance_score', 0)}/100")
    print(f"Comments: {result.get('content_validation', {}).get('comments', 'No comments')}")
    
    if "failure_reason" in result:
        print(f"\nFailure reason: {result['failure_reason']}")
    
    print("\nTop repetitive phrases:")
    repetitive_phrases = result.get('content_validation', {}).get('repetitive_phrases', [])
    for phrase, count in repetitive_phrases[:3]:
        print(f"- {phrase} ({count} occurrences)")
    
    print("\nModel scores:")
    print(f"- Phi score: {result.get('content_validation', {}).get('phi_score', 0)}%")
    print(f"- Groq score: {result.get('content_validation', {}).get('groq_score', 0)}%")
    
    print("=" * 80)
    return result

if __name__ == "__main__":
    run_validation()