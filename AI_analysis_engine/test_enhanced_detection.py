"""
Test script for enhanced detection
"""
import enhanced_detection
import json

def test_enhanced_detection():
    """Test the enhanced detection module"""
    # Sample OCR text (first 300 chars from a quantum mechanics document)
    ocr_text = """Introduction to Quantum Mechanics
    
    Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science."""
    
    # Test subject
    subject = "Physics"
    
    # Test plagiarism results
    plagiarism_results = {
        "plagiarism_percentage": 45,
        "ai_confidence": 65,
        "top_features_score": 55,
        "llm_similarity": 50
    }
    
    # Test highest plagiarism score
    highest_score = enhanced_detection.get_highest_plagiarism_score(plagiarism_results)
    print(f"Highest plagiarism score: {highest_score}%")
    
    # Test relevance check
    relevance_results = enhanced_detection.check_relevance_with_models(ocr_text, subject)
    print(f"Relevance results: {json.dumps(relevance_results, indent=2)}")
    
    # Test repetitive phrases
    phrases = enhanced_detection.find_repetitive_phrases(ocr_text)
    print(f"Top repetitive phrases: {phrases}")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_enhanced_detection()