"""
Minimal AI pattern detector module
"""

def detect_patterns(text):
    """
    Detects AI patterns in text
    """
    # Simple implementation
    patterns = ["as an ai", "as an assistant", "as a language model"]
    detected = [p for p in patterns if p in text.lower()]
    return detected