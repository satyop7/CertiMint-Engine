#!/usr/bin/env python3
"""
Adapter module for Phi-2 model to work with llama.cpp

This module provides a compatibility layer to use Phi-2 models with older
versions of llama.cpp that don't natively support the phi2 architecture.
"""
import os
import sys
import logging
import importlib.util
import subprocess
import time
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('phi2_adapter')

class Phi2Adapter:
    """Adapter class to provide compatibility between Phi-2 and llama.cpp"""
    
    def __init__(self, model_path: str):
        """Initialize the adapter with the model path"""
        self.model_path = model_path
        self.model = None
        self.model_loaded = False
        
        # Check if we're in a Docker container
        self.in_docker = self._check_if_in_docker()
        if self.in_docker:
            logger.info("Running inside Docker container")
    
    def _check_if_in_docker(self) -> bool:
        """Check if we're running inside a Docker container"""
        try:
            with open('/proc/1/cgroup', 'rt') as f:
                return 'docker' in f.read()
        except:
            # Check for .dockerenv file
            return os.path.exists('/.dockerenv')
    
    def load_model(self, **kwargs) -> bool:
        """
        Load the Phi-2 model with fallback strategies
        
        Args:
            **kwargs: Additional arguments to pass to Llama constructor
            
        Returns:
            bool: True if model was successfully loaded, False otherwise
        """
        if not os.path.exists(self.model_path):
            logger.error(f"Model file not found: {self.model_path}")
            return False
            
        try:
            # Check llama-cpp-python version first
            llama_version = self._get_llama_cpp_version()
            logger.info(f"llama-cpp-python version: {llama_version if llama_version else 'unknown'}")
            
            from llama_cpp import Llama
            
            # Get model file size
            file_size_mb = os.path.getsize(self.model_path) / (1024 * 1024)
            logger.info(f"Model size: {file_size_mb:.2f} MB")
            
            if file_size_mb < 500:  # Suspicious if less than 500MB
                logger.warning(f"Model file is unusually small: {file_size_mb:.2f} MB")
            
            # Try different model loading strategies
            strategies = [
                {"desc": "Default parameters", "params": {}},
                {"desc": "With phi2 model type", "params": {"model_type": "phi2"}},
                {"desc": "With phi model type", "params": {"model_type": "phi"}},
                {"desc": "With llama model type", "params": {"model_type": "llama"}},
                {"desc": "With gptj model type", "params": {"model_type": "gptj"}},
                {"desc": "With minimal context", "params": {"n_ctx": 512, "n_batch": 8, "verbose": True}}
            ]
            
            # For Docker, prioritize strategies that are more likely to work
            if self.in_docker:
                # In Docker, the model_type parameter might cause issues
                strategies = [
                    {"desc": "Docker-compatible minimal params", "params": {"n_ctx": 512, "n_batch": 1}},
                    {"desc": "Docker-compatible with llama type", "params": {"n_ctx": 512, "n_batch": 1, "model_type": "llama"}},
                    {"desc": "Docker minimal", "params": {}},
                ] + strategies
            
            last_error = None
            for strategy in strategies:
                try:
                    logger.info(f"Trying to load model with {strategy['desc']}")
                    
                    # Create base parameters dictionary
                    params = {
                        "model_path": self.model_path,
                        "n_ctx": 2048,
                        "n_gpu_layers": -1,  # Auto-detect
                        "n_batch": 512,
                        "verbose": kwargs.get("verbose", False)
                    }
                    
                    # Add strategy-specific parameters
                    params.update(strategy["params"])
                    
                    # Add any additional parameters passed to this function
                    params.update({k:v for k,v in kwargs.items() if k not in strategy["params"]})
                    
                    # Log actual parameters being used
                    param_log = {k:v for k,v in params.items() if k != "model_path"}
                    logger.info(f"Loading with parameters: {param_log}")
                    
                    # Try loading the model
                    start_time = time.time()
                    self.model = Llama(**params)
                    load_time = time.time() - start_time
                    logger.info(f"Model loaded in {load_time:.2f} seconds")
                    
                    # Test with a minimal prompt
                    logger.info("Testing model with a minimal prompt")
                    output = self.model("Hello", max_tokens=1)
                    logger.info(f"Model test successful")
                    
                    self.model_loaded = True
                    return True
                except Exception as e:
                    last_error = e
                    logger.error(f"Failed with {strategy['desc']}: {e}")
                    
                    # If in Docker and the error mentions "unknown model architecture",
                    # we need to log more detailed information
                    if self.in_docker and "unknown model architecture" in str(e):
                        logger.error("This is a common error with Phi-2 models in Docker containers")
                        logger.error("The Docker container may need an updated version of llama-cpp-python")
                        
                        # Check if direct llama.cpp binary is available
                        self._check_direct_llama_cpp()
                        
                    # Extra delay between strategies in Docker
                    if self.in_docker:
                        logger.info("Waiting before next attempt...")
                        time.sleep(1)
            
            if last_error:
                logger.error(f"All loading strategies failed. Last error: {last_error}")
            else:
                logger.error("All loading strategies failed without specific error")
            
            return False
        except ImportError as e:
            logger.error(f"Import error: {e}")
            logger.error("llama-cpp-python package is not installed or incompatible")
            self._suggest_fixes()
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def _get_llama_cpp_version(self) -> Optional[str]:
        """Get the version of llama-cpp-python"""
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
    
    def _check_direct_llama_cpp(self) -> None:
        """Check if direct llama.cpp binary is available"""
        try:
            # Check if llama.cpp/build/bin/main exists
            direct_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      "llama.cpp", "build", "bin", "main")
            if os.path.exists(direct_path):
                logger.info(f"Found direct llama.cpp binary: {direct_path}")
                logger.info(f"Consider using this binary directly if Python binding fails")
        except:
            pass
    
    def _suggest_fixes(self) -> None:
        """Suggest fixes for common issues"""
        logger.info("\nPossible solutions:")
        logger.info("1. Install llama-cpp-python with Phi-2 support:")
        logger.info("   pip install --upgrade llama-cpp-python>=0.1.79")
        logger.info("2. Or install a fork with guaranteed Phi-2 support:")
        logger.info("   pip uninstall -y llama-cpp-python")
        logger.info("   pip install llama-cpp-python-phi")
        logger.info("3. For Docker environments, rebuild the container with an updated version")
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text from the model
        
        Args:
            prompt: The input prompt
            **kwargs: Additional arguments to pass to llama_cpp.generate
            
        Returns:
            Dict with generation results
        """
        if not self.model_loaded or not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Default parameters for generation
        params = {
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.95,
            "repeat_penalty": 1.1,
            "top_k": 40,
            "echo": False
        }
        
        # Override with any provided parameters
        params.update(kwargs)
        
        # Generate with the model
        try:
            logger.info(f"Generating with prompt: {prompt[:30]}...")
            result = self.model(prompt, **params)
            
            # Check if the result contains expected fields
            if isinstance(result, dict) and "choices" in result:
                text = result["choices"][0]["text"]
                logger.info(f"Generated {len(text)} chars")
                return result
            else:
                logger.error(f"Unexpected result format: {result}")
                return {"error": "Invalid response format", "raw_result": result}
                
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return {"error": str(e)}
    
    def __call__(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Shorthand for generate method"""
        return self.generate(prompt, **kwargs)


# Example usage
if __name__ == "__main__":
    model_path = "phi-2.Q4_K_M.gguf"
    
    adapter = Phi2Adapter(model_path)
    if adapter.load_model(verbose=True):
        prompt = """
You are Phi-2, a helpful and harmless language model. Please answer the following question:

What are the main applications of large language models in academic research?
"""
        result = adapter.generate(prompt, max_tokens=100)
        if "choices" in result:
            text = result["choices"][0]["text"]
            print(f"--- Generated Output ---\n{text}\n-----------------------")
        else:
            print(f"Error: {result}")
    else:
        print("Failed to load model")
