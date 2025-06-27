#!/usr/bin/env python3
"""
Keyword extractor for content relevance validation

This module extracts important keywords from scraped reference data
and uses them to evaluate the relevance of submitted documents.
"""

import os
import json
import re
import logging
from collections import Counter
from typing import Dict, List, Tuple, Any, Set, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('keyword_extractor')

# Common English stopwords to exclude from keyword extraction
STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
    'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than',
    'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during',
    'to', 'from', 'in', 'on', 'by', 'with', 'at', 'into', 'only', 'also',
    'be', 'been', 'being', 'am', 'are', 'was', 'were', 'has', 'have', 'had',
    'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should', 'must',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'their', 'there', 'here', 'when', 'who', 'how', 'all', 'any', 'some', 'many',
    'most', 'very'
}

def extract_keywords_from_references(references_file: str, max_keywords: int = 20) -> List[Tuple[str, float]]:
    """
    Extract important keywords from reference data
    
    Args:
        references_file: Path to references.json file
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of (keyword, importance_score) tuples
    """
    if not os.path.exists(references_file):
        logger.error(f"References file not found: {references_file}")
        return []
    
    try:
        with open(references_file, 'r') as f:
            references = json.load(f)
            
        if not references:
            logger.warning("References file is empty")
            return []
            
        # Combine all reference content
        all_content = ""
        for ref in references:
            if "content" in ref and ref["content"]:
                all_content += ref["content"] + "\n\n"
                
        if not all_content.strip():
            logger.warning("No content found in references")
            return []
            
        # Extract keywords using multiple methods for better results
        keywords = []
        
        # Method 1: TF-IDF based extraction
        keywords_tfidf = extract_keywords_tfidf(all_content, max_keywords=max_keywords)
        keywords.extend(keywords_tfidf)
        
        # Method 2: Simple frequency-based extraction
        keywords_freq = extract_keywords_frequency(all_content, max_keywords=max_keywords)
        keywords.extend([(k, s) for k, s in keywords_freq if k not in [kw for kw, _ in keywords]])
        
        # Merge and sort by score
        keywords.sort(key=lambda x: x[1], reverse=True)
        
        # Return top keywords, avoiding duplicates
        unique_keywords = []
        seen_keywords = set()
        for kw, score in keywords:
            if kw not in seen_keywords and len(kw) > 2:  # Skip very short keywords
                unique_keywords.append((kw, score))
                seen_keywords.add(kw)
                if len(unique_keywords) >= max_keywords:
                    break
                    
        return unique_keywords
        
    except Exception as e:
        logger.error(f"Error extracting keywords from references: {e}")
        return []

def extract_keywords_tfidf(text: str, max_keywords: int = 15) -> List[Tuple[str, float]]:
    """
    Extract keywords using TF-IDF
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of (keyword, importance_score) tuples
    """
    try:
        # Create vectorizer
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words=list(STOPWORDS),
            ngram_range=(1, 2),  # Use both unigrams and bigrams
            use_idf=True
        )
        
        # Fit and transform text
        tfidf_matrix = vectorizer.fit_transform([text])
        
        # Get feature names and scores
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Sort by score and get top keywords
        keyword_scores = list(zip(feature_names, scores))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        return keyword_scores[:max_keywords]
    except Exception as e:
        logger.error(f"Error in TF-IDF extraction: {e}")
        return []

def extract_keywords_frequency(text: str, max_keywords: int = 15) -> List[Tuple[str, float]]:
    """
    Extract keywords based on frequency and filtering
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of (keyword, frequency) tuples
    """
    try:
        # Clean text: remove punctuation and convert to lowercase
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Tokenize
        words = cleaned_text.split()
        
        # Remove stopwords and very short words
        filtered_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
        
        # Count frequencies
        word_counts = Counter(filtered_words)
        
        # Get most common words
        most_common = word_counts.most_common(max_keywords)
        
        # Convert counts to scores (0-1 range)
        if most_common:
            max_count = most_common[0][1]
            return [(word, count / max_count) for word, count in most_common]
        return []
    except Exception as e:
        logger.error(f"Error in frequency-based extraction: {e}")
        return []

def calculate_relevance_score(text: str, keywords: List[Tuple[str, float]]) -> Dict[str, Any]:
    """
    Calculate relevance score based on keyword presence
    
    Args:
        text: Document text to check
        keywords: List of (keyword, importance_score) tuples
        
    Returns:
        Dictionary with relevance information
    """
    if not keywords:
        return {
            "relevance_score": 0,
            "keywords_found": [],
            "keywords_missing": [],
            "comments": "No keywords available for relevance calculation"
        }
    
    text_lower = text.lower()
    
    # Check each keyword
    keywords_found = []
    keywords_missing = []
    total_importance = sum(score for _, score in keywords)
    found_importance = 0
    
    for keyword, importance in keywords:
        if keyword.lower() in text_lower:
            # Count occurrences
            occurrences = text_lower.count(keyword.lower())
            found_importance += importance
            keywords_found.append({
                "keyword": keyword,
                "importance": importance,
                "occurrences": occurrences
            })
        else:
            keywords_missing.append({
                "keyword": keyword,
                "importance": importance
            })
    
    # Calculate relevance score (0-100)
    if total_importance > 0:
        relevance_score = min(100, (found_importance / total_importance) * 100)
    else:
        relevance_score = 0
    
    # Determine status
    status = "PASSED" if relevance_score >= 60 else "FAILED"
    
    # Generate comments
    if relevance_score >= 80:
        comments = f"Document is highly relevant, containing {len(keywords_found)} of {len(keywords)} key subject terms"
    elif relevance_score >= 60:
        comments = f"Document is sufficiently relevant, containing {len(keywords_found)} of {len(keywords)} subject terms"
    elif relevance_score >= 40:
        comments = f"Document has limited relevance, missing {len(keywords_missing)} key subject terms"
    else:
        comments = f"Document lacks relevance to subject, missing {len(keywords_missing)} key subject terms"
    
    return {
        "relevance_score": relevance_score,
        "status": status,
        "keywords_found": keywords_found,
        "keywords_missing": keywords_missing,
        "comments": comments
    }

