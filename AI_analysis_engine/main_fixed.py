"""
Fixed version of main.py with enhanced detection
"""
import os
import json
import argparse
import datetime
import logging
import socket
import re
import enhanced_detection
from ocr_processor import OCRProcessor
from llm_sandbox import SandboxedLLM
from llm_loader import load_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

class AssignmentValidator:
    def __init__(self, model_path, references_path="data/references.json"):
        # Initialize components
        self.model_path = model_path
        self.references_path = references_path
        
        # Load model
        self.llm = self._load_model()
        
        # Load references
        self.reference_sources = self._load_references()
        
        # Initialize OCR
        self.ocr = self._initialize_ocr()
    
    def _load_model(self):
        """Load the LLM model"""
        logger.info(f"Loading model from: {self.model_path}")
        try:
            return SandboxedLLM(self.model_path)
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def _load_references(self):
        """Load reference sources"""
        logger.info(f"Loading references from: {self.references_path}")
        try:
            with open(self.references_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading references: {e}")
            return []
    
    def _initialize_ocr(self):
        """Initialize OCR processor"""
        logger.info("Initializing OCR processor")
        try:
            return OCRProcessor(use_gpu=False, lang='en')
        except Exception as e:
            logger.error(f"Error initializing OCR: {e}")
            return None
    
    def process_assignment(self, file_path, subject, assignment_id):
        """Process an assignment file"""
        logger.info(f"Processing assignment: {assignment_id}")
        logger.info(f"Subject: {subject}")
        logger.info(f"File: {file_path}")
        
        # Create result structure
        result = {
            "subject": subject,
            "assignment_id": assignment_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "PROCESSING"
        }
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            result["status"] = "ERROR"
            result["error"] = "File not found"
            return result
        
        # Extract text with OCR
        try:
            logger.info("Extracting text with OCR")
            ocr_text = self.ocr.process_document(file_path)
            result["ocr_text_length"] = len(ocr_text)
            logger.info(f"Extracted {len(ocr_text)} characters")
        except Exception as e:
            logger.error(f"OCR error: {e}")
            result["status"] = "ERROR"
            result["error"] = f"OCR error: {str(e)}"
            return result
        
        # Check plagiarism
        try:
            logger.info("Checking plagiarism")
            plagiarism_results = self.llm.check_plagiarism(ocr_text, self.reference_sources)
            result["plagiarism_check"] = plagiarism_results
            
            # Get highest plagiarism score
            plagiarism_percentage = enhanced_detection.get_highest_plagiarism_score(plagiarism_results)
            logger.info(f"Highest plagiarism score: {plagiarism_percentage}%")
        except Exception as e:
            logger.error(f"Plagiarism check error: {e}")
            result["plagiarism_check"] = {"error": str(e), "plagiarism_percentage": 0}
            plagiarism_percentage = 0
        
        # Check relevance
        try:
            logger.info("Checking relevance")
            validation = enhanced_detection.check_relevance_with_models(ocr_text[:300], subject)
            result["content_validation"] = validation
            logger.info(f"Relevance score: {validation.get('relevance_score', 0)}%")
        except Exception as e:
            logger.error(f"Relevance check error: {e}")
            result["content_validation"] = {"error": str(e), "relevance_score": 0, "status": "ERROR"}
            validation = {"status": "ERROR", "relevance_score": 0}
        
        # Determine final status
        strict_mode = False
        try:
            if os.path.exists("data/info.json"):
                with open("data/info.json", "r") as f:
                    info = json.load(f)
                    strict_mode = info.get("strict_ai_detection", False)
        except:
            pass
        
        # Use lower thresholds in strict mode
        if strict_mode:
            plagiarism_threshold = 35
            relevance_threshold = 60
            logger.info("Using strict detection thresholds")
        else:
            plagiarism_threshold = 40
            relevance_threshold = 50
        
        # Check failure conditions
        failure_reasons = []
        
        if plagiarism_percentage > plagiarism_threshold:
            failure_reasons.append(f"High plagiarism detected ({plagiarism_percentage}%)")
        
        if validation.get("status") != "PASSED" or validation.get("relevance_score", 0) < relevance_threshold:
            failure_reasons.append(f"Content not sufficiently relevant to {subject}")
        
        # Set final status
        if not failure_reasons:
            result["status"] = "PASSED"
            logger.info("Assignment PASSED validation")
        else:
            result["status"] = "FAILED"
            result["failure_reason"] = failure_reasons[0]
            result["all_failure_reasons"] = failure_reasons
            logger.info(f"Assignment FAILED: {failure_reasons[0]}")
        
        # Save results
        try:
            output_file = f"data/result_{assignment_id}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
        
        return result

def main():
    parser = argparse.ArgumentParser(description="Assignment Validation")
    parser.add_argument("--file", required=True, help="Path to assignment file")
    parser.add_argument("--subject", required=True, help="Subject of the assignment")
    parser.add_argument("--id", required=True, help="Assignment ID")
    parser.add_argument("--model", default="models/phi-2.gguf", help="Path to LLM model")
    args = parser.parse_args()
    
    validator = AssignmentValidator(args.model)
    result = validator.process_assignment(args.file, args.subject, args.id)
    
    print("\n=== ASSIGNMENT VALIDATION RESULTS ===")
    print(f"Subject: {args.subject}")
    print(f"Assignment ID: {args.id}")
    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Plagiarism: {result.get('plagiarism_check', {}).get('plagiarism_percentage', 0)}%")
    print(f"Relevance: {result.get('content_validation', {}).get('relevance_score', 0)}/100")
    
    if "failure_reason" in result:
        print(f"\nFailure reason: {result['failure_reason']}")

if __name__ == "__main__":
    main()