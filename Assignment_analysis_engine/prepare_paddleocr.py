#!/usr/bin/env python3
"""
Script to prepare PaddleOCR models for offline use
This should be run before executing the network-isolated workflow
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('prepare_paddleocr')

def download_models():
    """Download and prepare PaddleOCR models for offline use"""
    try:
        logger.info("Downloading PaddleOCR models...")
        
        # Import PaddleOCR here to download models
        from paddleocr import PaddleOCR
        
        # Initialize PaddleOCR to trigger downloads
        logger.info("Initializing PaddleOCR to trigger downloads...")
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        logger.info("PaddleOCR initialized successfully")
        
        # Now find where models were downloaded
        paddle_home = os.environ.get('PADDLE_HOME', os.path.expanduser('~/.paddleocr'))
        logger.info(f"Default PaddleOCR home: {paddle_home}")
        
        # Create local copy for use in sandbox
        app_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(app_dir, "paddleocr_models")
        os.makedirs(target_dir, exist_ok=True)
        
        # Check where models might be stored
        possible_paths = [
            os.path.expanduser('~/.paddleocr'),
            os.path.join(app_dir, ".paddleocr"),
            paddle_home
        ]
        
        models_found = False
        
        for source_dir in possible_paths:
            if not os.path.exists(source_dir):
                logger.info(f"Directory not found: {source_dir}")
                continue
                
            logger.info(f"Checking for models in: {source_dir}")
            
            # Check for model directories
            whl_dir = os.path.join(source_dir, "whl")
            if not os.path.exists(whl_dir):
                logger.info(f"No 'whl' directory in {source_dir}")
                continue
                
            # Check for model types
            for model_type in ["det", "rec", "cls"]:
                model_dir = os.path.join(whl_dir, model_type)
                if os.path.exists(model_dir):
                    # For 'rec', we need the language-specific directory
                    if model_type == "rec":
                        lang_dirs = [d for d in os.listdir(model_dir) if os.path.isdir(os.path.join(model_dir, d))]
                        for lang in lang_dirs:
                            lang_dir = os.path.join(model_dir, lang)
                            target_lang_dir = os.path.join(target_dir, "whl", model_type, lang)
                            os.makedirs(target_lang_dir, exist_ok=True)
                            
                            logger.info(f"Copying {model_type}/{lang} models to {target_lang_dir}")
                            for item in os.listdir(lang_dir):
                                s = os.path.join(lang_dir, item)
                                d = os.path.join(target_lang_dir, item)
                                if os.path.isfile(s):
                                    shutil.copy2(s, d)
                                    models_found = True
                    else:
                        target_model_dir = os.path.join(target_dir, "whl", model_type)
                        os.makedirs(target_model_dir, exist_ok=True)
                        
                        logger.info(f"Copying {model_type} models to {target_model_dir}")
                        for item in os.listdir(model_dir):
                            s = os.path.join(model_dir, item)
                            d = os.path.join(target_model_dir, item)
                            if os.path.isfile(s):
                                shutil.copy2(s, d)
                                models_found = True
        
        if models_found:
            logger.info("✓ Models copied successfully to paddleocr_models directory")
            # Create a marker file to indicate models are prepared
            with open(os.path.join(target_dir, "MODELS_READY"), "w") as f:
                f.write("PaddleOCR models successfully prepared for offline use\n")
            return True
        else:
            logger.error("No models were found to copy")
            return False
            
    except ImportError:
        logger.error("PaddleOCR not installed. Please install with: pip install paddleocr")
        return False
    except Exception as e:
        logger.error(f"Error preparing models: {e}")
        return False

if __name__ == "__main__":
    success = download_models()
    sys.exit(0 if success else 1)
