"""
Real OCR processor using PaddleOCR
"""
import logging
import os

logger = logging.getLogger('ocr_processor')

class OCRProcessor:
    def __init__(self, use_gpu=False, lang='en', use_offline=True):
        """Initialize PaddleOCR processor"""
        self.use_gpu = use_gpu
        self.lang = lang
        self.use_offline = use_offline
        self.ocr = None
        
        logger.info("Initializing PaddleOCR processor")
        self._initialize_paddle_ocr()
    
    def _initialize_paddle_ocr(self):
        """Initialize PaddleOCR with error handling"""
        try:
            from paddleocr import PaddleOCR
            
            logger.info(f"Loading PaddleOCR (GPU: {self.use_gpu}, Lang: {self.lang})")
            
            # Initialize PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False
            )
            
            logger.info("✓ PaddleOCR initialized successfully")
            
        except ImportError:
            logger.error("PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr")
            self.ocr = None
        except Exception as e:
            logger.error(f"Error initializing PaddleOCR: {e}")
            self.ocr = None
    
    def process_document(self, file_path):
        """Process a document and extract text using PaddleOCR"""
        logger.info(f"Processing document with PaddleOCR: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not self.ocr:
            logger.warning("PaddleOCR not available, using fallback")
            return self._fallback_ocr(file_path)
        
        try:
            # For PDF files, convert to images first
            if file_path.lower().endswith('.pdf'):
                return self._process_pdf(file_path)
            
            # For image files, process directly
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                return self._process_image(file_path)
            
            else:
                logger.warning(f"Unsupported file format: {file_path}")
                return self._fallback_ocr(file_path)
                
        except Exception as e:
            logger.error(f"PaddleOCR processing error: {e}")
            return self._fallback_ocr(file_path)
    
    def _process_pdf(self, pdf_path):
        """Process PDF file by converting to images"""
        try:
            import fitz  # PyMuPDF
            
            logger.info("Converting PDF to images for OCR processing")
            
            # Open PDF
            doc = fitz.open(pdf_path)
            extracted_text = ""
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Convert page to image
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Save temporary image
                temp_img_path = f"temp_page_{page_num}.png"
                with open(temp_img_path, "wb") as f:
                    f.write(img_data)
                
                # Process with PaddleOCR
                page_text = self._process_image(temp_img_path)
                extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                # Clean up temp file
                os.remove(temp_img_path)
            
            doc.close()
            logger.info(f"✓ PDF processing complete: {len(extracted_text)} characters extracted")
            return extracted_text.strip()
            
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install PyMuPDF")
            return self._fallback_ocr(pdf_path)
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return self._fallback_ocr(pdf_path)
    
    def _process_image(self, image_path):
        """Process image file with PaddleOCR"""
        try:
            logger.info(f"Processing image: {image_path}")
            
            # Run OCR
            result = self.ocr.ocr(image_path, cls=True)
            
            # Extract text from results
            extracted_text = ""
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text = line[1][0]  # Get text content
                        confidence = line[1][1]  # Get confidence score
                        
                        # Only include text with reasonable confidence
                        if confidence > 0.5:
                            extracted_text += text + " "
            
            logger.info(f"✓ Image OCR complete: {len(extracted_text)} characters")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            return ""
    
    def _fallback_ocr(self, file_path):
        """Fallback OCR for when PaddleOCR fails"""
        logger.warning("Using fallback OCR (limited functionality)")
        
        # Try PyMuPDF for text extraction (not OCR)
        if file_path.lower().endswith('.pdf'):
            try:
                import fitz
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                
                if text.strip():
                    logger.info(f"✓ Fallback text extraction: {len(text)} characters")
                    return text
                    
            except ImportError:
                logger.error("PyMuPDF not available for fallback")
            except Exception as e:
                logger.error(f"Fallback extraction error: {e}")
        
        # Return minimal fallback
        logger.warning("Returning minimal fallback text")
        return f"Unable to extract text from {os.path.basename(file_path)}. Please check file format and OCR dependencies."