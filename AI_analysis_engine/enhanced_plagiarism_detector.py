"""
Enhanced Plagiarism Detector

This module provides enhanced plagiarism detection capabilities by combining
multiple detection strategies including AI pattern detection.
"""

import re
from collections import Counter
import ai_pattern_detector

def detect_enhanced_plagiarism(text, references):
    """
    Performs enhanced plagiarism detection using multiple strategies.
    
    Args:
        text (str): The text to analyze
        references (list): List of reference sources
        
    Returns:
        dict: Detection results with confidence scores
    """
    # Get AI pattern detection results
    ai_results = ai_pattern_detector.detect_ai_patterns(text)
    
    # Check for subject mismatch
    subject_mismatch = False
    try:
        import os
        import json
        if os.path.exists("data/info.json"):
            with open("data/info.json") as f:
                info = json.load(f)
                file_subject = info.get("subject_name", "").lower()
                if file_subject and file_subject not in text.lower():
                    subject_mismatch = True
    except:
        pass
    
    # Calculate plagiarism score based on AI detection and other signals
    plagiarism_score = ai_results.get("ai_confidence", 0)
    
    # Add additional score for subject mismatch
    if subject_mismatch:
        plagiarism_score = max(plagiarism_score, 60)  # Minimum 60% if subject mismatch
    
    # Combine results
    return {
        "plagiarism_detected": plagiarism_score > 30,
        "plagiarism_percentage": plagiarism_score,
        "ai_patterns_detected": ai_results.get("ai_patterns_detected", False),
        "ai_confidence": ai_results.get("ai_confidence", 0),
        "ai_patterns": ai_results.get("ai_patterns", {}),
        "emoji_detected": ai_results.get("emoji_detected", False),
        "emoji_count": ai_results.get("emoji_count", 0),
        "emoji_list": ai_results.get("emoji_list", []),
        "top_features_score": ai_results.get("top_features_score", 0),
        "subject_mismatch": subject_mismatch,
        "llm_similarity": plagiarism_score
    }