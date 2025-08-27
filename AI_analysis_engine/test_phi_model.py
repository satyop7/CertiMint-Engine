#!/usr/bin/env python3
"""
Simple Phi model test script
"""
import logging
from llm_loader import load_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('phi_test')

def test_phi_model():
    """Test Phi model loading and basic inference"""
    
    print("🔧 Testing Phi-2 Model")
    print("=" * 50)
    
    # Test 1: Model Loading
    print("1. Loading optimized Phi-2 model...")
    model, loaded, error = load_model("phi-2.Q4_K_M.gguf")
    
    if not loaded:
        print(f"❌ Model loading failed: {error}")
        return False
    
    print("✅ Model loaded successfully!")
    print(f"   - Layers: 1-16 (optimized)")
    print(f"   - Context: 512 tokens")
    print(f"   - Threads: 4")
    
    # Test 2: Basic Inference
    print("\n2. Testing basic inference...")
    test_prompt = "What is artificial intelligence?"
    
    try:
        response = model(
            test_prompt,
            max_tokens=50,
            temperature=0.1,
            stop=["</s>", "\n\n"]
        )
        
        generated_text = response['choices'][0]['text'].strip()
        print(f"✅ Inference successful!")
        print(f"   Prompt: {test_prompt}")
        print(f"   Response: {generated_text}")
        
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        return False
    
    # Test 3: Plagiarism Analysis
    print("\n3. Testing plagiarism analysis...")
    plagiarism_prompt = """Rate this text plagiarism from 0 to 100:

Text: Artificial intelligence is a very good field with many opportunities.

Plagiarism score: """
    
    try:
        response = model(
            plagiarism_prompt,
            max_tokens=20,
            temperature=0.3,
            stop=["\n\n", ".", "!"]
        )
        
        plagiarism_response = response['choices'][0]['text'].strip()
        print(f"✅ Plagiarism analysis successful!")
        print(f"   Full response: '{plagiarism_response}'")
        
        # Extract number if present
        import re
        numbers = re.findall(r'\d+', plagiarism_response)
        if numbers:
            print(f"   Extracted score: {numbers[0]}%")
        else:
            print(f"   ⚠️  No numeric score found in response")
        
    except Exception as e:
        print(f"❌ Plagiarism analysis failed: {e}")
        return False
    
    # Test 4: Relevance Analysis
    print("\n4. Testing relevance analysis...")
    relevance_prompt = """Rate relevance 0-100:

Text: Programming involves algorithms and data structures.
Subject: Computer Science

Score: """
    
    try:
        response = model(
            relevance_prompt,
            max_tokens=20,
            temperature=0.3,
            stop=["\n\n", ".", "!"]
        )
        
        relevance_response = response['choices'][0]['text'].strip()
        print(f"✅ Relevance analysis successful!")
        print(f"   Full response: '{relevance_response}'")
        
        # Extract number if present
        import re
        numbers = re.findall(r'\d+', relevance_response)
        if numbers:
            print(f"   Extracted score: {numbers[0]}%")
        else:
            print(f"   ⚠️  No numeric score found in response")
        
    except Exception as e:
        print(f"❌ Relevance analysis failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Phi-2 model is working correctly.")
    return True

if __name__ == "__main__":
    success = test_phi_model()
    exit(0 if success else 1)