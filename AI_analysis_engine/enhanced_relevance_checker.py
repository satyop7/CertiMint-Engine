"""
Enhanced Relevance Checker

This module provides functionality to check the relevance of text content
to a specified subject.
"""

def enhanced_relevance_check(text, subject, model=None):
    """
    Checks the relevance of text content to a specified subject.
    
    Args:
        text (str): The text to analyze
        subject (str): The subject to check relevance against
        model: Optional model for advanced checks
        
    Returns:
        dict: Relevance assessment results
    """
    # Convert to lowercase for case-insensitive matching
    subject_lower = subject.lower()
    text_lower = text.lower()
    
    # Calculate subject occurrences
    subject_count = text_lower.count(subject_lower)
    keywords_found = [word for word in subject_lower.split() if len(word) > 3 and word in text_lower]
    
    # Subject-specific keywords
    subject_keywords = {
        "physics": ["quantum", "mechanics", "physics", "particle", "wave", "energy"],
        "history": ["history", "century", "war", "civilization", "ancient", "medieval"],
        "mathematics": ["mathematics", "math", "algebra", "geometry", "calculus"],
        "biology": ["biology", "cell", "organism", "evolution", "gene", "dna"],
        "computer science": ["algorithm", "code", "programming", "computer", "software", "hardware"],
        "chemistry": ["chemical", "reaction", "molecule", "atom", "compound", "element"],
        "literature": ["novel", "author", "literary", "character", "plot", "narrative"]
    }
    
    # Check for subject keywords
    if subject_lower in subject_keywords:
        subject_specific_keywords = subject_keywords[subject_lower]
        keyword_matches = sum(1 for word in subject_specific_keywords if word in text_lower)
        keyword_match_ratio = keyword_matches / len(subject_specific_keywords)
    else:
        # Generic approach for subjects not in our dictionary
        keyword_match_ratio = len(keywords_found) / max(1, len(subject_lower.split()))
    
    # Simple keyword check for the subject
    if subject_lower in text_lower or keyword_match_ratio > 0.3:
        contains_subject = True
        # Adjust score based on frequency
        if subject_count > 3 or keyword_match_ratio > 0.5:
            score = 75
            status = "PASSED"
            comments = f"Content appears to be relevant to {subject} with {subject_count} mentions"
        else:
            score = 60
            status = "PASSED"
            comments = f"Content appears somewhat relevant to {subject} with limited mentions"
    else:
        # Check for common keywords that would indicate a mismatch
        mismatch_subjects = {}
        
        # Count occurrences of subject keywords in other subjects
        for subj, keywords in subject_keywords.items():
            if subj.lower() != subject_lower:
                matches = sum(1 for word in keywords if word in text_lower)
                if matches >= 3:
                    mismatch_subjects[subj] = matches
        
        # Check for mismatch
        if mismatch_subjects:
            wrong_subject = max(mismatch_subjects.items(), key=lambda x: x[1])[0]
            contains_subject = False
            score = 10
            status = "FAILED"
            comments = f"Document contains '{wrong_subject}' which is unrelated to {subject}"
        else:
            contains_subject = False
            score = 30
            status = "FAILED" 
            comments = f"Content appears unrelated to {subject}"
    
    return {
        "status": status,
        "relevance_score": score,
        "comments": comments
    }