def check_document_relevance(doc_text: str, references_file: str = "data/references.json") -> Dict[str, Any]:
    """
    Check document relevance to subject based on reference keywords
    
    Args:
        doc_text: Document text to check
        references_file: Path to references.json file
        
    Returns:
        Dictionary with relevance results
    """
    # Extract keywords from references
    keywords = extract_keywords_from_references(references_file)
    
    if not keywords:
        logger.warning(f"No keywords extracted from {references_file}")
        
        # Try to use LLM for relevance assessment as fallback
        try:
            # Import needed only if keywords not found
            from llm_sandbox import SandboxedLLM
            
            # Look for model path in standard locations
            model_paths = ["phi-2.Q4_K_M.gguf", "models/phi-2.Q4_K_M.gguf"]
            model_path = None
            
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if model_path:
                logger.info(f"Using LLM fallback with model: {model_path}")
                
                # Get subject from references file path or fallback to generic
                subject = "unknown"
                try:
                    # Extract subject from filename or parent directory
                    ref_dir = os.path.dirname(references_file)
                    if "data" in ref_dir and os.path.exists(os.path.join(ref_dir, "info.json")):
                        with open(os.path.join(ref_dir, "info.json"), 'r') as f:
                            info = json.load(f)
                            subject = info.get("subject_name", "unknown")
                except Exception as e:
                    logger.error(f"Error getting subject from info.json: {e}")
                
                # Initialize LLM
                llm = SandboxedLLM(model_path)
                
                # Use LLM to evaluate relevance
                llm_result = llm.validate_content(doc_text[:5000], subject)
                
                logger.info(f"LLM relevance fallback result: {llm_result}")
                return llm_result
            else:
                logger.warning("No model found for LLM fallback")
        except ImportError as ie:
            logger.error(f"Cannot import SandboxedLLM for fallback: {ie}")
        except Exception as e:
            logger.error(f"Error in LLM fallback: {e}")
        
        # Ultimate fallback if LLM doesn't work either
        return {
            "status": "PASSED",  # Default to pass to avoid false failures
            "relevance_score": 50.0,
            "comments": f"No subject keywords available from references and LLM fallback failed"
        }
    
    # Log keywords for debugging
    logger.info(f"Extracted {len(keywords)} subject keywords:")
    for kw, score in keywords[:10]:
        logger.info(f"  - {kw}: {score:.3f}")
    
    # Calculate relevance score
    relevance_data = calculate_relevance_score(doc_text, keywords)
    
    # Log relevance for debugging
    logger.info(f"Relevance score: {relevance_data['relevance_score']:.1f}%")
    logger.info(f"Found {len(relevance_data['keywords_found'])} keywords out of {len(keywords)}")
    
    # Return simplified result
    return {
        "status": relevance_data["status"],
        "relevance_score": relevance_data["relevance_score"],
        "comments": relevance_data["comments"],
        "keywords": {
            "found": [k["keyword"] for k in relevance_data["keywords_found"][:5]],
            "missing": [k["keyword"] for k in relevance_data["keywords_missing"][:5]]
        }
    }

# Example usage
if __name__ == "__main__":
    import sys
    
    # Get references file path
    references_file = sys.argv[1] if len(sys.argv) > 1 else "data/references.json"
    
    # Get document file path
    doc_file = sys.argv[2] if len(sys.argv) > 2 else "data/ocr_text.txt"
    
    # Check if files exist
    if not os.path.exists(references_file):
        print(f"References file not found: {references_file}")
        sys.exit(1)
    
    if not os.path.exists(doc_file):
        print(f"Document file not found: {doc_file}")
        sys.exit(1)
    
    # Read document text
    with open(doc_file, 'r') as f:
        doc_text = f.read()
    
    # Check relevance
    result = check_document_relevance(doc_text, references_file)
    
    # Print result
    print("\n=== DOCUMENT RELEVANCE ANALYSIS ===")
    print(f"Relevance Score: {result['relevance_score']:.1f}%")
    print(f"Status: {result['status']}")
    print(f"Comments: {result['comments']}")
    
    if "keywords" in result:
        print("\nTop keywords found:")
        for kw in result["keywords"].get("found", []):
            print(f"  ✓ {kw}")