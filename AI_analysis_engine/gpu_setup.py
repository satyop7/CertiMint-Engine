#!/usr/bin/env python3
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def check_gpu_availability():
    """Check if NVIDIA GPU is available"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("NVIDIA GPU detected:")
            logger.info(result.stdout.split('\n')[8])  # GPU info line
            return True
        else:
            logger.warning("nvidia-smi failed, GPU may not be available")
            return False
    except FileNotFoundError:
        logger.warning("nvidia-smi not found, GPU drivers may not be installed")
        return False

def setup_cuda_environment():
    """Setup CUDA environment variables"""
    cuda_paths = [
        "/usr/local/cuda/bin",
        "/usr/local/cuda-11/bin", 
        "/usr/local/cuda-12/bin"
    ]
    
    for path in cuda_paths:
        if os.path.exists(path):
            os.environ["PATH"] = f"{path}:{os.environ.get('PATH', '')}"
            logger.info(f"Added CUDA path: {path}")
            break
    
    # Set GPU memory growth
    os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    
def install_gpu_dependencies():
    """Install GPU-accelerated dependencies"""
    try:
        # Check if llama-cpp-python with CUDA is installed
        import llama_cpp
        logger.info("llama-cpp-python found")
        
        # Try to create a model with GPU support
        try:
            # This will fail if no CUDA support
            test_model = llama_cpp.Llama(model_path="", n_gpu_layers=1, verbose=False)
            logger.info("CUDA support detected in llama-cpp-python")
        except:
            logger.warning("llama-cpp-python may not have CUDA support")
            logger.info("Consider reinstalling with: pip install llama-cpp-python[cuda]")
            
    except ImportError:
        logger.warning("llama-cpp-python not found")
        logger.info("Install with: pip install llama-cpp-python[cuda]")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== GPU Setup Check ===")
    gpu_available = check_gpu_availability()
    
    if gpu_available:
        setup_cuda_environment()
        install_gpu_dependencies()
        print("✓ GPU setup completed")
    else:
        print("⚠ GPU not available, using CPU mode")