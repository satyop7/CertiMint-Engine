"""
Add enhanced detection functionality to main.py
"""
import os

def add_enhanced_detection():
    """Add enhanced detection functionality to main.py"""
    # Read the original file
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'r') as f:
        content = f.read()
    
    # Add code to use highest plagiarism score
    if "scores.sort(reverse=True)" in content:
        modified_content = content.replace(
            "scores.sort(reverse=True)\n            if len(scores) >= 2:\n                plagiarism_percentage = (scores[0] + scores[1]) / 2\n                llm_similarity = plagiarism_percentage\n            else:\n                plagiarism_percentage = plagiarism_results.get(\"plagiarism_percentage\", 0)\n                llm_similarity = plagiarism_results.get(\"llm_similarity\", 0)",
            "scores.sort(reverse=True)\n            if len(scores) >= 2:\n                # Use enhanced detection to get highest score\n                plagiarism_percentage = enhanced_detection.get_highest_plagiarism_score(plagiarism_results)\n                llm_similarity = plagiarism_percentage\n            else:\n                plagiarism_percentage = plagiarism_results.get(\"plagiarism_percentage\", 0)\n                llm_similarity = plagiarism_results.get(\"llm_similarity\", 0)"
        )
    else:
        modified_content = content
    
    # Add code to use enhanced relevance checking
    if "validation = self.llm.validate_content_semantic" in modified_content:
        modified_content = modified_content.replace(
            "validation = self.llm.validate_content_semantic(ocr_text, subject, self.reference_sources)",
            "# Try enhanced relevance checking first\n                            try:\n                                validation = enhanced_detection.check_relevance_with_models(ocr_text[:300], subject)\n                                logger.info(\"Used enhanced model-based relevance detection\")\n                            except Exception as e:\n                                logger.warning(f\"Enhanced relevance detection failed: {e}, falling back to standard method\")\n                                validation = self.llm.validate_content_semantic(ocr_text, subject, self.reference_sources)"
        )
    
    # Write the modified file
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'w') as f:
        f.write(modified_content)
    
    return "Added enhanced detection functionality to main.py"

if __name__ == "__main__":
    add_enhanced_detection()