import os
import json
import requests
import logging
import re

logger = logging.getLogger(__name__)

def get_subject_keywords_from_groq(subject):
    """Get 8 most common repetitive words for a subject using Groq API"""
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found, skipping Groq validation")
            return []
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"List exactly 8 most important and specific keywords that are commonly found in academic texts about {subject}. Return only the words separated by commas, no explanations or additional text."
        
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama3-8b-8192",
            "max_tokens": 100,
            "temperature": 0.1
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            keywords = [word.strip().lower() for word in content.split(",")][:8]
            logger.info(f"Groq keywords for {subject}: {keywords}")
            return keywords
        else:
            logger.error(f"Groq API error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return []

def validate_with_groq_keywords(ocr_text, subject):
    """Validate OCR text using Groq-generated keywords"""
    keywords = get_subject_keywords_from_groq(subject)
    if not keywords:
        return {"status": "FAILED", "relevance_score": 0, "comments": "Could not get keywords from Groq"}
    
    text_lower = ocr_text.lower()
    found_keywords = [kw for kw in keywords if kw in text_lower]
    keyword_count = sum(text_lower.count(kw) for kw in found_keywords)
    
    # Calculate relevance based on keyword matches
    if len(found_keywords) == 0:
        relevance_score = 0
    else:
        # Base score from keyword matches (0-80%)
        base_score = (len(found_keywords) / len(keywords)) * 80
        # Bonus from frequency (0-20%)
        frequency_bonus = min(20, keyword_count * 2)
        relevance_score = min(100, base_score + frequency_bonus)
    
    status = "PASSED" if relevance_score >= 35 else "FAILED"
    
    logger.info(f"Groq validation: {len(found_keywords)}/{len(keywords)} keywords found, score: {relevance_score:.1f}%")
    
    return {
        "status": status,
        "relevance_score": int(relevance_score),
        "comments": f"Found {len(found_keywords)}/{len(keywords)} keywords",
        "groq_keywords": keywords,
        "found_keywords": found_keywords
    }

def hybrid_validation(ocr_text, subject, phi_model):
    """Combine Groq keyword validation with Phi model validation - takes minimum of both scores"""
    logger.info(f"Starting hybrid validation for subject: {subject}")
    
    # Step 1: Get Groq keyword validation
    groq_result = validate_with_groq_keywords(ocr_text, subject)
    groq_score = groq_result["relevance_score"]
    logger.info(f"Groq keyword score: {groq_score}%")
    
    # Step 2: Get Phi model validation
    try:
        phi_prompt = f"""Rate how relevant this text is to the subject "{subject}" on a scale of 0-100.
        
Text sample: {ocr_text[:500]}
        
Respond with only a number (0-100):"""
        
        phi_response = phi_model.model(phi_prompt, max_tokens=10, temperature=0.1)
        response_text = phi_response["choices"][0]["text"].strip()
        
        # Extract number from response
        phi_match = re.search(r'(\d+)', response_text)
        if phi_match:
            phi_score = min(100, max(0, int(phi_match.group(1))))
        else:
            phi_score = 50  # Default if no number found
            
        logger.info(f"Phi model score: {phi_score}%")
        
    except Exception as e:
        logger.warning(f"Phi model validation failed: {e}")
        phi_score = 50
    
    # Step 3: Take the MINIMUM of both scores
    final_score = min(groq_score, phi_score)
    final_status = "PASSED" if final_score >= 35 else "FAILED"
    
    logger.info(f"Final hybrid score (min of {groq_score}% and {phi_score}%): {final_score}%")
    
    return {
        "status": final_status,
        "relevance_score": final_score,
        "comments": f"model_relevance_estimate: {final_score}%",
        "validation_method": "hybrid",
        "groq_score": groq_score,
        "phi_score": phi_score
    }