"""
Test plagiarism detection directly
"""
import json
import datetime
from advanced_plagiarism_algorithms import calculate_advanced_plagiarism

# Test with sample text
ocr_text = """Introduction to Quantum Mechanics

Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles. It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science.

Classical physics, the collection of theories that existed before the advent of quantum mechanics, describes many aspects of nature at an ordinary (macroscopic) scale, but is not sufficient for describing them at small (atomic and subatomic) scales. Most theories in classical physics can be derived from quantum mechanics as an approximation valid at large (macroscopic) scale."""

reference_content = "Physics is the natural science that studies matter, its motion and behavior through space and time, and the related entities of energy and force."

groq_words = ["quantum", "mechanics", "physics", "particle", "wave", "energy", "force", "motion"]

# Run plagiarism detection
print("Testing advanced plagiarism detection...")
results = calculate_advanced_plagiarism(ocr_text, reference_content, groq_words)

print(f"Plagiarism Score: {results['plagiarism_percentage']}%")
print(f"AI Confidence: {results['ai_confidence']}%")
print(f"Feature Scores: {results['feature_scores']}")

# Create result structure
result = {
    "subject": "Geography",
    "assignment_id": "1",
    "username": "Vicky",
    "timestamp": datetime.datetime.now().isoformat(),
    "status": "FAILED",
    "sandbox_mode": True,
    "ocr_text_length": len(ocr_text),
    "ocr_text_preview": ocr_text[:200] + "...",
    "plagiarism_check": {
        "plagiarism_detected": results['plagiarism_percentage'] > 35.0,
        "plagiarism_percentage": results['plagiarism_percentage'],
        "ai_patterns_detected": results['ai_confidence'] > 40.0,
        "ai_confidence": results['ai_confidence'],
        "ai_patterns": {
            "explicit_patterns": [],
            "feature_scores": results['feature_scores']
        },
        "semantic_similarity": results['semantic_similarity'],
        "statistical_similarity": results['statistical_similarity'],
        "ngram_similarity": results['ngram_similarity'],
        "top_features_score": results['top_features_score']
    },
    "content_validation": {
        "status": "FAILED",
        "relevance_score": 15.0,
        "comments": "Content not relevant to Geography"
    },
    "failure_reasons": [
        f"High plagiarism detected ({results['plagiarism_percentage']}%)",
        "Content not sufficiently relevant to Geography (15.0%)"
    ]
}

# Save as result.json
import os
os.makedirs("result", exist_ok=True)
with open('result/result.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f"Result saved to result/result.json")
print(f"Final plagiarism score: {results['plagiarism_percentage']}%")