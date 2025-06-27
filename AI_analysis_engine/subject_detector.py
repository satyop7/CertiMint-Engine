#!/usr/bin/env python3
"""
Subject detection module for enhanced validation

This module analyzes document content to detect the actual subject matter
and compare it with the declared subject, which helps identify AI-generated
or plagiarized content that doesn't match the assigned topic.
"""

import os
import json
import re
import logging
from collections import Counter
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('subject_detector')

# List of major academic subjects
SUBJECTS = {
    "computer science": ["programming", "algorithm", "data structure", "software", "hardware", "computing", "code", 
                      "database", "network", "artificial intelligence", "machine learning", "computer"],
    "mathematics": ["algebra", "calculus", "geometry", "equation", "theorem", "mathematical", "function", 
                  "number theory", "statistics", "probability", "matrix"],
    "physics": ["quantum", "mechanics", "relativity", "particle", "force", "energy", "motion", "gravity", 
              "electromagnetic", "thermodynamics", "velocity", "acceleration", "physics"],
    "chemistry": ["chemical", "reaction", "molecule", "compound", "element", "periodic table", "acid", 
                "base", "organic", "inorganic", "solution", "chemistry", "bond"],
    "biology": ["cell", "organism", "species", "evolution", "genetics", "dna", "ecosystem", "protein", 
              "biological", "anatomy", "physiology", "biology"],
    "engineering": ["design", "system", "mechanical", "electrical", "civil", "structural", "construction", 
                  "manufacturing", "engineering"],
    "history": ["century", "war", "civilization", "empire", "revolution", "historical", "ancient", 
              "medieval", "modern", "king", "queen", "president", "historical", "history"],
    "literature": ["novel", "poetry", "fiction", "character", "narrative", "author", "literary", 
                 "shakespeare", "poem", "writer", "literature"],
    "psychology": ["behavior", "cognitive", "mental", "perception", "emotion", "psychological", 
                 "consciousness", "memory", "brain", "psychology"],
    "economics": ["market", "economy", "financial", "trade", "supply", "demand", "monetary", 
                "fiscal", "inflation", "economic", "economics"]
}

def detect_document_subject(text: str) -> Dict[str, Any]:
    """
    Analyze text to determine the most likely academic subject
    
    Args:
        text: The document text to analyze
        
    Returns:
        Dictionary with detected subject info
    """
    if not text or len(text) < 100:
        logger.warning("Text too short for reliable subject detection")
        return {"subject": "unknown", "confidence": 0, "keywords": []}
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Count keyword occurrences for each subject
    subject_scores = {}
    subject_keywords = {}
    
    for subject, keywords in SUBJECTS.items():
        keyword_counts = {}
        for keyword in keywords:
            count = text_lower.count(keyword)
            if count > 0:
                keyword_counts[keyword] = count
                
        # Calculate score based on keyword count and relevance
        if keyword_counts:
            total_count = sum(keyword_counts.values())
            unique_keywords = len(keyword_counts)
            
            # Favor subjects with both high occurrence count and keyword diversity
            score = total_count * (1 + 0.1 * unique_keywords)
            subject_scores[subject] = score
            subject_keywords[subject] = keyword_counts
    
    # Get top subject and confidence
    if not subject_scores:
        return {"subject": "unknown", "confidence": 0, "keywords": []}
    
    # Find top subject
    top_subject = max(subject_scores, key=subject_scores.get)
    top_score = subject_scores[top_subject]
    
    # Calculate relative confidence (0-100)
    total_score = sum(subject_scores.values())
    confidence = (top_score / total_score) * 100 if total_score > 0 else 0
    
    # Get top keywords for the detected subject
    top_keywords = subject_keywords[top_subject]
    keywords_list = sorted(top_keywords.items(), key=lambda x: x[1], reverse=True)
    
    # Secondary subjects (if any)
    other_subjects = []
    for subject, score in sorted(subject_scores.items(), key=lambda x: x[1], reverse=True)[1:3]:
        if score > top_score * 0.5:  # Only include relatively strong secondary subjects
            other_subjects.append({
                "subject": subject, 
                "score": score,
                "confidence": (score / total_score) * 100
            })
    
    return {
        "subject": top_subject,
        "confidence": confidence,
        "score": top_score,
        "keywords": keywords_list[:5],  # Top 5 keywords
        "secondary_subjects": other_subjects
    }

def check_subject_mismatch(text: str, declared_subject: str) -> Dict[str, Any]:
    """
    Check if the document content matches the declared subject
    
    Args:
        text: The document text to analyze
        declared_subject: The subject as declared in metadata
        
    Returns:
        Dictionary with mismatch analysis
    """
    # Clean up the declared subject
    declared_subject = declared_subject.lower().strip()
    
    # Detect actual subject from document
    detected = detect_document_subject(text)
    actual_subject = detected["subject"]
    
    # Check direct match
    direct_match = (declared_subject == actual_subject)
    
    # Check if declared subject is one of detected keywords
    keyword_match = any(declared_subject in keyword for keyword, _ in detected["keywords"])
    
    # Check if declared subject is in secondary subjects
    secondary_match = any(declared_subject == sec["subject"] for sec in detected.get("secondary_subjects", []))
    
    # Check if declared subject is a known subject
    is_known_subject = any(declared_subject in subject for subject in SUBJECTS.keys())
    
    # Calculate match confidence
    if direct_match:
        match_confidence = 100
    elif secondary_match:
        match_confidence = 60
    elif keyword_match:
        match_confidence = 40
    else:
        match_confidence = 0
    
    # Determine if there's a significant mismatch
    is_mismatch = not (direct_match or secondary_match)
    
    return {
        "declared_subject": declared_subject,
        "detected_subject": actual_subject,
        "is_match": not is_mismatch,
        "match_confidence": match_confidence,
        "is_mismatch": is_mismatch,
        "mismatch_severity": "high" if is_mismatch and not keyword_match else "medium" if is_mismatch else "none",
        "detected_info": detected
    }

def get_declared_subject_from_info() -> Optional[str]:
    """Get the declared subject from info.json file"""
    try:
        if os.path.exists("data/info.json"):
            with open("data/info.json", "r") as f:
                info = json.load(f)
                return info.get("subject_name", "").lower().strip()
    except Exception as e:
        logger.error(f"Error reading info.json: {e}")
    return None

# Example usage
if __name__ == "__main__":
    # Test with sample text
    import sys
    
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], "r") as f:
            text = f.read()
    else:
        # Sample physics text
        text = """
        Quantum mechanics is a fundamental theory in physics that describes the physical properties of nature
        at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including
        quantum chemistry, quantum field theory, quantum technology, and quantum information science.
        """
    
    # Get detected subject
    result = detect_document_subject(text)
    print(f"Detected subject: {result['subject']} (confidence: {result['confidence']:.1f}%)")
    print(f"Top keywords: {result['keywords']}")
    
    # Get declared subject (if available)
    declared_subject = get_declared_subject_from_info() or "physics"
    print(f"Declared subject: {declared_subject}")
    
    # Check for mismatch
    mismatch = check_subject_mismatch(text, declared_subject)
    print(f"Subject match: {mismatch['is_match']}")
    print(f"Match confidence: {mismatch['match_confidence']:.1f}%")
    print(f"Mismatch severity: {mismatch['mismatch_severity']}")
