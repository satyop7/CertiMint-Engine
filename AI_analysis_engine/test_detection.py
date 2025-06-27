"""
Test script for enhanced detection
"""
import enhanced_detection

def test_detection():
    """Test the enhanced detection module"""
    # Sample OCR text
    ocr_text = """Introduction to Quantum Mechanics
    
    Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science."""
    
    # Test subjects
    subjects = ["Physics", "Chemistry"]
    
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
    
    # Test relevance check for each subject
    for subject in subjects:
        print(f"\nTesting relevance for subject: {subject}")
        relevance_results = enhanced_detection.check_relevance_with_models(ocr_text, subject)
        print(f"Status: {relevance_results['status']}")
        print(f"Score: {relevance_results['relevance_score']}%")
        print(f"Phi score: {relevance_results['phi_score']}%")
        print(f"Groq score: {relevance_results['groq_score']}%")
        print(f"Comments: {relevance_results['comments']}")
        print(f"Top phrases: {relevance_results['repetitive_phrases'][:3]}")

if __name__ == "__main__":
    test_detection()