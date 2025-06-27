"""
Human-friendly content relevance checker using keywords and Phi LLM
"""
import re
import logging
from llm_loader import load_model

logger = logging.getLogger('content_relevance')

# Global Phi model instance
_phi_model = None
_phi_loaded = False

def _get_phi_model():
    """Get or load optimized Phi model"""
    global _phi_model, _phi_loaded
    
    if not _phi_loaded:
        logger.info("Loading optimized Phi-2 model for content relevance")
        _phi_model, success, error = load_model("phi-2.Q4_K_M.gguf")
        _phi_loaded = True
        if not success:
            logger.warning(f"Optimized Phi model loading failed: {error}")
        else:
            logger.info("✓ Optimized Phi-2 model ready for relevance analysis")
    
    return _phi_model

def check_groq_word_relevance(ocr_text, keywords):
    """Check relevance based on keywords (more lenient)"""
    text_lower = ocr_text.lower()
    total_words = len(re.findall(r'\b\w+\b', text_lower))
    
    if total_words == 0:
        return 0.0
    
    # Count occurrences of keywords and related terms
    word_matches = 0
    for word in keywords:
        word_matches += text_lower.count(word.lower())
    
    # Check for broader subject relevance
    subject_relevance = check_broader_relevance(text_lower, keywords)
    
    # Calculate percentage based on word density (more generous)
    base_relevance = min((word_matches / len(keywords)) * 40, 100.0)
    final_relevance = base_relevance + subject_relevance
    
    logger.info(f"Keyword-based relevance analysis: {final_relevance}%")
    return round(min(final_relevance, 100.0), 2)

def check_broader_relevance(text_lower, keywords):
    """Check for broader subject relevance"""
    # Expanded subject mappings for better coverage
    subject_expansions = {
        "artificial": ["ai", "machine", "learning", "intelligence", "algorithm", "model", "data", "computer"],
        "intelligence": ["ai", "artificial", "smart", "learning", "cognitive", "neural", "algorithm"],
        "machine": ["learning", "ai", "artificial", "algorithm", "model", "data", "training"],
        "learning": ["machine", "ai", "artificial", "algorithm", "model", "training", "neural"],
        "computer": ["science", "programming", "algorithm", "software", "technology", "coding"],
        "mathematics": ["math", "equation", "formula", "calculation", "number", "statistics"],
        "biology": ["life", "organism", "cell", "genetic", "evolution", "species", "living"],
        "physics": ["force", "energy", "matter", "quantum", "particle", "wave", "motion"],
        "chemistry": ["chemical", "reaction", "molecule", "compound", "element", "bond"]
    }
    
    relevance_bonus = 0
    
    # Check if any keyword has related terms in text
    for keyword in keywords:
        if keyword.lower() in subject_expansions:
            related_terms = subject_expansions[keyword.lower()]
            matches = sum(1 for term in related_terms if term in text_lower)
            relevance_bonus += matches * 5  # 5 points per related term
    
    # Check for general academic terms
    academic_terms = ["field", "domain", "study", "learn", "knowledge", "research", "theory", "concept"]
    academic_matches = sum(1 for term in academic_terms if term in text_lower)
    relevance_bonus += academic_matches * 2
    
    return min(relevance_bonus, 40.0)

def check_phi_relevance(ocr_text_300, subject, phi_model=None):
    """Check relevance using optimized Phi LLM (more lenient)"""
    phi_model = _get_phi_model()
    
    if phi_model:
        try:
            logger.info("Running optimized Phi-2 relevance analysis (layers 1-16)")
            prompt = f"""Rate how relevant this text is to the subject "{subject}" on a scale of 0-100:

Text: {ocr_text_300}
Subject: {subject}

Relevance score (0-100): """
            
            response = phi_model(
                prompt,
                max_tokens=10,
                temperature=0.1,
                stop=["</s>", "\n"]
            )
            
            response_text = response['choices'][0]['text'].strip()
            
            # Extract number from response
            import re
            match = re.search(r'(\d+)', response_text)
            if match:
                score = int(match.group(1))
                score = max(0, min(100, score))
                logger.info(f"✓ Optimized Phi-2 relevance score: {score}% (16-layer processing)")
                return float(score)
                
        except Exception as e:
            logger.error(f"Optimized Phi-2 relevance check error: {e}")
    
    # Enhanced fallback relevance analysis
    logger.info("Using enhanced fallback relevance analysis")
    return calculate_enhanced_fallback_relevance(ocr_text_300, subject)

def calculate_enhanced_fallback_relevance(text, subject):
    """Enhanced fallback relevance calculation"""
    text_lower = text.lower()
    subject_lower = subject.lower()
    
    base_score = 30.0  # Higher base score
    
    # Direct subject mention
    if subject_lower in text_lower:
        base_score += 30.0
    
    # Enhanced subject-related keywords with broader coverage
    subject_keywords = {
        "artificial intelligence": ["ai", "artificial", "intelligence", "machine", "learning", "algorithm", "model", "data", "neural", "deep", "computer", "technology", "automation"],
        "computer science": ["computer", "programming", "algorithm", "software", "code", "technology", "data", "system", "digital", "coding", "development"],
        "physics": ["quantum", "mechanics", "particle", "wave", "energy", "force", "matter", "motion", "physics", "scientific"],
        "chemistry": ["molecule", "atom", "reaction", "compound", "element", "chemical", "bond", "chemistry", "substance"],
        "biology": ["cell", "organism", "evolution", "gene", "dna", "life", "living", "species", "biological", "nature"],
        "mathematics": ["equation", "function", "theorem", "algebra", "geometry", "calculus", "math", "mathematical", "number", "formula", "statistics", "probability"],
        "machine learning": ["machine", "learning", "ai", "artificial", "algorithm", "model", "data", "training", "neural", "deep"],
        "data science": ["data", "analysis", "statistics", "machine", "learning", "algorithm", "model", "analytics", "science"]
    }
    
    # Find best matching subject category
    best_match_score = 0
    for category, keywords in subject_keywords.items():
        if any(term in subject_lower for term in category.split()):
            keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)
            match_score = min(keyword_matches * 8, 50.0)  # 8 points per keyword, max 50
            best_match_score = max(best_match_score, match_score)
    
    # Add general academic/technical terms bonus
    academic_terms = ["field", "domain", "opportunities", "learn", "study", "knowledge", "theory", "concept", "research", "development", "progress", "models", "powerful", "used", "applications"]
    academic_matches = sum(1 for term in academic_terms if term in text_lower)
    academic_bonus = min(academic_matches * 3, 20.0)
    
    final_score = base_score + best_match_score + academic_bonus
    
    logger.info(f"Enhanced fallback relevance score: {final_score}%")
    return round(min(final_score, 100.0), 2)

def calculate_final_relevance(keyword_score, phi_score):
    """Calculate final relevance score (more generous)"""
    # Take weighted average favoring the higher score
    if keyword_score > phi_score:
        final_score = (keyword_score * 0.7) + (phi_score * 0.3)
    else:
        final_score = (keyword_score * 0.3) + (phi_score * 0.7)
    
    # Apply minimum threshold for reasonable content
    final_score = max(final_score, 25.0)  # Minimum 25% for any coherent text
    
    logger.info(f"Final relevance calculation: weighted average = {final_score}%")
    return round(final_score, 2)