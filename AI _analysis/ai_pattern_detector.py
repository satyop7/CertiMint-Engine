"""
Enhanced AI Content Detection Module

This module provides advanced techniques for detecting AI-generated content
with higher accuracy than simple semantic comparisons.
"""

import re
import string
import logging
import random
import math
import sys
from collections import Counter

logger = logging.getLogger(__name__)

# Configure more verbose logging for debugging
if __name__ == "__main__" or "--debug" in sys.argv:
    logging.basicConfig(level=logging.DEBUG, 
                      format='%(asctime)s - %(levelname)s - %(message)s')

# AI-specific patterns commonly found in generated text
AI_PATTERNS = [
    r"as an AI",
    r"as an artificial intelligence",
    r"I don't have personal",
    r"I don't have the ability to",
    r"I don't have access to",
    r"I cannot access",
    r"my training data",
    r"my knowledge cutoff",
    r"my last update",
    r"As of my last training",
    r"my training cut[- ]?off",
    r"As a language model",
    r"Based on my training",
    r"As of my last update",
    r"I don't have subjective experiences",
    r"I don't have the capability to",
    r"I don't have real-time",
    r"as of my training data",
    r"I don't have opinions",
    r"I don't have beliefs",
    r"I can provide information",
    r"I'm not able to",
    r"I'm just a",
    r"I'm an AI",
]

# Common AI filler phrases and repetitive structures
AI_REPETITIVE_STRUCTURES = [
    r"In conclusion,",
    r"To summarize,",
    r"In summary,",
    r"It's important to note that",
    r"It's worth mentioning that",
    r"It's essential to understand that",
    r"Let me explain",
    r"Let's explore",
    r"Let's discuss",
]

# Common AI transition phrases that appear frequently in generated text
AI_TRANSITIONS = [
    r"First(ly)?,.*Second(ly)?,.*Third(ly)?",
    r"On one hand,.*On the other hand",
    r"However, it's important to consider",
    r"Nevertheless, it's crucial to acknowledge",
]

# AI text tends to have very consistent paragraph length
def analyze_paragraph_consistency(text):
    """Calculate the consistency of paragraph lengths in the text"""
    paragraphs = re.split(r'\n\s*\n', text)
    if len(paragraphs) <= 2:
        return 0.0
    
    lengths = [len(p.strip()) for p in paragraphs if len(p.strip()) > 0]
    if not lengths:
        return 0.0
        
    # Calculate variance coefficient - AI text often has very consistent paragraph lengths
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    
    # Calculate coefficient of variation - lower values indicate more consistency (common in AI text)
    cv = std_dev / mean if mean > 0 else 0
    
    # Map the coefficient of variation to a consistency score (0-100)
    # Very consistent paragraph lengths (low CV) map to high scores
    consistency_score = max(0, min(100, 100 * (1 - cv)))
    
    return consistency_score

