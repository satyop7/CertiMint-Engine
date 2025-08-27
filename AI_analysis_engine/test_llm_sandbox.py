#!/usr/bin/env python3
"""
Test LLM Sandbox with Phi model
"""
import logging
from llm_sandbox import SandboxedLLM

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sandbox_test')

def test_llm_sandbox():
    """Test SandboxedLLM class with Phi model"""
    
    print("🧪 Testing LLM Sandbox")
    print("=" * 50)
    
    # Initialize sandbox
    print("1. Initializing SandboxedLLM...")
    llm = SandboxedLLM("phi-2.Q4_K_M.gguf")
    
    if not llm.model_loaded:
        print(f"❌ Sandbox initialization failed: {llm.error}")
        print("🔄 Testing fallback mode...")
    else:
        print("✅ Sandbox initialized successfully!")
    
    # Test plagiarism check
    print("\n2. Testing plagiarism check...")
    test_text = """Artificial intelligence is a very good field with many opportunities. 
    To learn Artificial intelligence we need to learn statistical mathematics like std. deviation, 
    linear equation, probability etc. --created by sambhranta ghosh, b.tech : cse ,(2023-2027)"""
    
    try:
        plagiarism_result = llm.check_plagiarism(test_text, [])
        print("✅ Plagiarism check successful!")
        print(f"   Plagiarism detected: {plagiarism_result['plagiarism_detected']}")
        print(f"   Plagiarism percentage: {plagiarism_result['plagiarism_percentage']}%")
        print(f"   AI confidence: {plagiarism_result['ai_confidence']}%")
        print(f"   Model optimization: {plagiarism_result['model_optimization']}")
        
    except Exception as e:
        print(f"❌ Plagiarism check failed: {e}")
        return False
    
    # Test content validation
    print("\n3. Testing content validation...")
    test_subject = "Artificial Intelligence"
    
    try:
        validation_result = llm.validate_content(test_text[:300], test_subject, [])
        print("✅ Content validation successful!")
        print(f"   Status: {validation_result['status']}")
        print(f"   Relevance score: {validation_result['relevance_score']}%")
        print(f"   Comments: {validation_result['comments']}")
        print(f"   Model optimization: {validation_result['model_optimization']}")
        
    except Exception as e:
        print(f"❌ Content validation failed: {e}")
        return False
    
    # Test with different subjects
    print("\n4. Testing with different subjects...")
    subjects = ["Computer Science", "Mathematics", "Physics", "Biology"]
    
    for subject in subjects:
        try:
            result = llm.validate_content(test_text[:200], subject, [])
            print(f"   {subject}: {result['relevance_score']}% relevant")
        except Exception as e:
            print(f"   {subject}: Error - {e}")
    
    print("\n🎉 LLM Sandbox tests completed!")
    return True

if __name__ == "__main__":
    success = test_llm_sandbox()
    exit(0 if success else 1)