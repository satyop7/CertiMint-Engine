"""
Enhanced Plagiarism Detection Module

This module provides advanced plagiarism detection by combining multiple techniques:
- Semantic similarity comparison
- AI pattern detection
- Statistical text analysis
- N-gram comparison 
"""

import re
import string
import logging
import math
import os
import json
from collections import Counter
import ai_pattern_detector

logger = logging.getLogger(__name__)

# Function to extract n-grams from text
def get_ngrams(text, n=3):
    """Extract n-grams from text"""
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.append(ngram)
    return ngrams

def calculate_ngram_similarity(text1, text2, n=3):
    """Calculate n-gram similarity between two texts"""
    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)
    
    if not ngrams1 or not ngrams2:
        return 0.0
        
    # Count common n-grams
    common_ngrams = set(ngrams1).intersection(set(ngrams2))
    
    # Calculate Jaccard similarity
    jaccard = len(common_ngrams) / (len(set(ngrams1)) + len(set(ngrams2)) - len(common_ngrams))
    
    return jaccard * 100

def analyze_statistical_similarity(text1, text2):
    """Calculate statistical similarity based on sentence length distribution"""
    def get_sentence_stats(text):
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        if not sentences:
            return (0, 0)
        lengths = [len(s) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        if len(lengths) > 1:
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0
        return (avg_len, std_dev)
    
    stats1 = get_sentence_stats(text1)
    stats2 = get_sentence_stats(text2)
    
    if stats1[0] == 0 or stats2[0] == 0:
        return 0.0
        
    # Calculate similarity based on sentence length statistics
    avg_len_diff = abs(stats1[0] - stats2[0]) / max(stats1[0], stats2[0])
    std_diff = abs(stats1[1] - stats2[1]) / max(stats1[1], stats2[1]) if max(stats1[1], stats2[1]) > 0 else 1.0
    
    stat_similarity = 100 * (1 - (avg_len_diff * 0.5 + std_diff * 0.5))
    return max(0, min(100, stat_similarity))

def calculate_top_features_score(feature_scores):
    """
    Calculate a score based on the top 2 highest feature scores.
    
    Args:
        feature_scores: Dictionary of feature scores
        
    Returns:
        Average score of the top 2 features
    """
    if not feature_scores or len(feature_scores) < 2:
        return 0.0
        
    # Sort feature scores from highest to lowest
    sorted_scores = sorted(feature_scores.values(), reverse=True)
    
    # Get the top 2 scores
    top_2_scores = sorted_scores[:2]
    
    # Calculate the average
    average_score = sum(top_2_scores) / len(top_2_scores)
    
    # Log which features were used
    top_features = [k for k, v in feature_scores.items() 
                   if v in top_2_scores]
    logger.info(f"Using top 2 AI features for calculation: {top_features}")
    logger.info(f"Top features average: {average_score:.1f}%")
    
    return average_score

def detect_enhanced_plagiarism(text, reference_sources=None):
    """
    Enhanced plagiarism detection using multiple methods.
    
    Args:
        text: The text to analyze
        reference_sources: Optional list of reference texts
        
    Returns:
        Dictionary with plagiarism detection results
    """
    results = {
        "plagiarism_detected": False,
        "plagiarism_percentage": 0,
        "ai_patterns_detected": False,
        "ai_confidence": 0,
        "ai_patterns": [],
        "semantic_similarity": 0,
        "statistical_similarity": 0,
        "ngram_similarity": 0,
        "emoji_detected": False,
        "emoji_count": 0,
        "emoji_list": []
    }
    
    # Run AI pattern detection
    ai_detection = ai_pattern_detector.detect_ai_content(text)
    results["ai_patterns_detected"] = ai_detection["is_ai_generated"]
    results["ai_confidence"] = ai_detection["ai_confidence"]
    results["ai_patterns"] = {
        "explicit_patterns": ai_detection["patterns_detected"],
        "feature_scores": ai_detection["feature_scores"]
    }
    
    # Check for emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+", flags=re.UNICODE)
    
    emojis = emoji_pattern.findall(text)
    results["emoji_detected"] = len(emojis) > 0
    results["emoji_count"] = len(emojis)
    results["emoji_list"] = emojis[:10]  # Limit to first 10 emojis
    
    # If reference sources are provided, calculate similarities
    if reference_sources and isinstance(reference_sources, list):
        try:
            max_semantic = 0
            max_ngram = 0
            max_stat = 0
            
            for ref in reference_sources:
                if isinstance(ref, dict) and "content" in ref:
                    ref_text = ref["content"]
                    
                    # Calculate n-gram similarity
                    ngram_sim = calculate_ngram_similarity(text, ref_text)
                    max_ngram = max(max_ngram, ngram_sim)
                    
                    # Calculate statistical similarity
                    stat_sim = analyze_statistical_similarity(text, ref_text)
                    max_stat = max(max_stat, stat_sim)
            
            # Store the maximum similarities found
            results["ngram_similarity"] = max_ngram
            results["statistical_similarity"] = max_stat
            
            # Calculate overall plagiarism score using weighted average
            # Give higher weight to AI pattern detection for AI-generated content
            
            # Check if strict AI detection is enabled in info.json
            strict_ai_detection = False
            use_top_features = False
            try:
                if os.path.exists("data/info.json"):
                    with open("data/info.json", "r") as f:
                        info = json.load(f)
                        strict_ai_detection = info.get("strict_ai_detection", False)
                        use_top_features = info.get("use_top_features", False)
            except Exception:
                pass
            
            # Calculate the top features score
            ai_feature_scores = ai_detection.get("feature_scores", {})
            top_features_score = calculate_top_features_score(ai_feature_scores)
            results["top_features_score"] = top_features_score
            
            # If requested, use the top features score as the main plagiarism indicator
            if use_top_features:
                logger.info("Using top 2 AI feature scores for plagiarism calculation")
                results["plagiarism_percentage"] = top_features_score
                # Apply a boost if AI patterns were detected
                if results["ai_patterns_detected"]:
                    results["plagiarism_percentage"] = min(100, results["plagiarism_percentage"] * 1.25)
                    logger.info(f"Applied AI pattern boost to score: {results['plagiarism_percentage']:.1f}%")
            # If strict detection is enabled, increase the weight of AI confidence
            elif strict_ai_detection:
                logger.info("Using strict AI detection weights")
                # In strict mode, give significant weight to top features score
                results["plagiarism_percentage"] = (
                    results["ai_confidence"] * 0.5 +  # Weight for AI confidence
                    top_features_score * 0.3 +        # Weight for top features
                    max_ngram * 0.1 +
                    max_stat * 0.1
                )
                
                # Apply a minimum threshold for suspicious AI content
                if results["ai_confidence"] > 25 or top_features_score > 65:  # Lower threshold in strict mode
                    results["plagiarism_percentage"] = max(60, results["plagiarism_percentage"])
                    logger.warning(f"Strict AI detection triggered with confidence {results['ai_confidence']}%")
            else:
                # Standard weighting with top features included
                if results["ai_patterns_detected"]:
                    results["plagiarism_percentage"] = (
                        results["ai_confidence"] * 0.4 +
                        top_features_score * 0.3 +
                        max_ngram * 0.15 +
                        max_stat * 0.15
                    )
                else:
                    results["plagiarism_percentage"] = (
                        results["ai_confidence"] * 0.3 +
                        top_features_score * 0.3 +
                        max_ngram * 0.2 +
                        max_stat * 0.2
                    )
                
            # Ensure the percentage is within bounds
            results["plagiarism_percentage"] = max(0, min(100, results["plagiarism_percentage"]))
            
        except Exception as e:
            logger.error(f"Error in plagiarism detection: {e}")
    else:
        # If no references are available, rely solely on AI pattern detection
        results["plagiarism_percentage"] = results["ai_confidence"]
    
    # Check for indicators that the subject in info.json doesn't match the content
    subject_mismatch = False
    try:
        if os.path.exists("data/info.json"):
            with open("data/info.json", "r") as f:
                info = json.load(f)
                subject = info.get("subject_name", "").lower()
                file_name = info.get("File_name", "").lower()
                
                # Check if the content mentions the subject
                if subject and len(subject) > 3:
                    if subject not in text.lower() and not any(word in text.lower() for word in subject.split()):
                        subject_mismatch = True
                        logger.warning(f"Subject '{subject}' not found in content")
                
                # Check if filename subject doesn't match content
                if file_name and "_" in file_name:
                    parts = file_name.split("_")
                    if any(len(part) > 4 for part in parts):
                        file_subject = " ".join(file_name.replace(".pdf", "").replace(".docx", "").split("_"))
                        if file_subject not in text.lower():
                            subject_mismatch = True
                            logger.warning(f"Filename subject '{file_subject}' not found in content")
    except Exception as e:
        logger.error(f"Error checking subject match: {e}")
    
    # Determine overall plagiarism status
    strict_mode = False
    try:
        if os.path.exists("data/info.json"):
            with open("data/info.json", "r") as f:
                info = json.load(f)
                strict_mode = info.get("strict_ai_detection", False)
    except Exception:
        pass
    
    if strict_mode:
        # In strict mode, lower the thresholds for detecting AI-generated content
        results["plagiarism_detected"] = (
            results["plagiarism_percentage"] > 55 or  # Lower threshold
            results["ai_confidence"] > 25 or         # Much lower threshold
            results["ai_patterns_detected"] or 
            results["emoji_detected"] or
            subject_mismatch                        # Subject mismatch is strong indicator
        )
        logger.info(f"Using strict plagiarism detection threshold. Result: {results['plagiarism_detected']}")
    else:
        # Standard detection
        results["plagiarism_detected"] = (
            results["plagiarism_percentage"] > 60 or 
            results["ai_patterns_detected"] or 
            results["emoji_detected"]
        )
    
    # Add mismatch information to results
    results["subject_mismatch"] = subject_mismatch
    
    return results
