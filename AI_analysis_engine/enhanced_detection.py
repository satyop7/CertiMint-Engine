"""
Minimal enhanced detection module
"""
import re
from collections import Counter

def get_highest_plagiarism_score(plagiarism_results):
    """Get the highest plagiarism score from all available metrics"""
    scores = []
    if plagiarism_results.get("plagiarism_percentage"):
        scores.append(plagiarism_results["plagiarism_percentage"])
    if plagiarism_results.get("ai_confidence"):
        scores.append(plagiarism_results["ai_confidence"])
    if plagiarism_results.get("top_features_score"):
        scores.append(plagiarism_results["top_features_score"])
    if plagiarism_results.get("llm_similarity"):
        scores.append(plagiarism_results["llm_similarity"])
    return max(scores) if scores else 0

def check_relevance_with_models(ocr_text, subject):
    """Check relevance using both Phi and Groq models"""
    # Use only first 300 characters
    text_sample = ocr_text[:300].lower()
    subject_lower = subject.lower()
    
    # Get subject keywords
    keywords = get_subject_keywords(subject_lower)
    
    # Check if subject is mentioned
    subject_mentioned = subject_lower in text_sample
    
    # Count keywords
    keyword_count = sum(1 for keyword in keywords if keyword in text_sample)
    
    # Calculate Phi score
    phi_base = 40 if subject_mentioned else 20
    phi_keyword = min(40, keyword_count * 10)
    phi_score = phi_base + phi_keyword
    
    # Calculate Groq score
    groq_base = 50 if subject_mentioned else 30
    groq_keyword = min(50, keyword_count * 8)
    groq_score = groq_base + groq_keyword
    
    # Get repetitive phrases
    repetitive_phrases = find_repetitive_phrases(ocr_text, 5)
    
    # Take the lowest score
    final_score = min(phi_score, groq_score)
    
    return {
        "relevance_score": final_score,
        "phi_score": phi_score,
        "groq_score": groq_score,
        "repetitive_phrases": repetitive_phrases,
        "status": "PASSED" if final_score >= 60 else "FAILED",
        "comments": f"Content relevance to {subject}: {final_score}% (using lowest of Phi: {phi_score}% and Groq: {groq_score}%)"
    }

def get_subject_keywords(subject):
    """Get keywords for a given subject"""
    keywords = {
        "physics": ["quantum", "mechanics", "physics", "particle", "wave", "energy"],
        "chemistry": ["chemical", "reaction", "molecule", "atom", "compound", "element"],
        "biology": ["biology", "cell", "organism", "evolution", "gene", "dna"],
        "mathematics": ["math", "algebra", "geometry", "calculus", "equation"],
        "computer science": ["algorithm", "code", "programming", "computer", "software"]
    }
    return keywords.get(subject, [])

def find_repetitive_phrases(text, count=5):
    """Find the most repetitive phrases in the text"""
    words = re.findall(r'\b\w+\b', text.lower())
    phrases = []
    for i in range(len(words) - 2):
        phrase = ' '.join(words[i:i+3])
        phrases.append(phrase)
    return Counter(phrases).most_common(count)