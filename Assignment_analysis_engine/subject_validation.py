"""
Subject validation module

This module provides direct keyword-based validation for assignment subjects
to prevent incorrect subject-content matching.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Dictionary of subjects with their essential keywords and disqualifying keywords
SUBJECT_KEYWORDS = {
    "history": {
        "essential": ["history", "historical", "ancient", "medieval", "century", "civilization", 
                     "empire", "dynasty", "war", "revolution", "period", "era"],
        "disqualifying": ["quantum", "mechanics", "physics", "artificial intelligence", "neural network", 
                         "machine learning", "algorithm", "programming", "code", "software", "computer science"]
    },
    "physics": {
        "essential": ["physics", "mechanics", "energy", "force", "motion", "quantum", "relativity", 
                     "particle", "wave", "theory", "thermodynamics", "electromagnetic"],
        "disqualifying": ["literature", "novel", "poem", "fiction", "author", "character", 
                         "political science", "government", "democracy", "economy"]
    },
    "quantum mechanics": {
        "essential": ["quantum", "mechanics", "wave function", "particle", "uncertainty", "superposition", 
                     "physics", "entanglement", "energy levels", "schrodinger", "heisenberg", "atomic", 
                     "subatomic", "quantum state", "probability"],
        "disqualifying": ["history", "literature", "ancient", "medieval", "dynasty", "economy", 
                        "government", "politics", "linguistics", "grammar"]
    },
    "computer science": {
        "essential": ["algorithm", "programming", "software", "hardware", "data", "network", 
                     "computer", "code", "system", "application", "development", "database"],
        "disqualifying": ["medieval", "ancient history", "literature", "poem", "novel", "biology", "chemistry"]
    },
    "artificial intelligence": {
        "essential": ["ai", "artificial intelligence", "machine learning", "neural", "algorithm", 
                     "deep learning", "model", "training", "prediction", "classification"],
        "disqualifying": ["ancient history", "medieval history", "chemistry", "organic chemistry"]
    },
    "literature": {
        "essential": ["literature", "novel", "fiction", "character", "narrative", "plot", 
                     "author", "book", "poem", "poetry", "story", "writing"],
        "disqualifying": ["quantum", "physics", "algorithm", "programming", "code", "software"]
    },
}

def validate_subject_keywords(text, subject):
    """
    Performs direct keyword validation for a subject.
    Returns a tuple of (is_valid, confidence, reason)
    """
    text_lower = text.lower()
    subject_lower = subject.lower()
    
    # Try to match with a known subject
    matched_subject = subject_lower
    for known_subject in SUBJECT_KEYWORDS:
        if known_subject in subject_lower or subject_lower in known_subject:
            matched_subject = known_subject
            break
    
    # If we don't have rules for this subject, return neutral result
    if matched_subject not in SUBJECT_KEYWORDS:
        return True, 50, f"No defined keyword rules for subject: {subject}"
    
    # Check for disqualifying keywords first (strongest signal)
    disqualifying = SUBJECT_KEYWORDS[matched_subject]["disqualifying"]
    for keyword in disqualifying:
        if keyword in text_lower:
            pattern = r'\b{}\b'.format(re.escape(keyword))
            matches = re.findall(pattern, text_lower)
            if matches:
                return False, 10, f"Document contains '{keyword}' which is unrelated to {subject}"
    
    # Check for essential keywords
    essential_count = 0
    essential = SUBJECT_KEYWORDS[matched_subject]["essential"]
    for keyword in essential:
        if keyword in text_lower:
            pattern = r'\b{}\b'.format(re.escape(keyword))
            matches = re.findall(pattern, text_lower)
            essential_count += len(matches)
    
    # Evaluate based on essential keywords
    if essential_count > 5:
        return True, 90, f"Document contains multiple keywords related to {subject}"
    elif essential_count > 2:
        return True, 70, f"Document contains some keywords related to {subject}"
    elif essential_count > 0:
        # Changed to true with low confidence - a few keywords might still indicate relevance
        return True, 40, f"Document contains few keywords related to {subject}"
    else:
        return False, 20, f"Document contains no essential keywords related to {subject}"
