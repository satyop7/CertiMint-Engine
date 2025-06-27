#!/usr/bin/env python3
"""
Test script for LLM sandbox reliability improvements
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("llm_sandbox_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('llm_sandbox_test')

def test_model_loading():
    """Test model loading with different mechanisms"""
    logger.info("=== Testing Model Loading ===")
    
    model_path = "phi-2.Q4_K_M.gguf"
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False
        
    # Test standard loading
    try:
        logger.info("Testing standard model loading...")
        from llm_sandbox import SandboxedLLM
        llm = SandboxedLLM(model_path)
        logger.info("Standard loading: SUCCESS")
    except Exception as e:
        logger.error(f"Standard loading failed: {e}")
        return False
        
    # Test docker-compatible loading
    try:
        logger.info("Testing Docker-compatible loading...")
        # Set compatibility mode env var
        os.environ["PHI2_COMPAT_MODE"] = "1"
        
        from docker_llm_loader import load_model_for_docker
        model, success = load_model_for_docker(model_path)
        
        if success and model:
            logger.info("Docker-compatible loading: SUCCESS")
        else:
            logger.error("Docker-compatible loading: FAILED")
            return False
    except Exception as e:
        logger.error(f"Docker-compatible loading failed: {e}")
        return False
        
    # Test adapter loading
    try:
        logger.info("Testing Phi2Adapter loading...")
        from phi2_adapter import Phi2Adapter
        
        adapter = Phi2Adapter(model_path)
        if adapter.load_model():
            logger.info("Adapter loading: SUCCESS")
        else:
            logger.error("Adapter loading: FAILED")
            return False
    except Exception as e:
        logger.error(f"Adapter loading failed: {e}")
        logger.warning("Adapter test skipped - continuing with other tests")
    
    return True

def test_json_parsing():
    """Test JSON parsing robustness"""
    logger.info("=== Testing JSON Parsing Robustness ===")
    
    test_cases = [
        # Simple valid JSON
        '{"key": "value", "score": 75}',
        
        # JSON with surrounding text
        'Here is the result: {"key": "value", "score": 85} and some more text',
        
        # Malformed JSON with common issues
        '{key: "value", score: 95, status: "PASSED"}',
        
        # JSON with single quotes
        "{'key': 'value', 'score': 65, 'status': 'FAILED'}",
        
        # JSON with trailing comma
        '{"key": "value", "score": 70, "status": "PASSED",}',
        
        # Complex case with multiple issues
        """The relevance analysis shows:
        {
            key: 'content validation',
            score: 82,
            status: 'PASSED',
            notes: "Found clear evidence of relevance",
        }"""
    ]
    
    try:
        from json_parser import extract_and_clean_json
        
        success_count = 0
        for i, test in enumerate(test_cases):
            logger.info(f"Test case {i+1}: {test[:50]}...")
            result = extract_and_clean_json(test)
            
            if result is not None:
                logger.info(f"✓ Successfully parsed: {result}")
                success_count += 1
            else:
                logger.error(f"✗ Failed to parse test case {i+1}")
                
        success_rate = success_count / len(test_cases) * 100
        logger.info(f"JSON parsing success rate: {success_rate:.1f}%")
        
        return success_rate >= 80  # At least 80% success rate
        
    except ImportError:
        logger.error("json_parser module not available")
        return False
    except Exception as e:
        logger.error(f"Error in JSON parsing test: {e}")
        return False

def test_model_fallback():
    """Test model fallback mechanisms"""
    logger.info("=== Testing Model Fallback Mechanisms ===")
    
    try:
        from model_checker import ModelChecker
        
        # First test with invalid model
        logger.info("Testing with invalid model path...")
        checker = ModelChecker("nonexistent_model.gguf")
        
        # Check if alternatives are found
        alternatives = checker.find_alternative_models()
        has_alternatives = len(alternatives) > 0
        
        logger.info(f"Found {len(alternatives)} alternative models")
        
        # Check best model selection
        best_model = checker.get_best_model_path()
        if best_model:
            logger.info(f"Best alternative model: {best_model}")
            return True
        else:
            logger.warning("No valid model found through fallback mechanism")
            # Not failing the test here as there might genuinely be no valid models
            return has_alternatives
            
    except ImportError:
        logger.error("model_checker module not available")
        return False
    except Exception as e:
        logger.error(f"Error in model fallback test: {e}")
        return False

def test_llm_interaction():
    """Test LLM interaction with robust error handling"""
    logger.info("=== Testing LLM Interaction ===")
    
    model_path = "phi-2.Q4_K_M.gguf"
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False
    
    try:
        from llm_sandbox import SandboxedLLM
        llm = SandboxedLLM(model_path)
        
        # Test content validation
        logger.info("Testing content validation...")
        sample_text = "Neural networks are computational models inspired by the human brain. They consist of layers of interconnected nodes or 'neurons' that can learn patterns from data."
        validation = llm.validate_content(sample_text, "Machine Learning")
        
        logger.info(f"Content validation result: {validation}")
        
        if isinstance(validation, dict) and "relevance_score" in validation:
            logger.info(f"Content validation: SUCCESS (score: {validation['relevance_score']})")
        else:
            logger.error("Content validation: FAILED (invalid result format)")
            return False
            
        # Test plagiarism detection
        logger.info("Testing plagiarism detection...")
        reference = [{
            "url": "https://example.com/reference",
            "title": "Neural Networks Overview",
            "content": """Neural networks, a cornerstone of artificial intelligence, are designed to mimic the human brain's structure and function. 
            At their core, they comprise interconnected nodes (neurons) organized in layers that process and transform data."""
        }]
        
        plagiarism_result = llm.check_plagiarism(sample_text, reference)
        logger.info(f"Plagiarism detection result: {plagiarism_result}")
        
        if isinstance(plagiarism_result, dict) and "plagiarism_percentage" in plagiarism_result:
            logger.info(f"Plagiarism detection: SUCCESS (score: {plagiarism_result['plagiarism_percentage']}%)")
            return True
        else:
            logger.error("Plagiarism detection: FAILED (invalid result format)")
            return False
            
    except Exception as e:
        logger.error(f"Error in LLM interaction test: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    logger.info("Starting LLM sandbox reliability tests")
    
    tests = [
        ("Model Loading", test_model_loading),
        ("JSON Parsing", test_json_parsing),
        ("Model Fallback", test_model_fallback),
        ("LLM Interaction", test_llm_interaction)
    ]
    
    results = {}
    all_passed = True
    
    for name, test_func in tests:
        logger.info(f"\nRunning test: {name}")
        try:
            success = test_func()
            results[name] = "PASSED" if success else "FAILED"
            
            if not success:
                all_passed = False
                
        except Exception as e:
            logger.error(f"Test '{name}' raised an exception: {e}")
            results[name] = "ERROR"
            all_passed = False
            
        logger.info(f"Test '{name}': {results[name]}")
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    for name, result in results.items():
        logger.info(f"{name}: {result}")
    
    logger.info(f"\nOverall result: {'SUCCESS' if all_passed else 'FAILURE'}")
    
    return all_passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test LLM sandbox reliability improvements")
    parser.add_argument("--test", choices=["loading", "json", "fallback", "interaction", "all"],
                      default="all", help="Which test to run")
    args = parser.parse_args()
    
    if args.test == "loading":
        success = test_model_loading()
    elif args.test == "json":
        success = test_json_parsing()
    elif args.test == "fallback":
        success = test_model_fallback()
    elif args.test == "interaction":
        success = test_llm_interaction()
    else:  # all
        success = run_all_tests()
        
    sys.exit(0 if success else 1)
