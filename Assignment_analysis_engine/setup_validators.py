"""
Validator Setup Module

This script ensures all validator components are available and correctly configured.
"""

import os
import sys
import logging
import importlib

logger = logging.getLogger(__name__)

def check_and_install_module(module_name):
    """Check if a module is installed and attempt to install it if not"""
    try:
        importlib.import_module(module_name)
        logger.info(f"✓ Module {module_name} is available")
        return True
    except ImportError:
        logger.warning(f"Module {module_name} not found, attempting to install...")
        
        try:
            import subprocess
            result = subprocess.run([sys.executable, "-m", "pip", "install", module_name], 
                                   check=True, capture_output=True)
            logger.info(f"Successfully installed {module_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to install {module_name}: {e}")
            return False

def setup_validators():
    """Setup all validation components"""
    # Check for enhanced plagiarism detector
    try:
        import enhanced_plagiarism_detector
        logger.info("✓ Enhanced plagiarism detector is available")
    except ImportError:
        logger.error("Enhanced plagiarism detector module not found")
        logger.error("The system will fall back to basic plagiarism detection")
    
    # Check for AI pattern detector
    try:
        import ai_pattern_detector
        logger.info("✓ AI pattern detector is available")
    except ImportError:
        logger.error("AI pattern detector module not found")
        logger.error("The system will fall back to basic AI detection")
    
    # Check for subject validation
    try:
        import subject_validation
        logger.info("✓ Subject validation is available")
    except ImportError:
        logger.error("Subject validation module not found")
        logger.error("The system will fall back to basic relevance detection")
    
    # Essential libraries
    required_modules = [
        "scikit-learn", 
        "numpy", 
        "pymongo"
    ]
    
    all_available = True
    for module in required_modules:
        if not check_and_install_module(module):
            all_available = False
    
    return all_available

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    successful = setup_validators()
    if successful:
        logger.info("All validator components are available and configured")
        sys.exit(0)
    else:
        logger.error("Some validator components could not be setup correctly")
        sys.exit(1)