def analyze_sentence_variety(text):
    """Analyze the variety in sentence structures and lengths"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    if len(sentences) < 3:
        return 0.0
    
    # Calculate sentence length statistics
    lengths = [len(s) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    cv = math.sqrt(variance) / mean if mean > 0 else 0
    
    # Human text typically has more variety in sentence length
    # Map the coefficient of variation to a variety score (0-100)
    variety_score = max(0, min(100, 100 * cv))
    
    return variety_score

def analyze_lexical_diversity(text):
    """Calculate the lexical diversity (type-token ratio)"""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return 0.0
        
    # Type-token ratio (unique words / total words)
    unique_words = set(words)
    diversity = len(unique_words) / len(words)
    
    # Map to a score (0-100) - AI text often has lower lexical diversity
    diversity_score = max(0, min(100, 100 * diversity))
    
    return diversity_score

def analyze_repetitive_patterns(text):
    """Detect repetitive patterns common in AI-generated text"""
    text_lower = text.lower()
    
    # Count occurrences of repetitive structures
    repetition_count = 0
    for pattern in AI_REPETITIVE_STRUCTURES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        repetition_count += len(matches)
    
    # Normalize by text length
    text_length = len(text.split())
    if text_length == 0:
        return 0.0
    
    repetition_rate = repetition_count / (text_length / 100)
    repetition_score = max(0, min(100, repetition_rate * 10))
    
    return repetition_score

ACADEMIC_AI_PHRASES = [
    r"this study aims to",
    r"the results indicate that",
    r"further research is needed",
    r"it is widely accepted that",
    r"according to recent studies",
    r"the data suggests that",
    r"in this paper, we will",
    r"we propose that",
    r"it can be concluded that",
    r"this research demonstrates",
    r"the findings reveal that",
    r"evidence suggests that",
    r"this highlights the importance of",
    r"it is important to consider",
    r"one possible explanation is",
    r"this raises the question of",
    r"another study found that",
    r"these results are consistent with",
    r"this is supported by",
    r"the literature suggests that",
    r"previous research has shown",
]

def detect_ai_content(text):
    """
    Enhanced AI content detection using multiple heuristics.
    Returns a dictionary with AI detection results.
    """
    results = {
        "is_ai_generated": False,
        "ai_confidence": 0,
        "patterns_detected": [],
        "feature_scores": {},
        "subject_mismatch": False
    }
    
    logger.info("Running AI pattern detection analysis")
    
    # Check for explicit AI patterns
    pattern_count = 0
    for pattern in AI_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            pattern_count += len(matches)
            results["patterns_detected"].extend(matches)
    
    # Check for academic AI phrases
    academic_pattern_count = 0
    for pattern in ACADEMIC_AI_PHRASES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            academic_pattern_count += len(matches)
            results["patterns_detected"].extend([f"Academic AI: {m}" for m in matches[:2]])
    
    if pattern_count > 0:
        logger.info(f"Found {pattern_count} explicit AI phrase patterns")
    
    if academic_pattern_count > 0:
        logger.info(f"Found {academic_pattern_count} academic AI phrase patterns")
    
    # Analyze paragraph consistency (AI often has very uniform paragraph lengths)
    para_consistency = analyze_paragraph_consistency(text)
    results["feature_scores"]["paragraph_consistency"] = para_consistency
    logger.info(f"Paragraph consistency score: {para_consistency:.1f}/100")
    
    # Analyze sentence variety (AI often has less varied sentence structures)
    sentence_variety = analyze_sentence_variety(text)
    results["feature_scores"]["sentence_variety"] = sentence_variety
    logger.info(f"Sentence variety score: {sentence_variety:.1f}/100")
    
    # Analyze lexical diversity (AI often has lower lexical diversity)
    lexical_diversity = analyze_lexical_diversity(text)
    results["feature_scores"]["lexical_diversity"] = lexical_diversity
    logger.info(f"Lexical diversity score: {lexical_diversity:.1f}/100")
    
    # Analyze repetitive patterns (AI often uses certain phrases repeatedly)
    repetitive_patterns = analyze_repetitive_patterns(text)
    results["feature_scores"]["repetitive_patterns"] = repetitive_patterns
    logger.info(f"Repetitive patterns score: {repetitive_patterns:.1f}/100")
    
    # Analyze structural patterns typical in AI text
    structure_score = analyze_structural_patterns(text)
    results["feature_scores"]["structural_patterns"] = structure_score
    logger.info(f"Structural patterns score: {structure_score:.1f}/100")
    
    # Check for subject-content mismatch (strong indicator of AI generation)
    mismatch_results = detect_subject_content_mismatch(text)
    subject_mismatch = mismatch_results.get("mismatch_detected", False)
    mismatch_confidence = mismatch_results.get("confidence", 0)
    
    if subject_mismatch:
        claimed = mismatch_results.get("claimed_subject", "unknown")
        detected = mismatch_results.get("detected_subjects", [])[0]["subject"] if mismatch_results.get("detected_subjects") else "unknown"
        logger.warning(f"SUBJECT MISMATCH DETECTED: Claimed '{claimed}' but detected '{detected}'")
        results["subject_mismatch"] = True
        results["subject_mismatch_details"] = mismatch_results
    
    # Calculate weighted AI score based on all features
    ai_score = (
        para_consistency * 0.15 +
        (100 - sentence_variety) * 0.15 +
        (100 - lexical_diversity) * 0.15 +
        repetitive_patterns * 0.15 +
        structure_score * 0.15
    )
    
    # Add more weight if explicit AI patterns were detected
    if pattern_count > 0:
        bonus = min(20, pattern_count * 5)
        ai_score += bonus
        logger.info(f"Adding AI pattern bonus of {bonus} points")
    
    # Add weight for academic AI phrases (less strong evidence than explicit patterns)
    if academic_pattern_count > 0:
        academic_bonus = min(15, academic_pattern_count * 2.5)
        ai_score += academic_bonus
        logger.info(f"Adding academic pattern bonus of {academic_bonus} points")
    
    # Add significant weight for subject mismatch
    if subject_mismatch:
        mismatch_bonus = min(30, mismatch_confidence * 0.5)
        ai_score += mismatch_bonus
        logger.warning(f"Adding subject mismatch bonus of {mismatch_bonus} points")
    
    # Check for strict AI detection mode in info.json
    strict_detection = False
    try:
        import os
        import json
        if os.path.exists("data/info.json"):
            with open("data/info.json", "r") as f:
                info = json.load(f)
                strict_detection = info.get("strict_ai_detection", False)
    except Exception:
        pass
    
    ai_score = min(100, ai_score)
    results["ai_confidence"] = ai_score
    
    # Determine if the text is likely AI-generated based on the score
    # Use a lower threshold for academic papers since they're more subtle
    is_academic = "introduction" in text.lower() and any(heading in text.lower() for heading in ["abstract", "conclusion", "references"])
    
    if strict_detection:
        # In strict mode, use lower thresholds
        threshold = 30 if is_academic else 35
        logger.info(f"Using strict AI detection threshold: {threshold}%")
    else:
        # Standard thresholds
        threshold = 60 if is_academic else 65
    
    # Content/subject mismatch is a strong indication of AI generation
    results["is_ai_generated"] = ai_score > threshold or subject_mismatch
    
    logger.info(f"Final AI confidence: {ai_score:.1f}% - AI Generated: {results['is_ai_generated']}")
    if results["is_ai_generated"]:
        trigger_reason = "high confidence score" if ai_score > threshold else "subject mismatch"
        logger.warning(f"AI content detected due to {trigger_reason}")
    
    return results

def analyze_structural_patterns(text):
    """Analyze common AI text structural patterns"""
    text_lower = text.lower()
    score = 0
    
    # Check for numbered lists and point-by-point structures
    numbered_pattern = re.compile(r'\n\s*\d+\.\s+[A-Z]')
    numbered_matches = numbered_pattern.findall(text)
    if len(numbered_matches) >= 3:
        score += 15
        logger.info(f"Found {len(numbered_matches)} numbered points - typical AI structure")
    
    # Check for Q&A format
    qa_pattern = re.compile(r'(?:question:|q:)|(?:\?)\s*\n+\s*(?:answer:|a:)', re.IGNORECASE)
    qa_matches = qa_pattern.findall(text)
    if qa_matches:
        score += 10
        logger.info("Found Q&A format - common in AI-generated text")
    
    # Check for excessive heading structure (common in AI-generated text)
    heading_pattern = re.compile(r'\n\s*#+\s+[A-Z]|\n\s*[A-Z][^.!?]+\n\s*[-=]+\s*\n')
    heading_matches = heading_pattern.findall(text)
    if len(heading_matches) >= 3:
        score += 15
        logger.info(f"Found {len(heading_matches)} markdown-style headings - typical AI structure")
    
    return score

def detect_subject_content_mismatch(text):
    """
    Detect mismatches between the content and the claimed subject in info.json
    Returns a dictionary with mismatch results.
    """
    try:
        import os
        import json
        
        mismatch_results = {
            "mismatch_detected": False,
            "claimed_subject": "",
            "detected_subjects": [],
            "confidence": 0
        }
        
        # Load subject from info.json
        if os.path.exists("data/info.json"):
            with open("data/info.json", "r") as f:
                info = json.load(f)
                claimed_subject = info.get("subject_name", "").lower()
                mismatch_results["claimed_subject"] = claimed_subject
                
                # Skip if no subject provided
                if not claimed_subject:
                    return mismatch_results
                
                # Common subjects and their keywords
                subject_keywords = {
                    "history": ["history", "historical", "century", "civilization", "ancient", "medieval", 
                               "empire", "dynasty", "revolution", "war", "monarchy"],
                    "physics": ["physics", "quantum", "mechanics", "relativity", "particle", "wave", 
                               "energy", "force", "mass", "velocity", "electromagnetic"],
                    "mathematics": ["mathematics", "math", "algebra", "geometry", "calculus", "theorem", 
                                  "function", "equation", "polynomial", "matrix", "vector"],
                    "biology": ["biology", "cell", "organism", "evolution", "gene", "protein", 
                              "DNA", "species", "ecosystem", "photosynthesis"],
                    "computer science": ["algorithm", "programming", "software", "database", "network", 
                                       "computational", "code", "internet", "data structure"]
                }
                
                # Detect subject from content
                text_lower = text.lower()
                subject_matches = {}
                
                for subject, keywords in subject_keywords.items():
                    matches = sum(1 for keyword in keywords if keyword in text_lower)
                    if matches > 0:
                        subject_matches[subject] = matches
                
                # Get top subjects
                if subject_matches:
                    sorted_subjects = sorted(subject_matches.items(), key=lambda x: x[1], reverse=True)
                    top_subject, top_matches = sorted_subjects[0]
                    
                    mismatch_results["detected_subjects"] = [
                        {"subject": s, "match_count": c} for s, c in sorted_subjects[:3]
                    ]
                    
                    # Check if claimed subject matches detected subject
                    claimed_found = False
                    for detected, _ in sorted_subjects:
                        if claimed_subject in detected or detected in claimed_subject:
                            claimed_found = True
                            break
                    
                    if not claimed_found and top_matches >= 5:
                        mismatch_results["mismatch_detected"] = True
                        mismatch_results["confidence"] = min(100, top_matches * 10)
                        logger.warning(f"Subject mismatch detected! Claimed: {claimed_subject}, Detected: {top_subject}")
        
        return mismatch_results
        
    except Exception as e:
        logger.error(f"Error in subject mismatch detection: {e}")
        return {"mismatch_detected": False, "error": str(e)}
