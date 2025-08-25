#!/usr/bin/env python3
"""
LLM loader module that provides a unified loading approach for Phi-2 or other models
across different environments (local, Docker, etc.)

This module uses multiple fallback strategies to ensure the model loads successfully,
regardless of the environment or llama-cpp-python version.
"""
import os
import logging
import time
import importlib.util
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('llm_loader')

def is_in_docker() -> bool:
    """Check if we're running inside a Docker container"""
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read()
    except:
        # Check for .dockerenv file
        return os.path.exists('/.dockerenv')

def get_llama_cpp_version() -> Optional[str]:
    """Get the installed version of llama-cpp-python"""
    try:
        llama_spec = importlib.util.find_spec("llama_cpp")
        if not llama_spec:
            return None
            
        try:
            import llama_cpp
            return getattr(llama_cpp, "__version__", "unknown")
        except:
            return "installed but version unknown"
    except:
        return None

def load_model(model_path: str, max_attempts: int = 3) -> Tuple[Any, bool, str]:
    """
    Load a LLM model with multiple fallback strategies
    
    Args:
        model_path: Path to the model file
        max_attempts: Maximum number of loading attempts
    
    Returns:
        Tuple of:
        - model: The loaded model or None if loading failed
        - success: True if model loaded successfully, False otherwise
        - error_message: Error message if loading failed, empty string otherwise
    """
    if not os.path.exists(model_path):
        return None, False, f"Model file not found: {model_path}"
    
    # Check model file permissions and fix if needed
    if not os.access(model_path, os.R_OK):
        try:
            logger.warning(f"Model file permissions issue, fixing...")
            os.chmod(model_path, 0o644)
            logger.info("Fixed model file permissions")
        except Exception as perm_err:
            logger.error(f"Failed to fix model permissions: {perm_err}")
    
    # Check if we're in Docker
    in_docker = is_in_docker()
    if in_docker:
        logger.info("Running in Docker environment")
    
    # Get llama-cpp-python version
    version = get_llama_cpp_version()
    logger.info(f"Using llama-cpp-python version: {version if version else 'unknown'}")
    
    # Define loading strategies from most compatible to most feature-rich
    # Start with strategies that are most likely to work in Docker
    strategies = [
        {
            "name": "Minimal params",
            "params": {
                "model_path": model_path,
                "verbose": True
            }
        },
        {
            "name": "Small context",
            "params": {
                "model_path": model_path,
                "n_ctx": 512,
                "n_batch": 8,
                "verbose": True
            }
        },
        {
            "name": "Standard params",
            "params": {
                "model_path": model_path,
                "n_ctx": 2048,
                "n_batch": 512,
                "verbose": True
            }
        },
        {
            "name": "GPU acceleration",
            "params": {
                "model_path": model_path,
                "n_ctx": 2048,
                "n_gpu_layers": -1,
                "n_batch": 512,
                "verbose": True
            }
        }
    ]
    
    # For non-Docker environment, add strategies with explicit model types
    if not in_docker:
        # These strategies are more likely to work outside Docker with newer versions
        model_type_strategies = [
            {
                "name": "With 'auto' type",
                "params": {
                    "model_path": model_path,
                    "model_type": "auto",
                    "n_ctx": 2048,
                    "n_batch": 512,
                    "verbose": True
                }
            },
            {
                "name": "With explicit phi2 type",
                "params": {
                    "model_path": model_path,
                    "model_type": "phi2",
                    "n_ctx": 2048,
                    "n_batch": 512,
                    "verbose": True
                }
            },
            {
                "name": "With llama type",
                "params": {
                    "model_path": model_path,
                    "model_type": "llama",
                    "n_ctx": 2048,
                    "n_batch": 512,
                    "verbose": True
                }
            }
        ]
        # Add these strategies at the beginning for non-Docker environments
        strategies = model_type_strategies + strategies
    
    # Try to import llama_cpp
    try:
        from llama_cpp import Llama
    except ImportError as e:
        return None, False, f"Failed to import llama_cpp: {e}"
    
    # Try multiple loading strategies
    last_error = None
    for attempt in range(1, max_attempts + 1):
        for i, strategy in enumerate(strategies):
            try:
                logger.info(f"Attempt {attempt}/{max_attempts} - Strategy: {strategy['name']}")
                
                # Try to load the model with this strategy
                model = Llama(**strategy['params'])
                
                # Test if model works with minimal prompt
                logger.info("Testing model with minimal prompt...")
                result = model("Hello", max_tokens=1)
                
                # If we get here, model loaded successfully
                logger.info(f"✓ Model successfully loaded using strategy: {strategy['name']}")
                return model, True, ""
                
            except Exception as e:
                # Skip strategies with model_type if we get architecture error
                if "unknown model architecture" in str(e) and "model_type" in strategy["params"]:
                    logger.warning(f"Strategy {strategy['name']} failed due to architecture error")
                    # Skip all remaining strategies with model_type
                    strategies = [s for s in strategies if "model_type" not in s["params"]]
                else:
                    logger.warning(f"Strategy {strategy['name']} failed: {e}")
                
                last_error = str(e)
        
        # If we've exhausted all strategies and still no success, wait before next attempt
        if attempt < max_attempts:
            logger.info(f"All strategies failed in attempt {attempt}, waiting before next attempt...")
            time.sleep(2)
    
    # If we get here, all attempts with all strategies failed
    error_msg = f"Failed to load model after {max_attempts} attempts with {len(strategies)} strategies."
    error_msg += f" Last error: {last_error}"
    logger.error(error_msg)
    
    return None, False, error_msg

# Simple test if run directly
if __name__ == "__main__":
    test_model_path = "phi-2.Q4_K_M.gguf"
    model, success, error = load_model(test_model_path)
    
    if success:
        print(f"Model loaded successfully!")
        # Test with a simple prompt
        result = model("Hello, I am", max_tokens=10)
        print(result["choices"][0]["text"])
    else:
        print(f"Failed to load model: {error}")
