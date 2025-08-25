#!/usr/bin/env python3
"""
Script to pre-download PaddleOCR models for offline use
This should be run before building the Docker image or deploying to an offline environment.
"""

import os
import sys
import logging
import shutil
from paddleocr import PaddleOCR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('download_ocr_models')

def download_models():
    """Download OCR models for offline use"""
    try:
        logger.info("Downloading PaddleOCR models...")
        
        # Download models by initializing PaddleOCR
        # This will download the models to the default location
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        
        # Get the model directories from PaddleOCR
        from paddleocr.tools.infer.utility import get_model_config
        det_model_dir = get_model_config('det', None, None)[0]
        rec_model_dir = get_model_config('rec', None, 'en')[0]
        cls_model_dir = get_model_config('cls', None, None)[0]
        
        logger.info(f"Detection model path: {det_model_dir}")
        logger.info(f"Recognition model path: {rec_model_dir}")
        logger.info(f"Classification model path: {cls_model_dir}")
        
        # Create local directories
        target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paddleocr_models")
        os.makedirs(os.path.join(target_dir, "det"), exist_ok=True)
        os.makedirs(os.path.join(target_dir, "rec"), exist_ok=True)
        os.makedirs(os.path.join(target_dir, "cls"), exist_ok=True)
        
        # Copy the downloaded models to our local directory
        if os.path.exists(det_model_dir):
            logger.info("Copying detection model files...")
            for file in os.listdir(det_model_dir):
                shutil.copy(
                    os.path.join(det_model_dir, file),
                    os.path.join(target_dir, "det", file)
                )
        
        if os.path.exists(rec_model_dir):
            logger.info("Copying recognition model files...")
            for file in os.listdir(rec_model_dir):
                shutil.copy(
                    os.path.join(rec_model_dir, file),
                    os.path.join(target_dir, "rec", file)
                )
        
        if os.path.exists(cls_model_dir):
            logger.info("Copying classification model files...")
            for file in os.listdir(cls_model_dir):
                shutil.copy(
                    os.path.join(cls_model_dir, file),
                    os.path.join(target_dir, "cls", file)
                )
        
        logger.info("✓ OCR models downloaded and copied successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error downloading OCR models: {e}")
        return False

if __name__ == "__main__":
    success = download_models()
    sys.exit(0 if success else 1)
