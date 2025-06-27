#!/usr/bin/env python3
import os
import sys
import argparse
import logging
import gc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_minimal_model(model_path):
    """Load model with minimal settings to avoid memory issues"""
    try:
        # Force garbage collection first
        gc.collect()
        
        # Set minimal GPU settings
        os.environ["LLAMA_CPP_N_GPU_LAYERS"] = "16"  # Use fewer layers on GPU
        os.environ["LLAMA_CPP_N_CTX"] = "512"        # Smaller context window
        os.environ["LLAMA_CPP_N_BATCH"] = "64"       # Smaller batch size
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"     # Use first GPU
        os.environ["LLAMA_CUBLAS"] = "1"             # Enable CUDA
        
        # Import llama_cpp here to use the environment variables
        from llama_cpp import Llama
        
        # Load model with minimal settings
        logger.info(f"Loading model {model_path} with minimal settings...")
        model = Llama(
            model_path=model_path,
            n_ctx=512,           # Small context window
            n_batch=64,          # Small batch size
            n_gpu_layers=16,     # Use fewer layers on GPU
            verbose=False        # Reduce output
        )
        
        logger.info("Model loaded successfully")
        return model
    
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

def run_simple_inference(model, prompt):
    """Run simple inference to test model"""
    try:
        logger.info("Running test inference...")
        output = model(prompt, max_tokens=10)
        response = output["choices"][0]["text"]
        logger.info(f"Model response: {response}")
        return True
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load model with minimal settings")
    parser.add_argument("--model", required=True, help="Path to model file")
    args = parser.parse_args()
    
    model = load_minimal_model(args.model)
    if model:
        run_simple_inference(model, "Hello, how are you?")
    else:
        sys.exit(1)