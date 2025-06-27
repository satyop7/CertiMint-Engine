"""
Sandbox analysis: Advanced plagiarism detection with actual Phi LLM
"""
import json
import datetime
import logging
from sandbox_config import configure_offline_sandbox
from advanced_plagiarism_algorithms import calculate_advanced_plagiarism
from content_relevance import check_groq_word_relevance, calculate_final_relevance
from phi_llm_integration import PhiLLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sandbox')

def run_sandbox_analysis():
    """Run analysis inside sandbox with actual Phi LLM"""
    
    # Configure offline sandbox
    configure_offline_sandbox()
    
    # Load pre-processed data
    with open('data/pre_processed.json', 'r') as f:
        pre_data = json.load(f)
    
    info = pre_data['info']
    ocr_text = pre_data['ocr_text']
    scraped_content = pre_data['scraped_content']
    groq_words = pre_data['groq_words']
    
    subject = info['subject_name']
    assignment_id = info['assignmentID']
    username = info['username']
    
    logger.info(f"Running sandbox analysis for: {assignment_id}")
    
    # Initialize Phi LLM
    logger.info("Initializing Phi LLM in sandbox")
    phi_llm = PhiLLM()
    
    # Advanced plagiarism detection
    logger.info("Running advanced plagiarism detection")
    plagiarism_results = calculate_advanced_plagiarism(ocr_text, scraped_content['content'], groq_words)
    
    # Content relevance using actual Phi LLM
    logger.info("Checking content relevance with Phi LLM")
    groq_relevance = check_groq_word_relevance(ocr_text, groq_words)
    phi_relevance = phi_llm.check_content_relevance(ocr_text[:300], subject)
    final_relevance = calculate_final_relevance(groq_relevance, phi_relevance)
    
    # Check for subject mismatch
    subject_mismatch = subject.lower() not in ocr_text.lower()
    
    # Determine status
    strict_mode = info.get('strict_ai_detection', False)
    plagiarism_threshold = 35.0 if strict_mode else 40.0
    relevance_threshold = 60.0 if strict_mode else 50.0
    
    failure_reasons = []
    
    # Check subject mismatch first (highest priority)
    if subject_mismatch:
        failure_reasons.append(f"Subject-content mismatch: Paper claims to be about '{subject}' but contains content about 'unknown' - clear indication of AI-generated content")
    
    if plagiarism_results['plagiarism_percentage'] > plagiarism_threshold:
        failure_reasons.append(f"High plagiarism detected ({plagiarism_results['plagiarism_percentage']}%)")
    
    if plagiarism_results['ai_confidence'] > 40.0:
        failure_reasons.append("AI-generated content patterns detected - assignment fails academic integrity check")
    
    if final_relevance < relevance_threshold:
        failure_reasons.append(f"Content not sufficiently relevant to {subject} ({final_relevance}%)")
    
    status = "PASSED" if not failure_reasons else "FAILED"
    
    # Create result matching the response format
    result = {
        "subject": subject,
        "assignment_id": assignment_id,
        "username": username,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": status,
        "sandbox_mode": True,
        "ocr_text_length": len(ocr_text),
        "ocr_text_preview": ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text,
        "plagiarism_check": {
            "plagiarism_detected": plagiarism_results['plagiarism_percentage'] > plagiarism_threshold,
            "plagiarism_percentage": plagiarism_results['plagiarism_percentage'],
            "ai_patterns_detected": plagiarism_results['ai_confidence'] > 40.0,
            "ai_confidence": plagiarism_results['ai_confidence'],
            "ai_patterns": {
                "explicit_patterns": [],
                "feature_scores": plagiarism_results['feature_scores']
            },
            "semantic_similarity": plagiarism_results['semantic_similarity'],
            "statistical_similarity": plagiarism_results['statistical_similarity'],
            "ngram_similarity": plagiarism_results['ngram_similarity'],
            "emoji_detected": False,
            "emoji_count": 0,
            "emoji_list": [],
            "top_features_score": plagiarism_results['top_features_score'],
            "subject_mismatch": subject_mismatch,
            "llm_similarity": plagiarism_results['ai_confidence']
        },
        "content_validation": {
            "status": "PASSED" if final_relevance >= relevance_threshold else "FAILED",
            "relevance_score": final_relevance,
            "phi_llm_score": phi_relevance,
            "groq_word_score": groq_relevance,
            "comments": f"Phi LLM analysis for subject: {subject}"
        },
        "ai_detection": {
            "ai_patterns_detected": plagiarism_results['ai_confidence'] > 40.0,
            "ai_confidence": plagiarism_results['ai_confidence'],
            "patterns": {
                "explicit_patterns": [],
                "feature_scores": plagiarism_results['feature_scores']
            }
        },
        "failure_reason": failure_reasons[0] if failure_reasons else None,
        "all_failure_reasons": failure_reasons if failure_reasons else None,
        "phi_llm_used": phi_llm.model is not None
    }
    
    # Save result
    with open('result/result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info("Sandbox analysis complete with Phi LLM")
    return result

if __name__ == "__main__":
    run_sandbox_analysis()