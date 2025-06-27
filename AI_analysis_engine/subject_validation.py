"""
Subject Validation Module

This module provides functionality to validate if content matches a claimed subject.
"""

def validate_subject_keywords(text, subject):
    """
    Validates if the text content matches the claimed subject using keyword analysis.
    
    Args:
        text (str): The text to analyze
        subject (str): The claimed subject
        
    Returns:
        tuple: (is_valid, confidence, reason)
    """
    # Convert to lowercase for case-insensitive matching
    subject_lower = subject.lower()
    text_lower = text.lower()
    
    # Subject-specific keywords
    subject_keywords = {
        "physics": ["quantum", "mechanics", "physics", "particle", "wave", "energy", "force", "mass"],
        "history": ["history", "century", "war", "civilization", "ancient", "medieval", "empire", "revolution"],
        "mathematics": ["mathematics", "math", "algebra", "geometry", "calculus", "theorem", "equation", "function"],
        "biology": ["biology", "cell", "organism", "evolution", "gene", "dna", "protein", "species", "ecosystem"],
        "computer science": ["algorithm", "code", "programming", "computer", "software", "hardware", "data", "network"],
        "chemistry": ["chemical", "reaction", "molecule", "atom", "compound", "element", "acid", "bond"],
        "literature": ["novel", "author", "literary", "character", "plot", "narrative", "theme", "symbolism"]
    }
    
    # Check direct subject mention
    direct_mention = subject_lower in text_lower
    
    # Check for subject keywords
    if subject_lower in subject_keywords:
        subject_specific_keywords = subject_keywords[subject_lower]
        keyword_matches = sum(1 for word in subject_specific_keywords if word in text_lower)
        keyword_match_ratio = keyword_matches / len(subject_specific_keywords)
    else:
        # Generic approach for subjects not in our dictionary
        keywords = [word for word in subject_lower.split() if len(word) > 3]
        keyword_matches = sum(1 for word in keywords if word in text_lower)
        keyword_match_ratio = keyword_matches / max(1, len(keywords))
    
    # Check for competing subjects
    competing_subjects = {}
    for subj, keywords in subject_keywords.items():
        if subj.lower() != subject_lower:
            matches = sum(1 for word in keywords if word in text_lower)
            match_ratio = matches / len(keywords)
            if match_ratio > 0.4:  # Significant match with another subject
                competing_subjects[subj] = match_ratio
    
    # Determine if content matches claimed subject
    if direct_mention and keyword_match_ratio > 0.3:
        # Strong match
        is_valid = True
        confidence = min(100, 50 + int(keyword_match_ratio * 100))
        reason = f"Content matches claimed subject '{subject}' with good keyword coverage"
    elif direct_mention or keyword_match_ratio > 0.2:
        # Moderate match
        is_valid = True
        confidence = min(100, 40 + int(keyword_match_ratio * 100))
        reason = f"Content somewhat matches claimed subject '{subject}'"
    elif competing_subjects:
        # Content matches a different subject better
        is_valid = False
        best_match = max(competing_subjects.items(), key=lambda x: x[1])
        competing_subject = best_match[0]
        competing_ratio = best_match[1]
        confidence = min(100, int(competing_ratio * 100))
        reason = f"Content appears to be about '{competing_subject}' rather than claimed subject '{subject}'"
    else:
        # No strong match to any subject
        is_valid = False
        confidence = 20
        reason = f"Content does not appear to match claimed subject '{subject}'"
    
    return is_valid, confidence, reason