"""
Patch script to modify main.py to use enhanced detection
"""
import re
import os

def patch_main_py():
    """Add enhanced detection to main.py"""
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'r') as f:
        content = f.read()
    
    # Add import for enhanced_detection
    if 'import enhanced_detection' not in content:
        content = content.replace(
            'import re',
            'import re\nimport enhanced_detection'
        )
    
    # Replace plagiarism check section
    plagiarism_pattern = r'# Extract all plagiarism and AI detection information.*?scores\.sort\(reverse=True\)'
    replacement = """# Extract all plagiarism and AI detection information using enhanced detection
            # Get highest plagiarism score
            plagiarism_percentage = enhanced_detection.get_highest_plagiarism_score(plagiarism_results)
            llm_similarity = plagiarism_percentage"""
    
    content = re.sub(plagiarism_pattern, replacement, content, flags=re.DOTALL)
    
    # Replace content validation section
    validation_pattern = r'try:\s+validation = self\.llm\.validate_content_semantic.*?except Exception as e:'
    replacement = """try:
                        # Use enhanced detection for relevance checking
                        validation = enhanced_detection.check_relevance_with_models(ocr_text[:300], subject)
                        logger.info("Used enhanced model-based relevance detection")
                    except Exception as e:"""
    
    content = re.sub(validation_pattern, replacement, content, flags=re.DOTALL)
    
    # Write modified content back
    with open('/home/rick/projects/llama-sandbox-clean/main.py', 'w') as f:
        f.write(content)
    
    return "Added enhanced detection to main.py"

if __name__ == "__main__":
    patch_main_py()