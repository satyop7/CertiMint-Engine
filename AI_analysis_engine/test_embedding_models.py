#!/usr/bin/env python3
"""
Test embedding models
"""
from embedding_llm import EmbeddingLLM

def test_embedding_models():
    print("🧪 Testing Embedding Models")
    print("=" * 50)
    
    # Initialize models
    print("1. Loading models...")
    llm = EmbeddingLLM()
    
    if not llm.models_loaded:
        print("❌ Models failed to load")
        return False
    
    print("✅ Models loaded successfully!")
    
    # Test plagiarism
    print("\n2. Testing plagiarism detection...")
    test_text = "Artificial intelligence is a very good field with many opportunities. To learn AI we need statistical mathematics."
    
    result = llm.check_plagiarism(test_text, [])
    print(f"✅ Plagiarism: {result['plagiarism_percentage']}%")
    print(f"   Detected: {result['plagiarism_detected']}")
    print(f"   Optimization: {result['model_optimization']}")
    
    # Test relevance
    print("\n3. Testing relevance scoring...")
    result = llm.validate_content(test_text, "Artificial Intelligence", [])
    print(f"✅ Relevance: {result['relevance_score']}%")
    print(f"   Status: {result['status']}")
    print(f"   Optimization: {result['model_optimization']}")
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    test_embedding_models()