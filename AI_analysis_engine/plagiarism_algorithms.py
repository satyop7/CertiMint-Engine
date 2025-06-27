"""
Advanced plagiarism detection algorithms with decimal precision
"""
import re
from collections import Counter
import math

def calculate_precise_plagiarism(ocr_text, reference_content, groq_words):
    """Calculate plagiarism with decimal precision using multiple algorithms"""
    
    # Algorithm 1: N-gram similarity
    ngram_score = calculate_ngram_similarity(ocr_text, reference_content)
    
    # Algorithm 2: Keyword density analysis
    keyword_score = calculate_keyword_density(ocr_text, groq_words)
    
    # Algorithm 3: Semantic pattern matching
    pattern_score = calculate_pattern_matching(ocr_text, reference_content)
    
    # Algorithm 4: Statistical analysis
    statistical_score = calculate_statistical_similarity(ocr_text, reference_content)
    
    # Combine scores with weights
    final_score = (ngram_score * 0.3 + keyword_score * 0.25 + pattern_score * 0.25 + statistical_score * 0.2)
    
    return round(final_score, 2)

def calculate_ngram_similarity(text1, text2):
    """Calculate n-gram similarity"""
    words1 = re.findall(r'\b\w+\b', text1.lower())
    words2 = re.findall(r'\b\w+\b', text2.lower())
    
    # Create trigrams
    trigrams1 = [' '.join(words1[i:i+3]) for i in range(len(words1)-2)]
    trigrams2 = [' '.join(words2[i:i+3]) for i in range(len(words2)-2)]
    
    if not trigrams1 or not trigrams2:
        return 0.0
    
    # Calculate Jaccard similarity
    set1, set2 = set(trigrams1), set(trigrams2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return (intersection / union * 100) if union > 0 else 0.0

def calculate_keyword_density(text, keywords):
    """Calculate keyword density score"""
    text_lower = text.lower()
    total_words = len(re.findall(r'\b\w+\b', text_lower))
    
    if total_words == 0:
        return 0.0
    
    keyword_count = sum(text_lower.count(keyword.lower()) for keyword in keywords)
    density = (keyword_count / total_words) * 100
    
    return min(density * 10, 100.0)  # Scale and cap at 100

def calculate_pattern_matching(text1, text2):
    """Calculate pattern matching score"""
    # Simple pattern matching based on sentence structure
    sentences1 = re.split(r'[.!?]+', text1)
    sentences2 = re.split(r'[.!?]+', text2)
    
    if not sentences1 or not sentences2:
        return 0.0
    
    matches = 0
    for s1 in sentences1[:5]:  # Check first 5 sentences
        s1_words = set(re.findall(r'\b\w+\b', s1.lower()))
        for s2 in sentences2[:5]:
            s2_words = set(re.findall(r'\b\w+\b', s2.lower()))
            if len(s1_words.intersection(s2_words)) >= 3:
                matches += 1
                break
    
    return (matches / min(len(sentences1), len(sentences2), 5)) * 100

def calculate_statistical_similarity(text1, text2):
    """Calculate statistical similarity"""
    words1 = re.findall(r'\b\w+\b', text1.lower())
    words2 = re.findall(r'\b\w+\b', text2.lower())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate word frequency distributions
    freq1 = Counter(words1)
    freq2 = Counter(words2)
    
    # Calculate cosine similarity
    common_words = set(freq1.keys()).intersection(set(freq2.keys()))
    
    if not common_words:
        return 0.0
    
    dot_product = sum(freq1[word] * freq2[word] for word in common_words)
    magnitude1 = math.sqrt(sum(freq1[word]**2 for word in freq1))
    magnitude2 = math.sqrt(sum(freq2[word]**2 for word in freq2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    cosine_sim = dot_product / (magnitude1 * magnitude2)
    return cosine_sim * 100