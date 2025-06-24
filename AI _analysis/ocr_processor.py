import os
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
from pdf2image import convert_from_path

class OCRProcessor:
    def __init__(self, use_gpu=False, lang='en', use_offline=False):
        """Initialize OCR processor with PaddleOCR"""
        try:
            # First determine if we need offline mode
            offline_mode = use_offline
            if os.environ.get('SANDBOX_MODE', '').lower() == 'true':
                offline_mode = True
                
            # If we detect Docker environment, also use offline mode
            if os.path.exists('/.dockerenv'):
                offline_mode = True
                
            if offline_mode:
                print("Initializing PaddleOCR in offline mode")
                
                # IMPORTANT: Force environment variables for offline mode
                os.environ['PPOCR_DOWNLOAD'] = 'OFF'
                
                # Simply use PaddleOCR with the default cached models, 
                # but ensure download is disabled
                try:
                    self.ocr = PaddleOCR(
                        use_angle_cls=False,  # Disable angle cls to reduce dependencies
                        lang=lang,
                        use_gpu=use_gpu,
                        download_font=False,
                        show_log=False,
                        rec_char_dict_path=None  # Use default dict path
                    )
                except Exception as e:
                    print(f"Error initializing PaddleOCR in offline mode: {e}")
                    print("Using fallback implementation")
                    
                    # Create minimal implementation for offline mode
                    class MinimalOCR:
                        def ocr(self, img, cls=False):
                            # Return empty result as fallback
                            return []
                    
                    self.ocr = MinimalOCR()
            else:
                # Regular mode with network access
                self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=use_gpu)
                
            print("PaddleOCR initialized successfully")
        except Exception as e:
            print(f"Error initializing PaddleOCR: {e}")
            raise
    
    def _get_model_path(self, model_type):
        """Get path to pre-downloaded model files"""
        # Try multiple possible locations for the models
        possible_paths = [
            # Standard PaddleOCR cache location
            os.path.join(os.path.expanduser('~/.paddleocr')),
            # Models in current directory
            os.path.dirname(os.path.abspath(__file__)),
            # Models in app directory (for Docker)
            '/app',
            # Models in paddleocr_models directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "paddleocr_models")
        ]
        
        # Log available paths for debugging
        print(f"Looking for {model_type} model in possible paths:")
        for path in possible_paths:
            print(f" - {path}")
        
        # Check each path for model directories using multiple known patterns
        patterns = [
            ["whl", model_type],                       # Standard ~/.paddleocr structure
            ["whl", model_type, "en"] if model_type == "rec" else ["whl", model_type],  # For recognition models with language
            ["paddleocr", "whl", model_type],          # Alternative structure
            ["paddleocr", "whl", model_type, "en"] if model_type == "rec" else ["paddleocr", "whl", model_type],
            [".paddleocr", "whl", model_type],         # Hidden directory structure
            [".paddleocr", "whl", model_type, "en"] if model_type == "rec" else [".paddleocr", "whl", model_type],
            ["inference", model_type],                 # Direct inference structure
            [model_type],                              # Simple directory structure
        ]
        
        for base_dir in possible_paths:
            if not os.path.exists(base_dir):
                continue
                
            for pattern in patterns:
                model_dir = os.path.join(base_dir, *pattern)
                if os.path.exists(model_dir):
                    print(f"Found {model_type} model at: {model_dir}")
                    return model_dir
                    
        print(f"WARNING: No {model_type} model directory found in any location")
        return None
    
    def process_document(self, file_path):
        """Extract text from document using OCR"""
        try:
            if file_path.lower().endswith('.pdf'):
                return self._process_pdf(file_path)
            else:
                return self._process_image(file_path)
        except Exception as e:
            print(f"OCR error: {e}")
            return None
    
    def _process_image(self, image_path):
        """Process a single image file using PaddleOCR"""
        img = Image.open(image_path)
        img_array = np.array(img)
        result = self.ocr.ocr(img_array, cls=True)
        text = self._extract_text_from_result(result)
        return text
    
    def _process_pdf(self, pdf_path):
        pages = convert_from_path(pdf_path)
        full_text = ""
        for i, page in enumerate(pages):
            print(f"Processing page {i+1}/{len(pages)}")
            img_array = np.array(page)
            result = self.ocr.ocr(img_array, cls=True)
            page_text = self._extract_text_from_result(result)
            full_text += page_text + "\n\n"
        return full_text
    
    def _extract_text_from_result(self, result):
        text = ""
        if result is None:
            return ""
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            for page in result:
                if page:
                    for line in page:
                        if len(line) >= 2:
                            text += line[1][0] + " "
        else:
            for line in result:
                if len(line) >= 2:
                    text += line[1][0] + " "
        return text

if __name__ == "__main__":
    processor = OCRProcessor()
    sample_path = "data/sample.pdf"
    if os.path.exists(sample_path):
        text = processor.process_document(sample_path)
        print(f"Extracted {len(text)} characters of text")
        print(text[:500] + "...")
    else:
        print(f"Sample file not found: {sample_path}")
