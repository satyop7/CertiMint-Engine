#!/usr/bin/env python3
"""
Docker-compatible LLM loader for reliable model loading in container environments

This module handles the complexities of loading LLMs in Docker containers,
where memory constraints and compatibility issues can cause problems.
"""
import os
import sys
import time
import logging
from typing import Tuple, Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('docker_llm_loader')

def load_model_for_docker(model_path: str, 
                          max_attempts: int = 3, 
                          minimal_mode: bool = False) -> Tuple[Optional[Any], bool]:
    """
    Load a model in a Docker-compatible way with multiple strategies
    
    Args:
        model_path: Path to the model file
        max_attempts: Maximum number of loading attempts
        minimal_mode: If True, use minimal parameters for constrained environments
        
    Returns:
        Tuple of (model_object, success_status)
    """
    logger.info(f"Loading model {model_path} in Docker-compatible mode")
    
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return None, False
        
    # Check model file size and permissions
    try:
        file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        logger.info(f"Model size: {file_size_mb:.2f} MB")
        
        if not os.access(model_path, os.R_OK):
            logger.warning(f"Fixing model file permissions for {model_path}")
            os.chmod(model_path, 0o644)
    except Exception as e:
        logger.error(f"Error checking model file: {e}")
        return None, False
        
    # Try different loading strategies
    strategies = []
    
    # Determine system constraints
    ram_gb = _get_available_ram_gb()
    logger.info(f"Available RAM: ~{ram_gb:.1f} GB")
    is_memory_constrained = ram_gb < 8
    
    # Select strategies based on environment
    if minimal_mode or is_memory_constrained:
        strategies = [
            {"desc": "Minimal params for constrained environments", 
             "module": "llama_cpp", 
             "class": "Llama",
             "params": {
                "model_path": model_path,
                "n_ctx": 512,  # Very small context
                "n_batch": 8,  # Small batch size
                "n_gpu_layers": 0  # CPU only
             }},
            {"desc": "Basic params, no model type", 
             "module": "llama_cpp", 
             "class": "Llama",
             "params": {
                "model_path": model_path,
                "n_ctx": 1024,
                "n_batch": 64
             }},
        ]
    else:
        # Standard strategies for normal environments
        strategies = [
            {"desc": "Default Docker-compatible params", 
             "module": "llama_cpp", 
             "class": "Llama",
             "params": {
                "model_path": model_path,
                "n_ctx": 2048,
                "n_batch": 512,
                "n_gpu_layers": -1  # Auto-detect
             }},
            {"desc": "Using Phi-2 adapter", 
             "module": "phi2_adapter", 
             "class": "Phi2Adapter",
             "is_adapter": True,
             "params": {
                "model_path": model_path
             }}
        ]
    
    # Add fallback strategies for all environments
    fallback_strategies = [
        {"desc": "Basic params with phi2 model type", 
         "module": "llama_cpp", 
         "class": "Llama",
         "params": {
            "model_path": model_path,
            "n_ctx": 1024,
            "model_type": "phi2"
         }},
        {"desc": "Minimal params, last resort", 
         "module": "llama_cpp", 
         "class": "Llama",
         "params": {
            "model_path": model_path,
            "n_ctx": 512,
            "n_batch": 1,
         }}
    ]
    
    # Extend strategies with fallbacks
    strategies.extend(fallback_strategies)
    
    # Try each strategy
    for attempt, strategy in enumerate(strategies, 1):
        if attempt > max_attempts:
            logger.warning(f"Reached maximum attempts ({max_attempts}), stopping")
            break
            
        logger.info(f"Strategy {attempt}/{len(strategies)}: {strategy['desc']}")
        
        try:
            # Import the module dynamically
            module_name = strategy["module"]
            class_name = strategy["class"]
            
            # Try to import the module
            try:
                if module_name == "llama_cpp":
                    import llama_cpp
                    ModelClass = getattr(llama_cpp, class_name)
                elif module_name == "phi2_adapter":
                    import phi2_adapter
                    ModelClass = getattr(phi2_adapter, class_name)
                else:
                    logger.error(f"Unknown module: {module_name}")
                    continue
            except ImportError as ie:
                logger.error(f"Failed to import {module_name}: {ie}")
                continue
                
            # Load the model
            params = strategy["params"].copy()
            logger.info(f"Loading with params: {params}")
            
            # For adapters with different interface
            if strategy.get("is_adapter", False):
                model = ModelClass(**params)
                success = model.load_model()
                if not success:
                    logger.error("Adapter failed to load model")
                    continue
            else:
                model = ModelClass(**params)
            
            # Test the model with a simple prompt
            logger.info("Testing model with a simple prompt")
            
            # Different testing based on model type
            try:
                if strategy.get("is_adapter", False):
                    result = model("Hello", max_tokens=1)
                else:
                    result = model("Hello", max_tokens=1)
                    
                logger.info("Model test successful!")
                return model, True
            except Exception as test_error:
                logger.error(f"Model test failed: {test_error}")
                continue
                
        except Exception as e:
            logger.error(f"Strategy failed: {e}")
            
        # Delay before next attempt
        if attempt < len(strategies):
            logger.info(f"Waiting before next attempt...")
            time.sleep(1)
    
    # All strategies failed
    logger.error("All model loading strategies failed")
    return None, False

def _get_available_ram_gb() -> float:
    """Get approximate available RAM in GB"""
    try:
        if sys.platform == "linux" or sys.platform == "linux2":
            with open('/proc/meminfo', 'r') as mem:
                for line in mem:
                    if 'MemAvailable' in line:
                        return float(line.split()[1]) / 1024 / 1024
        
        # Default to conservative estimate
        return 4.0
    except:
        # Assume limited RAM if we can't determine it
        return 4.0

# Direct usage example
if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        model_path = "phi-2.Q4_K_M.gguf"
        
    model, success = load_model_for_docker(model_path)
    
    if success:
        print("Model loaded successfully!")
        
        # Test with a simple prompt
        prompt = "Hello, my name is"
        print(f"Testing with prompt: '{prompt}'")
        
        try:
            result = model(prompt, max_tokens=10)
            print(f"Result: {result}")
            
            # Extract the generated text
            if isinstance(result, dict) and "choices" in result:
                text = result["choices"][0]["text"]
                print(f"Generated text: {text}")
            else:
                print(f"Unexpected result format: {result}")
        except Exception as e:
            print(f"Error during generation: {e}")
    else:
        print("Failed to load model")
