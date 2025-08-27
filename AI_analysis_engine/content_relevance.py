"""
Content relevance checking with embedding models
"""
import logging

logger = logging.getLogger('content_relevance')

def check_groq_word_relevance(text, keywords):
    """Check relevance using keyword matching"""
    if not keywords or not text:
        return 50
    
    text_lower = text.lower()
    matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    if len(keywords) == 0:
        return 50
    
    relevance = (matches / len(keywords)) * 100
    return min(int(relevance), 90)

def calculate_final_relevance(keyword_score, embedding_score):
    """Calculate final relevance score"""
    # Weight embedding score higher (70%) vs keyword score (30%)
    final_score = (embedding_score * 0.7) + (keyword_score * 0.3)
    return int(final_score)