"""
Groq API client for getting top repetitive words
"""
import requests
import json

def get_top_repetitive_words(subject, count=8):
    """Get top 8 repetitive words for a subject using Groq"""
    # Mock implementation - in real scenario, use Groq API
    subject_words = {
        "physics": ["quantum", "mechanics", "particle", "wave", "energy", "force", "motion", "field"],
        "chemistry": ["molecule", "atom", "reaction", "compound", "element", "bond", "acid", "base"],
        "biology": ["cell", "organism", "evolution", "gene", "dna", "protein", "species", "tissue"],
        "mathematics": ["equation", "function", "theorem", "proof", "algebra", "geometry", "calculus", "variable"],
        "computer science": ["algorithm", "data", "structure", "programming", "code", "software", "hardware", "network"]
    }
    
    return subject_words.get(subject.lower(), ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"])[:count]