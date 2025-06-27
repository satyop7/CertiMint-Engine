#!/usr/bin/env python3
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_gpu_environment():
    """Configure environment for GPU usage"""
    # Set CUDA environment variables
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["LLAMA_CPP_N_GPU_LAYERS"] = "32"  # Use all layers on GPU
    os.environ["LLAMA_CUBLAS"] = "1"             # Enable cuBLAS
    
    # Limit CPU memory usage
    os.environ["LLAMA_CPP_N_THREADS"] = "4"      # Limit CPU threads
    os.environ["LLAMA_CPP_N_BATCH"] = "128"      # Smaller batch size
    
    # Set memory limits
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
    
    logger.info("GPU environment configured")

def check_gpu():
    """Check if NVIDIA GPU is available"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            gpu_info = result.stdout.split('\n')[8]  # GPU info line
            vram_info = result.stdout.split('\n')[9]  # Memory info line
            logger.info(f"GPU detected: {gpu_info.strip()}")
            logger.info(f"VRAM: {vram_info.strip()}")
            return True
        return False
    except:
        return False

def run_workflow(args):
    """Run the workflow with GPU optimizations"""
    # Force garbage collection
    import gc
    gc.collect()
    
    # Set environment variables
    os.environ["PHI2_COMPAT_MODE"] = "1"
    os.environ["SANDBOX_MODE"] = "true"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    
    # Run the main script with the same arguments
    cmd = [sys.executable, "main.py"] + args
    logger.info(f"Running command: {' '.join(cmd)}")
    
    return subprocess.run(cmd)

if __name__ == "__main__":
    logger.info("Starting GPU-optimized workflow")
    
    # Check for GPU
    if not check_gpu():
        logger.warning("No GPU detected! Using CPU only mode.")
    else:
        setup_gpu_environment()
    
    # Run the workflow with the same arguments
    sys.exit(run_workflow(sys.argv[1:]).returncode)