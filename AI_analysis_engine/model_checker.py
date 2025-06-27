#!/usr/bin/env python3
"""
Model integrity checker module for LLM sandbox

This module provides utilities to verify the integrity of model files,
check their validity, and find fallback models if needed.
"""
import os
import sys
import glob
import hashlib
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger('model_checker')

class ModelChecker:
    """Model integrity verification class"""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the model checker with an optional model path"""
        self.model_path = model_path
        
    def verify_model(self, model_path: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify if a model file exists and is valid
        
        Args:
            model_path: Path to model file to check, uses self.model_path if None
            
        Returns:
            Tuple of (is_valid, details_dict)
        """
        path = model_path or self.model_path
        
        if not path:
            logger.error("No model path provided")
            return False, {"error": "No model path provided"}
        
        # Check file existence
        if not os.path.exists(path):
            logger.error(f"Model file not found: {path}")
            return False, {"error": "Model file not found", "path": path}
            
        # Check if it's a file
        if not os.path.isfile(path):
            logger.error(f"Path is not a file: {path}")
            return False, {"error": "Path is not a file", "path": path}
            
        # Check file size
        size_bytes = os.path.getsize(path)
        size_mb = size_bytes / (1024 * 1024)
        
        # Model files should be at least 100MB for most LLMs
        if size_mb < 100:
            logger.warning(f"Model file seems too small: {size_mb:.2f} MB")
            return False, {
                "error": "Model file too small",
                "path": path,
                "size_mb": size_mb
            }
            
        # Check file permissions
        can_read = os.access(path, os.R_OK)
        if not can_read:
            logger.warning(f"Cannot read model file: {path}")
            return False, {"error": "No read permission", "path": path}
            
        # Calculate file signature (hash of first 1MB)
        try:
            md5 = hashlib.md5()
            with open(path, 'rb') as f:
                md5.update(f.read(1024 * 1024))
            signature = md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file signature: {e}")
            signature = "error"
            
        # Perform basic file header check for GGUF format
        header_valid = self._check_gguf_header(path)
            
        details = {
            "path": path,
            "size_mb": size_mb,
            "can_read": can_read,
            "signature": signature,
            "header_valid": header_valid
        }
        
        valid = can_read and size_mb >= 100 and header_valid
        
        if valid:
            logger.info(f"Model file valid: {path} ({size_mb:.2f} MB)")
        else:
            logger.warning(f"Model file may be invalid: {path}")
            
        return valid, details
    
    def _check_gguf_header(self, path: str) -> bool:
        """Check if the file has a valid GGUF header"""
        try:
            with open(path, 'rb') as f:
                header = f.read(8)
                # GGUF files start with "GGUF" in ASCII followed by version number
                if header[:4] == b'GGUF' or header[:4] == b'GGML' or header[:4] == b'ggjt':
                    return True
                # For other formats, just check if it's a binary file (not text)
                return not self._is_text_file(path)
        except:
            return False
    
    def _is_text_file(self, path: str) -> bool:
        """Check if a file is a text file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read as text
                return True
        except:
            return False  # Reading as text failed, likely binary
    
    def find_alternative_models(self) -> List[Dict[str, Any]]:
        """
        Find alternative model files that could be used
        
        Returns:
            List of dicts with model info
        """
        search_dirs = [
            ".",  # Current directory
            "./models",  # Models subdirectory
            os.path.expanduser("~/.cache/huggingface/"),  # HF cache
        ]
        
        found_models = []
        
        for directory in search_dirs:
            if not os.path.exists(directory):
                continue
                
            try:
                # Look for .gguf files (standard format for llama.cpp)
                for path in glob.glob(os.path.join(directory, "**", "*.gguf"), recursive=True):
                    if os.path.isfile(path):
                        size_mb = os.path.getsize(path) / (1024 * 1024)
                        
                        if size_mb >= 100:  # Only consider reasonably sized models
                            found_models.append({
                                "path": path,
                                "size_mb": size_mb
                            })
                            
                # Also look for other formats
                for ext in [".bin", ".pt", ".pth", ".safetensors"]:
                    for path in glob.glob(os.path.join(directory, "**", f"*{ext}"), recursive=True):
                        if os.path.isfile(path):
                            size_mb = os.path.getsize(path) / (1024 * 1024)
                            
                            # Only include large files that are likely to be models
                            if size_mb >= 500:
                                found_models.append({
                                    "path": path,
                                    "size_mb": size_mb
                                })
            except Exception as e:
                logger.error(f"Error searching for models in {directory}: {e}")
        
        # Sort by size (largest first) as a heuristic for model quality
        found_models.sort(key=lambda x: x["size_mb"], reverse=True)
        
        return found_models
    
    def get_best_model_path(self) -> Optional[str]:
        """
        Get the best available model path
        
        Returns:
            Path to the best model, or None if no valid model found
        """
        # First check if the provided model is valid
        if self.model_path:
            is_valid, _ = self.verify_model(self.model_path)
            if is_valid:
                return self.model_path
        
        # Look for alternatives
        alternatives = self.find_alternative_models()
        
        if not alternatives:
            return None
            
        # Validate the best alternative
        is_valid, _ = self.verify_model(alternatives[0]["path"])
        if is_valid:
            return alternatives[0]["path"]
            
        return None

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    model_path = sys.argv[1] if len(sys.argv) > 1 else "phi-2.Q4_K_M.gguf"
    
    checker = ModelChecker(model_path)
    is_valid, details = checker.verify_model()
    
    print(f"Model valid: {is_valid}")
    print(f"Details: {details}")
    
    if not is_valid:
        print("\nSearching for alternative models...")
        alternatives = checker.find_alternative_models()
        
        if alternatives:
            print(f"Found {len(alternatives)} alternative models:")
            for i, model in enumerate(alternatives[:5]):  # Show top 5
                print(f"{i+1}. {model['path']} ({model['size_mb']:.2f} MB)")
        else:
            print("No alternative models found.")
