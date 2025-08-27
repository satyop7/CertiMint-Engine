"""
Enhanced relevance calculation using combined keywords
"""
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger('enhanced_relevance')

def calculate_combined_relevance(ocr_text: str, groq_keywords: List[str], scraped_keywords: List[str], embedding_score: float = 0) -> Dict[str, Any]:
    """Calculate relevance score based on keywords from Groq API, web scraping, and embedding model"""
    # Normalize text for matching
    text_lower = ocr_text.lower()
    
    # Count matches for Groq keywords
    matched_keywords = [kw for kw in groq_keywords if kw.lower() in text_lower]
    groq_matches = len(matched_keywords)
    groq_percent = (groq_matches / len(groq_keywords) * 100) if groq_keywords else 0
    logger.info(f"Groq keywords matches: {groq_matches}/{len(groq_keywords)} = {groq_percent}%")
    
    # Check if scraped keywords are valid (non-empty and not generic placeholders)
    is_valid_keyword = lambda kw: kw and not kw.startswith("keyword")
    valid_scraped = [kw for kw in scraped_keywords if is_valid_keyword(kw)]
    use_scraped = len(valid_scraped) > 0
    
    # Skip scraped keywords if they're just placeholders (keyword1, keyword2, etc.)
    if use_scraped:
        scraped_matches = sum(1 for kw in valid_scraped if kw.lower() in text_lower)
        scraped_percent = (scraped_matches / len(valid_scraped) * 100) if valid_scraped else 0
        logger.info(f"Scraped keywords matches: {scraped_matches}/{len(valid_scraped)} = {scraped_percent}%")
    else:
        scraped_percent = 0
        logger.info("No valid scraped keywords available - using only Groq keywords and embedding score")
    
    # Calculate final score - simple average of available scores
    if embedding_score > 0:
        # Average with embedding score (prioritize embedding score if no valid scraped keywords)
        combined_score = (groq_percent + embedding_score) / 2
        logger.info(f"Using average of Groq keywords ({groq_percent}%) and embedding score ({embedding_score}%)")
    else:
        # Only use Groq score if no embedding score
        combined_score = groq_percent
        logger.info(f"Using only Groq keywords score ({groq_percent}%)")
    
    # Round to 2 decimal places
    combined_score = round(combined_score, 2)
    
    # Determine status
    status = "PASSED" if combined_score >= 48.0 else "FAILED"
    
    # Create detailed results
    matched_keywords = []
    missed_keywords = []
    
    # Track matched and missed keywords
    for kw in groq_keywords:
        if kw.lower() in text_lower:
            matched_keywords.append({"keyword": kw, "source": "groq"})
        else:
            missed_keywords.append({"keyword": kw, "source": "groq"})
            
    for kw in scraped_keywords:
        if kw.lower() in text_lower and kw not in [item["keyword"] for item in matched_keywords]:
            matched_keywords.append({"keyword": kw, "source": "scraped"})
        elif kw.lower() not in text_lower:
            missed_keywords.append({"keyword": kw, "source": "scraped"})
    
    # Generate comment based on score
    if combined_score >= 75:
        comment = "Content is highly relevant to the subject"
    elif combined_score >= 48:
        comment = "Content is sufficiently relevant to the subject"
    elif combined_score >= 30:
        comment = "Content has limited relevance to the subject"
    else:
        comment = "Content lacks relevance to the subject"
    
    return {
        "status": status,
        "relevance_score": combined_score,
        "groq_match_percent": groq_percent,
        "scraped_match_percent": scraped_percent,
        "matched_keywords": [item["keyword"] for item in matched_keywords[:10]],
        "missed_keywords": [item["keyword"] for item in missed_keywords[:10]],
        "comments": comment
    }

def check_combined_relevance(ocr_text: str, subject: str, groq_keywords: List[str], scraped_keywords: List[str], embedding_score: float = 0) -> Dict[str, Any]:
    """Check relevance using combined keywords from Groq API, web scraping, and embedding model"""
    logger.info(f"Checking relevance for subject: {subject}")
    logger.info(f"Using {len(groq_keywords)} Groq keywords and {len(scraped_keywords)} scraped keywords")
    if embedding_score > 0:
        logger.info(f"Including embedding model score: {embedding_score}%")
    
    # Normalize text for matching
    text_lower = ocr_text.lower()
    
    # Find matched and missed keywords
    matched_keywords = [kw for kw in groq_keywords if kw.lower() in text_lower]
    missed_keywords = [kw for kw in groq_keywords if kw.lower() not in text_lower]
    
    # Check if scraped keywords are valid (not placeholders)
    is_valid_keyword = lambda kw: kw and not kw.startswith("keyword")
    valid_scraped = [kw for kw in scraped_keywords if is_valid_keyword(kw)]
    
    # Add valid scraped keywords to matched/missed lists
    for kw in valid_scraped:
        if kw.lower() in text_lower and kw not in matched_keywords:
            matched_keywords.append(kw)
        elif kw not in missed_keywords:
            missed_keywords.append(kw)
    
    # Calculate relevance
    result = calculate_combined_relevance(ocr_text, groq_keywords, scraped_keywords, embedding_score)
    
    # Add matched and missed keywords to result
    result['matched_keywords'] = matched_keywords
    result['missed_keywords'] = missed_keywords
    result['relevance_score'] = round(result['relevance_score'], 2)
    result['status'] = "PASSED" if result['relevance_score'] >= 48.0 else "FAILED"
    
    # Log results
    logger.info(f"Relevance score: {result['relevance_score']}%")
    logger.info(f"Status: {result['status']}")
    logger.info(f"Matched {len(matched_keywords)} keywords, missed {len(missed_keywords)} keywords")
    
    return result