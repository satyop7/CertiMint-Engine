"""
Pre-sandbox processing: OCR, web scraping, Groq keywords
"""
import json
import os
import logging
from ocr_processor import OCRProcessor
from groq_client import get_top_repetitive_words
from web_scraper import scrape_subject_content

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('pre_sandbox')

def run_pre_sandbox():
    """Run pre-sandbox processing"""
    
    # Step 1: Read info.json
    logger.info("Step 1: Reading info.json")
    with open('data/info.json', 'r') as f:
        info = json.load(f)
    
    subject = info['subject_name']
    file_name = info['File_name']
    assignment_id = info['assignmentID']
    
    # Step 2: OCR
    logger.info("Step 2: Performing OCR")
    ocr = OCRProcessor()
    ocr_text = ocr.process_document(f"data/{file_name}")
    
    # Save OCR text to result directory
    os.makedirs('result', exist_ok=True)
    ocr_file_path = f"result/ocr_text_{assignment_id}.txt"
    with open(ocr_file_path, 'w', encoding='utf-8') as f:
        f.write(ocr_text)
    logger.info(f"OCR text saved to {ocr_file_path}")
    
    # Step 3: Web scraping
    logger.info("Step 3: Web scraping subject content")
    scraped_content = scrape_subject_content(subject)
    
    # Step 4: Groq keywords
    logger.info("Step 4: Getting Groq keywords")
    groq_words = get_top_repetitive_words(subject, 8)
    
    # Save pre-processed data for sandbox
    pre_data = {
        "info": info,
        "ocr_text": ocr_text,
        "scraped_content": scraped_content,
        "groq_words": groq_words
    }
    
    with open('data/pre_processed.json', 'w') as f:
        json.dump(pre_data, f, indent=2)
    
    logger.info("Pre-sandbox processing complete")
    return pre_data

if __name__ == "__main__":
    run_pre_sandbox()