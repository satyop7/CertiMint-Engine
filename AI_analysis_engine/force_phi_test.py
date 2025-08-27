#!/usr/bin/env python3
"""
Force Phi model to generate numbers
"""
import logging
from llm_loader import load_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('force_phi_test')

def force_phi_numbers():
    """Force Phi model to generate numeric responses"""
    
    print("🔧 Force Testing Phi-2 Model Numbers")
    print("=" * 50)
    
    # Load model
    model, loaded, error = load_model("phi-2.Q4_K_M.gguf")
    
    if not loaded:
        print(f"❌ Model loading failed: {error}")
        return False
    
    print("✅ Model loaded successfully!")
    
    # Test different prompts and parameters
    test_cases = [
        {
            "name": "Simple Math",
            "prompt": "2 + 2 = ",
            "params": {"max_tokens": 3, "temperature": 0.1, "stop": [" "]}
        },
        {
            "name": "Number Completion",
            "prompt": "The number is 4",
            "params": {"max_tokens": 5, "temperature": 0.3, "stop": ["\n"]}
        },
        {
            "name": "Score Format",
            "prompt": "Score: ",
            "params": {"max_tokens": 3, "temperature": 0.5, "stop": ["\n", " "]}
        },
        {
            "name": "Percentage",
            "prompt": "25",
            "params": {"max_tokens": 3, "temperature": 0.7, "stop": ["\n"]}
        },
        {
            "name": "Direct Number",
            "prompt": "42",
            "params": {"max_tokens": 1, "temperature": 0.0, "stop": []}
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        print(f"  Prompt: '{test['prompt']}'")
        
        try:
            response = model(test['prompt'], **test['params'])
            result = response['choices'][0]['text']
            print(f"  Response: '{result}'")
            print(f"  Length: {len(result)}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Test with different approaches
    print("\n" + "="*30)
    print("TESTING PLAGIARISM FORMATS")
    print("="*30)
    
    plagiarism_tests = [
        "Text plagiarism: 25%",
        "25",
        "Plagiarism score is 30",
        "30%",
        "Score 40",
        "The plagiarism percentage is 35"
    ]
    
    for i, prompt in enumerate(plagiarism_tests):
        print(f"\nTest {i+1}: '{prompt}'")
        try:
            response = model(
                prompt,
                max_tokens=10,
                temperature=0.8,
                top_p=0.95,
                stop=["\n", ".", "!", "?"]
            )
            result = response['choices'][0]['text']
            print(f"  Response: '{result}'")
            
            # Extract numbers
            import re
            numbers = re.findall(r'\d+', result)
            if numbers:
                print(f"  Numbers found: {numbers}")
            else:
                print(f"  No numbers found")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    return True

if __name__ == "__main__":
    force_phi_numbers()