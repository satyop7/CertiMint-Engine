import os
import json
import argparse
import datetime
import logging
import socket
import re
from ocr_processor import OCRProcessor
from llm_sandbox import SandboxedLLM
from llm_loader import load_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

"""
Assignment Validation Process:
- Extracts text from PDF/image files using OCR
- Validates content against plagiarism thresholds:
  1. LLM-based plagiarism detection: Fail if similarity > 60%
  2. Semantic similarity detection: Fail if similarity > 75%
  3. Emoji detection: Fail if any emojis found (indicates AI-generated content)
- Checks content relevance to the specified subject
"""

class AssignmentValidator:
    def __init__(self, model_path, references_path="data/references.json"):
        # Ensure we're in sandbox mode
        os.environ["LANGCHAIN_TRACING"] = "false"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"
        
        # Verify network isolation if in sandbox mode
        if os.environ.get("SANDBOX_MODE") == "true":
            self._verify_network_isolation()
            
        logger.info("="*50)
        logger.info("Initializing Assignment Validator in sandbox mode")
        logger.info("="*50)
        logger.info(f"Using references from: {references_path}")
        logger.info(f"Using LLM model from: {model_path}")
        
        # Initialize OCR processor
        logger.info("Initializing OCR processor...")
        try:
            # Check if we're running in a sandbox/offline environment
            sandbox_mode = os.environ.get("SANDBOX_MODE", "false").lower() == "true"
            
            # Use offline mode in sandbox environments
            self.ocr = OCRProcessor(use_gpu=False, lang='en', use_offline=sandbox_mode)
            logger.info("✓ OCR processor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OCR processor: {e}")
            logger.warning("Using simplified OCR functionality")
            self.ocr = self._create_mock_ocr()
        
        # Initialize LLM sandbox
        logger.info("Initializing LLM sandbox...")
        
        # Check if we're in PHI2_COMPAT_MODE (for Docker)
        phi2_compat_mode = os.environ.get("PHI2_COMPAT_MODE") == "1"
        if phi2_compat_mode:
            logger.info("Running in PHI2_COMPAT_MODE - using minimal loader for Docker compatibility")
            
        try:
            if phi2_compat_mode:
                # Use Docker-compatible loader
                from docker_llm_loader import load_model_for_docker
                logger.info("Using Docker-compatible loader without architecture specification")
                model, success = load_model_for_docker(model_path)
                if not success or model is None:
                    raise RuntimeError("Failed to load model with Docker-compatible approach")
                
                # Create a wrapper for the model
                class DockerCompatLLM:
                    def __init__(self, model):
                        self.model = model
                        self.model_loaded = True
                    
                    # Enhanced plagiarism checking and content validation methods
                    def check_plagiarism(self, text, references):
                        logger.info("Using Docker-compatible enhanced plagiarism check")
                        try:
                            # Try to use the enhanced plagiarism detector module
                            import enhanced_plagiarism_detector
                            import ai_pattern_detector
                            
                            # Run the enhanced plagiarism detection
                            logger.info("Running enhanced plagiarism detection...")
                            results = enhanced_plagiarism_detector.detect_enhanced_plagiarism(text, references)
                            
                            logger.info(f"Enhanced plagiarism score: {results.get('plagiarism_percentage', 0):.1f}%")
                            logger.info(f"AI confidence: {results.get('ai_confidence', 0):.1f}%")
                            
                            # Check if subject mismatch is detected (strong indicator of AI generation)
                            subject_mismatch = results.get("subject_mismatch", False)
                            if subject_mismatch:
                                logger.warning("Subject-content mismatch detected - strong indicator of AI-generated content")
                                
                            # Add LLM similarity from AI confidence for compatibility
                            results["llm_similarity"] = results.get("ai_confidence", 0)
                            
                            return results
                            
                        except Exception as e:
                            logger.error(f"Error using enhanced plagiarism detector: {e}")
                            logger.warning("Falling back to basic plagiarism detection")
                            # Try a simpler approach with less dependencies
                            try:
                                # Analyze text for common AI indicators
                                emoji_pattern = re.compile(
                                    "["
                                    "\U0001F600-\U0001F64F"  # emoticons
                                    "\U0001F300-\U0001F5FF"  # symbols & pictographs  
                                    "\U0001F680-\U0001F6FF"  # transport & map symbols
                                    "]+", flags=re.UNICODE)
                                
                                emojis = emoji_pattern.findall(text)
                                emoji_detected = len(emojis) > 0
                                
                                # Check simple AI patterns
                                ai_patterns = [
                                    "as an ai", "as an assistant", "as a language model",
                                    "i don't have personal", "i don't have the ability",
                                    "i don't have access", "my training data",
                                    "my training cut", "my knowledge cut"
                                ]
                                
                                ai_pattern_matches = [p for p in ai_patterns if p in text.lower()]
                                ai_detected = len(ai_pattern_matches) > 0
                                
                                # Calculate plagiarism based on these signals and n-grams
                                plagiarism_score = 20  # Base score
                                
                                if emoji_detected:
                                    plagiarism_score += 30
                                    logger.warning(f"Emojis detected in text: {emojis[:5]}")
                                
                                if ai_detected:
                                    plagiarism_score += 40
                                    logger.warning(f"AI patterns detected: {ai_pattern_matches}")
                                
                                # Check subject mismatch
                                if "info.json" in os.listdir("data"):
                                    try:
                                        with open("data/info.json") as f:
                                            info = json.load(f)
                                            file_subject = info.get("subject_name", "").lower()
                                            
                                            if file_subject and file_subject not in text.lower():
                                                plagiarism_score += 20
                                                logger.warning(f"Subject mismatch: {file_subject} not found in content")
                                    except:
                                        pass
                                
                                return {
                                    "status": "checked", 
                                    "plagiarism_percentage": min(100, plagiarism_score), 
                                    "similar_sources": [], 
                                    "llm_similarity": min(100, plagiarism_score),
                                    "ai_patterns": ai_pattern_matches,
                                    "emoji_detected": emoji_detected
                                }
                            except Exception as e:
                                # If the simplified approach also fails, return a basic result
                                logger.error(f"Error in simplified plagiarism check: {e}")
                                return {"status": "checked", "plagiarism_percentage": 30.0, "similar_sources": [], "llm_similarity": 30.0}
                    

                    def validate_content(self, text, subject, references):
                        logger.info(f"Using Docker-compatible content validation for subject: {subject}")
                        
                        try:
                            # Try to use direct subject validation module
                            import subject_validation
                            is_valid, confidence, reason = subject_validation.validate_subject_keywords(text, subject)
                            
                            # Check if there are no defined keyword rules for this subject
                            if "No defined keyword rules" in reason:
                                logger.info(f"No defined keyword rules for subject '{subject}', proceeding to LLM validation")
                                # Use enhanced relevance checker for better validation
                                from enhanced_relevance_checker import enhanced_relevance_check
                                return enhanced_relevance_check(text, subject, self)
                            
                            # If subject validation is available, use its results
                            status = "PASSED" if is_valid else "FAILED"
                            logger.info(f"Direct subject validation result: {status} with {confidence}% confidence")
                            
                            if not is_valid:
                                logger.warning(f"Subject mismatch reason: {reason}")
                            
                            return {
                                "status": status,
                                "relevance_score": confidence,
                                "comments": reason
                            }
                            
                        except Exception as e:
                            # Fall back to simple checks if module not available
                            logger.warning(f"Subject validation module error: {e}, falling back to simple checks")
                            
                            # Improved content-subject matching
                            subject_lower = subject.lower()
                            text_lower = text.lower()
                            
                            # Calculate subject occurrences
                            subject_count = text_lower.count(subject_lower)
                            keywords_found = [word for word in subject_lower.split() if len(word) > 3 and word in text_lower]
                            
                            # Simple keyword check for the subject
                            if subject_lower in text_lower:
                                contains_subject = True
                                # Adjust score based on frequency
                                if subject_count > 3 or len(keywords_found) >= 2:
                                    score = 75
                                    status = "PASSED"
                                    comments = f"Content appears to be relevant to {subject} with {subject_count} mentions"
                                else:
                                    score = 60
                                    status = "PASSED"
                                    comments = f"Content appears somewhat relevant to {subject} with limited mentions"
                            else:
                                # Check for common keywords that would indicate a mismatch
                                mismatch_subjects = {}
                                subject_keywords = {
                                    "physics": ["quantum", "mechanics", "physics", "particle", "wave", "energy"],
                                    "history": ["history", "century", "war", "civilization", "ancient", "medieval"],
                                    "mathematics": ["mathematics", "math", "algebra", "geometry", "calculus"],
                                    "biology": ["biology", "cell", "organism", "evolution", "gene", "dna"],
                                    "computer science": ["algorithm", "code", "programming", "computer", "software", "hardware"],
                                    "chemistry": ["chemical", "reaction", "molecule", "atom", "compound", "element"],
                                    "literature": ["novel", "author", "literary", "character", "plot", "narrative"]
                                }
                                
                                # Count occurrences of subject keywords in other subjects
                                for subj, keywords in subject_keywords.items():
                                    if subj.lower() != subject_lower:
                                        matches = sum(1 for word in keywords if word in text_lower)
                                        if matches >= 3:
                                            mismatch_subjects[subj] = matches
                                
                                # Check for mismatch
                                if mismatch_subjects:
                                    wrong_subject = max(mismatch_subjects.items(), key=lambda x: x[1])[0]
                                    contains_subject = False
                                    score = 10
                                    status = "FAILED"
                                    comments = f"Document contains '{wrong_subject}' which is unrelated to {subject}"
                                else:
                                    contains_subject = False
                                    score = 30
                                    status = "FAILED" 
                                    comments = f"Content appears unrelated to {subject}"
                            
                            return {
                                "status": status,
                                "relevance_score": score,
                                "comments": comments
                            }

                self.llm = DockerCompatLLM(model)
                logger.info("Successfully loaded model with Docker-compatible approach")
            else:
                # Standard approach
                self.llm = SandboxedLLM(model_path)
                logger.info("Successfully initialized SandboxedLLM")
        except Exception as e:
            # If SandboxedLLM fails, try direct llama.cpp approach
            logger.warning(f"Standard LLM initialization failed: {e}")
            logger.info("Attempting direct model loading with llama.cpp...")
            
            try:
                # Use our unified model loader with multiple fallback strategies
                logger.info(f"Loading model directly from: {model_path} using unified loader")
                llm_model, success, error_msg = load_model(model_path, max_attempts=3)
                
                if not success or llm_model is None:
                    raise RuntimeError(f"Failed to load model: {error_msg}")
                    
                logger.info("Model loaded successfully with unified loading approach")
                
                # Create a wrapper class that mimics SandboxedLLM but actually uses llama.cpp
                class DirectLLMWrapper:
                    def __init__(self, llm):
                        self.model = llm
                        self.model_loaded = True
                        logger.info("DirectLLMWrapper initialized")
                    
                    def check_plagiarism(self, text, references):
                        logger.info("Using direct llama.cpp for plagiarism check")
                        try:
                            # Select shorter content sample for efficient processing
                            content_sample = text[:1000] if len(text) > 1000 else text
                            
                            # Prepare reference sample
                            ref_sample = ""
                            for ref in references[:2]:  # Limit to first 2 references
                                ref_sample += f"Reference from {ref.get('title', 'Unknown')}:\n"
                                ref_sample += f"{ref.get('content', '')[:300]}...\n\n"
                            
                            # Create concise prompt for plagiarism assessment
                            prompt = f"""
                            You are a plagiarism detector. Compare these texts and return ONLY a similarity percentage (0-100).

                            TEXT:
                            {content_sample}
                            
                            REFERENCE:
                            {ref_sample}
                            
                            Respond with just a number between 0-100:
                            """
                            
                            # Call the model directly
                            result = self.model(prompt, max_tokens=10, temperature=0.1)
                            response = result["choices"][0]["text"]
                            
                            # Extract number from response
                            import re
                            num_match = re.search(r'(\d+(?:\.\d+)?)', response)
                            if num_match:
                                similarity = float(num_match.group(1))
                                # Ensure it's within bounds
                                similarity = max(0, min(100, similarity))
                                logger.info(f"Direct llama.cpp assessed plagiarism similarity: {similarity:.1f}%")
                                
                                return {
                                    "status": "checked",
                                    "plagiarism_percentage": similarity,
                                    "similar_sources": [],
                                    "llm_similarity": similarity
                                }
                            else:
                                    # Better fallback analysis instead of default 50%
                                logger.warning("Could not extract similarity score from model response, doing advanced analysis")
                                try:
                                    # Try to import enhanced detectors
                                    import enhanced_plagiarism_detector
                                    import ai_pattern_detector
                                    
                                    logger.info("Running fallback enhanced plagiarism detection...")
                                    results = enhanced_plagiarism_detector.detect_enhanced_plagiarism(text, references)
                                    
                                    logger.info(f"Enhanced plagiarism score: {results.get('plagiarism_percentage', 0):.1f}%")
                                    return results
                                except Exception as e:
                                    logger.error(f"Enhanced detection failed in fallback: {e}")
                                
                                # Manual checks for AI patterns if enhanced detection fails
                                ai_patterns = [
                                    "as an ai", "as an assistant", "as a language model",
                                    "i don't have personal", "i don't have the ability",
                                    "i don't have access", "my training data",
                                    "my training cut", "my knowledge cut"
                                ]
                                
                                # Check for emojis
                                emoji_pattern = re.compile("["
                                                        "\U0001F600-\U0001F64F"  # emoticons
                                                        "\U0001F300-\U0001F5FF"  # symbols & pictographs
                                                        "\U0001F680-\U0001F6FF"  # transport & map symbols
                                                        "]+", flags=re.UNICODE)
                                
                                emojis = emoji_pattern.findall(text)
                                ai_pattern_count = sum(1 for p in ai_patterns if p in text.lower())
                                
                                # Calculate plagiarism based on these patterns
                                score = 20  # Base score
                                if len(emojis) > 0:
                                    score += 40
                                    logger.warning(f"Emojis found in text: {emojis[:5]}")
                                    
                                if ai_pattern_count > 0:
                                    score += 30
                                    logger.warning(f"AI patterns found in text: {ai_pattern_count}")
                                
                                return {
                                    "status": "checked",
                                    "plagiarism_percentage": score,
                                    "similar_sources": [],
                                    "llm_similarity": score,
                                    "emoji_detected": len(emojis) > 0,
                                    "ai_patterns_detected": ai_pattern_count > 0
                                }
                        except Exception as e:
                            logger.error(f"Error in direct llama.cpp plagiarism check: {e}")
                            
                            # Try to use enhanced detection as fallback
                            try:
                                import enhanced_plagiarism_detector
                                logger.info("Using enhanced plagiarism detector as fallback after LLM error")
                                results = enhanced_plagiarism_detector.detect_enhanced_plagiarism(text, references)
                                logger.info(f"Fallback enhanced plagiarism score: {results.get('plagiarism_percentage', 0):.1f}%")
                                return results
                            except Exception as e2:
                                logger.error(f"Enhanced plagiarism detection also failed: {e2}")
                            
                            # If all else fails, do lightweight analysis
                            ai_patterns = [
                                "as an ai", "as an assistant", "as a language model",
                                "i don't have personal", "i don't have the ability",
                                "i don't have access", "my training data",
                                "my training cut", "my knowledge cut"
                            ]
                            
                            # Check for emojis
                            emoji_pattern = re.compile("["
                                                    "\U0001F600-\U0001F64F"  # emoticons
                                                    "\U0001F300-\U0001F5FF"  # symbols & pictographs  
                                                    "\U0001F680-\U0001F6FF"  # transport & map symbols
                                                    "]+", flags=re.UNICODE)
                            
                            emojis = emoji_pattern.findall(text)
                            ai_pattern_matches = [p for p in ai_patterns if p in text.lower()]
                            
                            # Calculate score based on simple analysis
                            score = 30  # Higher base score since LLM check failed
                            if emojis:
                                score += 30
                            if ai_pattern_matches:
                                score += 20
                            
                            return {
                                "status": "checked",
                                "plagiarism_percentage": score,
                                "similar_sources": [],
                                "llm_similarity": score,
                                "emoji_detected": bool(emojis),
                                "ai_patterns": ai_pattern_matches
                            }
                    
                    def validate_content(self, text, subject, references):
                        logger.info(f"Using direct llama.cpp for content validation on subject: {subject}")
                        try:
                            # Create a simplified prompt for content validation
                            prompt = f"""
                            Is this text about {subject}? Rate relevance 0-100.

                            TEXT: {text[:300]}

                            JSON response with ONLY these fields:
                            {{"relevance_score": number, "status": "PASSED" or "FAILED", "comments": "brief explanation"}}
                            """
                            
                            # Call the model directly
                            result = self.model(prompt, max_tokens=200, temperature=0.1)
                            response = result["choices"][0]["text"]
                            
                            # Try to extract JSON from response
                            import json
                            import re
                            
                            # Find JSON structure in response
                            logger.debug(f"Raw LLM response: {response[:500]}")
                            json_start = response.find("{")
                            json_end = response.rfind("}")
                            
                            # Try multiple JSON extraction approaches
                            if json_start >= 0 and json_end > json_start:
                                json_text = response[json_start:json_end+1]
                                logger.debug(f"Extracted JSON using braces: {json_text[:100]}...")
                                
                                # Clean up JSON text
                                json_text = json_text.replace('\\n', ' ').replace('\\t', ' ')
                                
                                # Fix common JSON formatting issues
                                json_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
                                json_text = re.sub(r':\s*\'([^\']+)\'', r':"\1"', json_text)
                                json_text = json_text.replace("'", '"')
                                
                                # Fix trailing commas which are invalid JSON
                                json_text = re.sub(r',\s*}', '}', json_text)
                                
                                try:
                                    validation = json.loads(json_text)
                                    logger.info(f"Successfully parsed JSON response from LLM: {list(validation.keys())}")
                                    
                                    # Ensure all required fields are present
                                    if "relevance_score" not in validation:
                                        validation["relevance_score"] = 60 if subject.lower() in text.lower() else 20
                                    if "status" not in validation:
                                        validation["status"] = "PASSED" if validation["relevance_score"] > 60 else "FAILED"
                                    if "comments" not in validation:
                                        validation["comments"] = f"The content's relevance to {subject} is {validation['relevance_score']}%"
                                        
                                    logger.info(f"Direct llama.cpp relevance assessment: {validation['relevance_score']}% for subject '{subject}'")
                                    return validation
                                except json.JSONDecodeError as json_err:
                                    logger.warning(f"JSON parsing error: {json_err}. Trying alternative extraction methods.")
                                    
                                    # Try to find any JSON-like pattern with status and relevance_score
                                    status_match = re.search(r'"status"\s*:\s*"(PASSED|FAILED)"', json_text, re.IGNORECASE)
                                    score_match = re.search(r'"relevance_score"\s*:\s*(\d+(?:\.\d+)?)', json_text)
                                    
                                    if status_match and score_match:
                                        status = status_match.group(1)
                                        score = float(score_match.group(1))
                                        logger.info(f"Extracted status ({status}) and score ({score}) directly from JSON-like text")
                                        return {
                                            "status": status,
                                            "relevance_score": score,
                                            "comments": f"Content relevance to {subject}: {score}%"
                                        }
                            
                            # If we couldn't parse JSON, try to extract just the relevance score number
                            number_match = re.search(r'\b(\d{1,3})\b', response)
                            if number_match:
                                score = min(100, max(0, int(number_match.group(1))))
                                logger.info(f"Extracted relevance score directly: {score}")
                                return {
                                    "status": "PASSED" if score > 35 else "FAILED",
                                    "relevance_score": score,
                                    "comments": f"Content relevance to {subject}: {score}%"
                                }
                            
                            # Content-based fallback (better than fixed numbers)
                            subject_lower = subject.lower()
                            subject_count = text.lower().count(subject_lower)
                            keywords_found = [word for word in subject_lower.split() if word in text.lower() and len(word) > 3]
                            is_relevant = (subject_count > 2 or len(keywords_found) >= 2) and subject_lower in text.lower()[:500]
                            
                            score = 70 if is_relevant else 30
                            logger.info(f"Using keyword analysis for relevance: score {score}%, subject mentions: {subject_count}, keywords found: {keywords_found}")
                            return {
                                "status": "PASSED" if is_relevant else "FAILED",
                                "relevance_score": score,
                                "comments": f"Content appears to be {'relevant' if is_relevant else 'not very relevant'} to {subject}. {'Found multiple direct mentions of the subject.' if subject_count > 2 else 'Found few mentions of the subject.'}"
                            }
                        except Exception as e:
                            logger.error(f"Error in direct llama.cpp content validation: {e}")
                            # Simple fallback
                            is_relevant = subject.lower() in text.lower()
                            return {
                                "status": "PASSED" if is_relevant else "FAILED",
                                "relevance_score": 60 if is_relevant else 20,
                                "comments": f"Error occurred in validation, fallback assessment: Content appears to be {'relevant' if is_relevant else 'not relevant'} to {subject}."
                            }
                        
                    def validate_content_semantic(self, text, subject, references):
                        return self.validate_content(text, subject, references)
                
                # Use the wrapper class
                self.llm = DirectLLMWrapper(llm_model)
                logger.info("✓ Successfully loaded model with direct llama.cpp approach")
                
            except Exception as direct_err:
                logger.error(f"Direct model loading also failed: {direct_err}")
                raise RuntimeError("All model loading approaches failed. Please check the model file.")
        
        # Don't initialize scraper in sandbox mode, only load references
        self.reference_sources = []
        os.makedirs("data", exist_ok=True)
        
        # Load references for offline use
        logger.info("Loading reference sources...")
        if os.path.exists(references_path):
            try:
                with open(references_path, "r", encoding="utf-8") as f:
                    self.reference_sources = json.load(f)
                
                if not self.reference_sources or len(self.reference_sources) == 0:
                    logger.warning(f"References file exists but contains no data")
                    self._create_mock_references()
                else:
                    logger.info(f"✓ Loaded {len(self.reference_sources)} reference sources from {references_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing references file: {e}")
                logger.warning("Creating mock reference sources")
                self._create_mock_references()
        else:
            logger.warning(f"References file not found: {references_path}")
            logger.warning("Creating mock reference sources")
            self._create_mock_references()
    
    def _enhanced_relevance_check(self, text, subject):
        """
        Enhanced relevance checking with multiple fallback strategies:
        1. First try keyword-based validation
        2. If keywords not found, use LLM with OCR sample
        3. If LLM fails, default to 45% relevance
        """
        logger.info(f"Starting enhanced relevance check for subject: {subject}")
        
        # Get configuration from environment variables
        relevance_mode = os.environ.get("RELEVANCE_MODE", "enhanced")
        min_threshold = int(os.environ.get("MIN_RELEVANCE_THRESHOLD", "35"))
        enable_llm_fallback = os.environ.get("ENABLE_LLM_FALLBACK", "true").lower() == "true"
        
        logger.info(f"Relevance mode: {relevance_mode}, Min threshold: {min_threshold}%, LLM fallback: {enable_llm_fallback}")
        
        # Step 1: Try keyword-based validation first (unless mode is llm_only)
        if relevance_mode != "llm_only":
            try:
                import subject_validation
                is_valid, confidence, reason = subject_validation.validate_subject_keywords(text, subject)
                    logger.info(f"No defined keyword rules for subject '{subject}', proceeding to LLM validation")
                    # Skip to LLM validation since we don't have keyword rules
                
                if is_valid and confidence > 50:
                    logger.info(f"Keywords found - direct validation successful: {confidence}% confidence")
                    return {
                        "status": "PASSED" if confidence >= min_threshold else "FAILED",
                        "relevance_score": confidence,
                        "comments": reason,
                        "validation_method": "keyword_based"
                    }
                elif not is_valid and confidence <= 20:
                    logger.warning(f"Strong keyword mismatch detected: {reason}")
                    return {
                        "status": "FAILED", 
                        "relevance_score": confidence,
                        "comments": reason,
                        "validation_method": "keyword_mismatch"
                    }
                else:
                    if relevance_mode == "keyword_only":
                        logger.info(f"Keyword-only mode: Using keyword result: {confidence}%")
                        return {
                            "status": "PASSED" if confidence >= min_threshold else "FAILED",
                            "relevance_score": confidence,
                            "comments": reason,
                            "validation_method": "keyword_only"
                        }
                    logger.info(f"Keywords validation inconclusive (confidence: {confidence}%), proceeding to LLM validation")
            except Exception as e:
                if relevance_mode == "keyword_only":
                    logger.error(f"Keyword validation failed in keyword_only mode: {e}")
                    return {
                        "status": "FAILED",
                        "relevance_score": min_threshold - 5,
                        "comments": f"Keyword validation failed: {str(e)}",
                        "validation_method": "keyword_error"
                    }
                logger.warning(f"Keyword validation failed: {e}, proceeding to LLM validation")
        
        # Step 2: Use LLM with OCR sample when keywords are not conclusive or when in llm_only mode
        if enable_llm_fallback or relevance_mode in ["llm_only", "enhanced"]:
            logger.info("Keywords not found or inconclusive - using LLM validation with OCR sample")
            
            try:
                # Create a 300-character sample from the beginning and middle of the text
                ocr_sample = ""
                if len(text) <= 300:
                    ocr_sample = text
                else:
                    # Take first 150 chars and middle 150 chars for better representation
                    first_part = text[:150]
                    middle_start = len(text) // 2 - 75
                    middle_part = text[middle_start:middle_start + 150]
                    ocr_sample = first_part + "..." + middle_part
                
                logger.info(f"Using OCR sample of {len(ocr_sample)} characters for LLM validation")
                
                # Create a focused prompt for relevance assessment
                relevance_prompt = f"""
                Analyze if this text content is relevant to the subject "{subject}".
                
                TEXT SAMPLE:
                {ocr_sample}
                
                SUBJECT: {subject}
                
                Rate the relevance from 0-100 and provide a brief explanation.
                Respond in JSON format:
                {{"relevance_score": number, "is_relevant": true/false, "explanation": "brief reason"}}
                """
                
                # Try to get LLM response
                if hasattr(self.llm, 'model') and self.llm.model:
                    logger.info("Using LLM model for relevance assessment")
                    result = self.llm.model(relevance_prompt, max_tokens=150, temperature=0.2)
                    response = result["choices"][0]["text"]
                    
                    # Parse LLM response
                    import json
                    import re
                    
                    logger.debug(f"LLM response for relevance: {response[:200]}...")
                    
                    # Try to extract JSON from response
                    json_start = response.find("{")
                    json_end = response.rfind("}")
                    
                    if json_start >= 0 and json_end > json_start:
                        json_text = response[json_start:json_end+1]
                        
                        # Clean up JSON
                        json_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
                        json_text = json_text.replace("'", '"')
                        json_text = re.sub(r',\s*}', '}', json_text)
                        
                        try:
                            llm_result = json.loads(json_text)
                            relevance_score = llm_result.get("relevance_score", min_threshold)
                            is_relevant = llm_result.get("is_relevant", relevance_score >= min_threshold)
                            explanation = llm_result.get("explanation", f"LLM assessed relevance to {subject}")
                            
                            # Ensure score is within bounds
                            relevance_score = max(0, min(100, relevance_score))
                            
                            logger.info(f"LLM relevance assessment: {relevance_score}% (relevant: {is_relevant})")
                            
                            return {
                                "status": "PASSED" if is_relevant and relevance_score >= min_threshold else "FAILED",
                                "relevance_score": relevance_score,
                                "comments": explanation,
                                "validation_method": "llm_sample_based"
                            }
                            
                        except json.JSONDecodeError as je:
                            logger.warning(f"Failed to parse LLM JSON response: {je}")
                            
                            # Try to extract just the score number
                            score_match = re.search(r'\b(\d{1,3})\b', response)
                            if score_match:
                                score = min(100, max(0, int(score_match.group(1))))
                                logger.info(f"Extracted relevance score from LLM response: {score}")
                                return {
                                    "status": "PASSED" if score >= min_threshold else "FAILED",
                                    "relevance_score": score,
                                    "comments": f"LLM assessment extracted from response: {score}% relevance to {subject}",
                                    "validation_method": "llm_score_extraction"
                                }
                    
                    # If JSON parsing failed, try simple keyword analysis on the LLM response
                    if "relevant" in response.lower() or "related" in response.lower():
                        score = max(min_threshold + 10, 60)
                        logger.info("LLM response indicates relevance, assigning elevated score")
                    elif "not relevant" in response.lower() or "unrelated" in response.lower():
                        score = max(min_threshold - 10, 25)
                        logger.info("LLM response indicates irrelevance, assigning low score")
                    else:
                        score = min_threshold
                        logger.info(f"LLM response unclear, using threshold score: {min_threshold}%")
                    
                    return {
                        "status": "PASSED" if score >= min_threshold else "FAILED",
                        "relevance_score": score,
                        "comments": f"LLM assessment based on response analysis: {score}% relevance to {subject}",
                        "validation_method": "llm_response_analysis"
                    }
                    
                else:
                    logger.warning("LLM model not available for relevance check")
                    
            except Exception as e:
                logger.error(f"LLM relevance assessment failed: {e}")
        
        # Step 3: Default fallback - 45% relevance
        logger.info("All validation methods failed, using default 45% relevance")
        
        # Always use 45% as the default fallback regardless of subject presence
        default_score = 45
        default_status = "PASSED" if default_score >= min_threshold else "FAILED"
        default_comments = f"Default assessment: Using fixed 45% relevance for {subject} after all checks failed"
        
        return {
            "status": default_status,
            "relevance_score": default_score,
            "comments": default_comments,
            "validation_method": "default_fallback"
        }
    
    def _verify_network_isolation(self):
        """Verify that the sandbox is properly isolated from the network"""
        logger.info("Verifying network isolation...")
        try:
            # Try to connect to a public DNS server with a short timeout
            socket.setdefaulttimeout(2)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            # If we reach this line, the connection was successful - network is NOT isolated
            logger.error("!!! SECURITY WARNING: Network isolation is NOT working correctly!")
            logger.error("!!! The container can access the internet, which poses a security risk.")
            logger.error("!!! Use '--network=none' with Docker run to enforce isolation.")
        except socket.error:
            # If we get an error, it means the connection failed - good, we are isolated
            logger.info("✓ Network isolation verified - sandbox is correctly isolated")
        except Exception as e:
            logger.warning(f"Unable to verify network isolation: {e}")
            
    def _create_mock_ocr(self):
        """Create a mock OCR processor in case of initialization failure"""
        class MockOCR:
            def process_document(self, file_path):
                logger.info(f"Using mock OCR processing for {file_path}")
                if file_path.lower().endswith(".pdf"):
                    return f"This is mock OCR text from PDF file {os.path.basename(file_path)}. " \
                           f"In a real system, this would contain the actual text extracted from the PDF. " \
                           f"For testing purposes, we're just generating placeholder content."
                else:
                    return f"This is mock OCR text from image file {os.path.basename(file_path)}. " \
                           f"In a real system, this would contain the actual text extracted from the image. " \
                           f"For testing purposes, we're just generating placeholder content."
        return MockOCR()
    
    def _create_mock_references(self):
        """Create mock references in case no references are available"""
        self.reference_sources = [{
            "url": "https://example.com/mock-reference",
            "title": "Mock Reference Source",
            "content": "This is a mock reference source created because no valid references were found. " \
                      "In a production system, this would be actual content scraped from the web. " \
                      "This mock content contains keywords like: algorithms, programming, data structures, " \
                      "computation, software engineering, machine learning, artificial intelligence."
        }]
        
        # Write mock references to file
        with open("data/references_mock.json", "w", encoding="utf-8") as f:
            json.dump(self.reference_sources, f, ensure_ascii=False, indent=2)
        
        logger.info("Created 1 mock reference source")

    def _get_subject_info(self, text, subject):
        """Get enhanced subject information using subject detector"""
        try:
            import subject_detector
            
            # Get subject analysis
            detected = subject_detector.detect_document_subject(text)
            mismatch = subject_detector.check_subject_mismatch(text, subject)
            
            logger.info(f"Detected subject: {detected['subject']} (confidence: {detected['confidence']:.1f}%)")
            logger.info(f"Declared subject: {subject}")
            logger.info(f"Subject match: {mismatch['is_match']} (confidence: {mismatch['match_confidence']:.1f}%)")
            
            # Get declared and detected subjects for reference collection
            info = {}
            try:
                if os.path.exists("data/info.json"):
                    with open("data/info.json", "r") as f:
                        info = json.load(f)
                        
                    # Add detected subject to info.json if not already there
                    if "detected_subject" not in info:
                        info["detected_subject"] = detected["subject"]
                        with open("data/info.json", "w") as f:
                            json.dump(info, f, indent=4)
            except Exception as e:
                logger.error(f"Error updating info.json: {e}")
            
            # Check if subject mismatch is extreme (strong sign of AI generation)
            significant_mismatch = mismatch['is_mismatch'] and mismatch['mismatch_severity'] == "high"
            
            return {
                "detected_subject": detected["subject"],
                "confidence": detected["confidence"],
                "is_match": mismatch["is_match"],
                "match_confidence": mismatch["match_confidence"],
                "mismatch_severity": mismatch["mismatch_severity"],
                "significant_mismatch": significant_mismatch,
                "keywords": detected["keywords"]
            }
        except ImportError:
            logger.warning("Subject detector not available")
            # Fallback to simple matching
            is_match = subject.lower() in text.lower()
            return {
                "detected_subject": "unknown",
                "is_match": is_match,
                "match_confidence": 100 if is_match else 0,
                "significant_mismatch": False
            }
        except Exception as e:
            logger.error(f"Error in subject detection: {e}")
            return {
                "detected_subject": "error",
                "is_match": True,  # Default to match to avoid false positives
                "match_confidence": 50,
                "significant_mismatch": False
            }
    
    def process_assignment(self, file_path, subject, assignment_id):
        try:
            logger.info("="*50)
            logger.info(f"PROCESSING ASSIGNMENT: {assignment_id}")
            logger.info(f"Subject: {subject}")
            logger.info(f"File: {file_path}")
            logger.info("="*50)
            
            # Create result structure for tracking status
            result = {
                "subject": subject,
                "assignment_id": assignment_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "sandbox_mode": True,
                "status": "PROCESSING"
            }
            
            # Verify file exists
            if not os.path.exists(file_path):
                logger.error(f"Assignment file not found: {file_path}")
                result["error"] = "Assignment file not found"
                result["status"] = "ERROR"
                return result
            
            # Extract text with OCR
            try:
                logger.info("Starting OCR text extraction...")
                start_time = datetime.datetime.now()
                ocr_text = self.ocr.process_document(file_path)
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                logger.info(f"OCR completed in {processing_time:.2f} seconds")
                
                if not ocr_text:
                    logger.error("OCR processing failed or returned no text")
                    result["error"] = "OCR processing failed or extracted no text"
                    result["status"] = "ERROR"
                    return result
                
                logger.info(f"✓ Successfully extracted {len(ocr_text)} characters of text")
                result["ocr_text_preview"] = ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text
                result["ocr_text_length"] = len(ocr_text)
                
                # Check if we have enough text to analyze
                if len(ocr_text) < 100:
                    logger.warning(f"⚠️ Extracted text is very short ({len(ocr_text)} chars), results may be unreliable")
                    result["warning"] = "Extracted text is very short, results may be unreliable"
            except Exception as e:
                logger.error(f"OCR processing error: {e}")
                result["error"] = f"OCR processing error: {str(e)}"
                result["status"] = "ERROR"
                return result
            
            # Analyze with LLM in sandbox
            try:
                logger.info("Running plagiarism check...")
                start_time = datetime.datetime.now()
                plagiarism_results = self.llm.check_plagiarism(ocr_text, self.reference_sources)
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                logger.info(f"Plagiarism check completed in {processing_time:.2f} seconds")
                logger.info(f"✓ Plagiarism percentage: {plagiarism_results.get('plagiarism_percentage', 0)}%")
                
                result["plagiarism_check"] = plagiarism_results
            except Exception as e:
                logger.error(f"Plagiarism checking error: {e}")
                result["plagiarism_check"] = {
                    "status": "error",
                    "plagiarism_percentage": 0,
                    "error": str(e),
                    "similar_sources": []
                }
            
            # Default validation values
            validation_status = "FAILED"
            relevance_score = 0
            
            try:
                logger.info("Validating content relevance using enhanced validation...")
                start_time = datetime.datetime.now()
                
                # Use the new enhanced relevance check function
                from enhanced_relevance_checker import enhanced_relevance_check
                validation = enhanced_relevance_check(ocr_text, subject, self.llm)
                
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                logger.info(f"Enhanced content validation completed in {processing_time:.2f} seconds")
                logger.info(f"✓ Relevance score: {validation.get('relevance_score', 0)}/100")
                logger.info(f"✓ Status: {validation.get('status', 'UNKNOWN')}")
                logger.info(f"✓ Method used: {validation.get('validation_method', 'unknown')}")
                
                # Extract validation results
                validation_status = validation.get("status", "FAILED")
                relevance_score = validation.get("relevance_score", 0)
                
                result["content_validation"] = validation
            except Exception as e:
                logger.error(f"Enhanced content validation error: {e}")
                result["content_validation"] = {
                    "status": "ERROR",
                    "relevance_score": 45,  # Default fallback
                    "comments": f"Validation error occurred, using default 45% relevance: {str(e)}",
                    "validation_method": "error_fallback"
                }
                validation_status = "FAILED"
                relevance_score = 45
            
            # Extract all plagiarism and AI detection information
            plagiarism_percentage = plagiarism_results.get("plagiarism_percentage", 0)
            llm_similarity = plagiarism_results.get("llm_similarity", 0)
            emoji_detected = plagiarism_results.get("emoji_detected", False)
            emoji_count = plagiarism_results.get("emoji_count", 0)
            
            # Enhanced AI detection features
            ai_patterns_detected = plagiarism_results.get("ai_patterns_detected", False)
            ai_confidence = plagiarism_results.get("ai_confidence", 0)
            ai_patterns = plagiarism_results.get("ai_patterns", [])
            
            # Add additional metrics to result
            result["ai_detection"] = {
                "ai_patterns_detected": ai_patterns_detected,
                "ai_confidence": ai_confidence,
                "patterns": ai_patterns
            }
            
            if llm_similarity > 0:
                logger.info(f"LLM-enhanced plagiarism detection score: {llm_similarity}%")
                
            if ai_patterns_detected:
                logger.warning(f"AI-generated content detected with {ai_confidence}% confidence")
            
            # Assignment passes if:
            # 1. Semantic similarity (plagiarism_percentage) is below threshold (< 40%)
            # 2. No emojis detected (indicates AI-generated content)
            # 3. No AI-generated patterns detected
            # 4. AI confidence is below threshold (< 60%)
            # 5. Relevance is above 35% (lowered threshold due to enhanced validation)
            
            # Check failure conditions
            failure_reasons = []
            
            # Check for subject mismatch (most severe issue)
            subject_mismatch = plagiarism_results.get("subject_mismatch", False)
            
            if subject_mismatch:
                mismatch_details = plagiarism_results.get("subject_mismatch_details", {})
                claimed = mismatch_details.get("claimed_subject", subject)
                detected = mismatch_details.get("detected_subjects", [])
                detected_subject = detected[0]["subject"] if detected else "unknown"
                
                failure_reasons.append(f"Subject-content mismatch: Paper claims to be about '{claimed}' but contains content about '{detected_subject}' - clear indication of AI-generated content")
            elif validation_status != "PASSED":
                if relevance_score < 30:
                    failure_reasons.append(f"Content is about a different subject than {subject} (relevance score: {relevance_score}%)")
                else:
                    failure_reasons.append(f"Content not sufficiently relevant to {subject} (score: {relevance_score}%)")
            
            # Get strict detection mode
            strict_mode = False
            try:
                if os.path.exists("data/info.json"):
                    with open("data/info.json", "r") as f:
                        info = json.load(f)
                        strict_mode = info.get("strict_ai_detection", False)
            except:
                pass
            
            # Use lower thresholds in strict mode
            if strict_mode:
                plagiarism_threshold = 35
                ai_confidence_threshold = 30
                logger.info("Using strict plagiarism/AI detection thresholds")
            else:
                plagiarism_threshold = 40
                ai_confidence_threshold = 60
            
            if plagiarism_percentage > plagiarism_threshold:
                failure_reasons.append(f"High plagiarism detected ({plagiarism_percentage}%)")
            
            if ai_confidence > ai_confidence_threshold:
                failure_reasons.append(f"High confidence AI-generated content detected ({ai_confidence}%)")
                
            if ai_patterns_detected:
                # Any AI pattern detection results in immediate failure
                failure_reasons.append(f"AI-generated content patterns detected - assignment fails academic integrity check")
                
            if emoji_detected:
                # Any emoji presence results in immediate failure
                failure_reasons.append(f"Inappropriate emoji usage detected ({emoji_count} emojis) - suggests AI-generated content")
            
            if not failure_reasons:
                result["status"] = "PASSED"
                logger.info("✓ Assignment PASSED validation")
            else:
                result["status"] = "FAILED"
                primary_reason = failure_reasons[0]
                result["failure_reason"] = primary_reason
                result["all_failure_reasons"] = failure_reasons
                logger.info(f"✗ Assignment FAILED: {primary_reason}")
            
            # Save full results to file
            try:
                output_file = f"data/result_{assignment_id}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"✓ Results saved to {output_file}")
                
                # Save full OCR text to a separate file for reference
                ocr_text_file = f"data/ocr_text_{assignment_id}.txt"
                with open(ocr_text_file, 'w', encoding='utf-8') as f:
                    f.write(ocr_text)
                logger.info(f"✓ Full OCR text saved to {ocr_text_file}")
            except Exception as e:
                logger.error(f"Error saving results: {e}")
            
            logger.info("="*50)
            logger.info(f"PROCESSING COMPLETE: {result['status']}")
            logger.info("="*50)
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in process_assignment: {e}")
            return {
                "subject": subject,
                "assignment_id": assignment_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "ERROR",
                "error": f"Unexpected error: {str(e)}",
                "sandbox_mode": True
            }
    
    def _enhanced_relevance_check(self, text, subject):
        """
        Enhanced relevance checking with multiple fallback strategies:
        1. First try keyword-based validation
        2. If keywords not found, use LLM with OCR sample
        3. If LLM fails, default to 45% relevance
        """
        logger.info(f"Starting enhanced relevance check for subject: {subject}")
        
        # Get configuration from environment variables
        relevance_mode = os.environ.get("RELEVANCE_MODE", "enhanced")
        min_threshold = int(os.environ.get("MIN_RELEVANCE_THRESHOLD", "35"))
        enable_llm_fallback = os.environ.get("ENABLE_LLM_FALLBACK", "true").lower() == "true"
        
        logger.info(f"Relevance mode: {relevance_mode}, Min threshold: {min_threshold}%, LLM fallback: {enable_llm_fallback}")
        
        # Step 1: Try keyword-based validation first (unless mode is llm_only)
        if relevance_mode != "llm_only":
            try:
                import subject_validation
                is_valid, confidence, reason = subject_validation.validate_subject_keywords(text, subject)
                    logger.info(f"No defined keyword rules for subject '{subject}', proceeding to LLM validation")
                    # Skip to LLM validation since we don't have keyword rules
                
                if is_valid and confidence > 50:
                    logger.info(f"Keywords found - direct validation successful: {confidence}% confidence")
                    return {
                        "status": "PASSED" if confidence >= min_threshold else "FAILED",
                        "relevance_score": confidence,
                        "comments": reason,
                        "validation_method": "keyword_based"
                    }
                elif not is_valid and confidence <= 20:
                    logger.warning(f"Strong keyword mismatch detected: {reason}")
                    return {
                        "status": "FAILED", 
                        "relevance_score": confidence,
                        "comments": reason,
                        "validation_method": "keyword_mismatch"
                    }
                else:
                    if relevance_mode == "keyword_only":
                        logger.info(f"Keyword-only mode: Using keyword result: {confidence}%")
                        return {
                            "status": "PASSED" if confidence >= min_threshold else "FAILED",
                            "relevance_score": confidence,
                            "comments": reason,
                            "validation_method": "keyword_only"
                        }
                    logger.info(f"Keywords validation inconclusive (confidence: {confidence}%), proceeding to LLM validation")
            except Exception as e:
                if relevance_mode == "keyword_only":
                    logger.error(f"Keyword validation failed in keyword_only mode: {e}")
                    return {
                        "status": "FAILED",
                        "relevance_score": min_threshold - 5,
                        "comments": f"Keyword validation failed: {str(e)}",
                        "validation_method": "keyword_error"
                    }
                logger.warning(f"Keyword validation failed: {e}, proceeding to LLM validation")
        
        # Step 2: Use LLM with OCR sample when keywords are not conclusive or when in llm_only mode
        if enable_llm_fallback or relevance_mode in ["llm_only", "enhanced"]:
            logger.info("Keywords not found or inconclusive - using LLM validation with OCR sample")
            
            try:
                # Create a 300-character sample from the beginning and middle of the text
                ocr_sample = ""
                if len(text) <= 300:
                    ocr_sample = text
                else:
                    # Take first 150 chars and middle 150 chars for better representation
                    first_part = text[:150]
                    middle_start = len(text) // 2 - 75
                    middle_part = text[middle_start:middle_start + 150]
                    ocr_sample = first_part + "..." + middle_part
                
                logger.info(f"Using OCR sample of {len(ocr_sample)} characters for LLM validation")
                
                # Create a focused prompt for relevance assessment
                relevance_prompt = f"""
                Analyze if this text content is relevant to the subject "{subject}".
                
                TEXT SAMPLE:
                {ocr_sample}
                
                SUBJECT: {subject}
                
                Rate the relevance from 0-100 and provide a brief explanation.
                Respond in JSON format:
                {{"relevance_score": number, "is_relevant": true/false, "explanation": "brief reason"}}
                """
                
                # Try to get LLM response
                if hasattr(self.llm, 'model') and self.llm.model:
                    logger.info("Using LLM model for relevance assessment")
                    result = self.llm.model(relevance_prompt, max_tokens=150, temperature=0.2)
                    response = result["choices"][0]["text"]
                    
                    # Parse LLM response
                    import json
                    import re
                    
                    logger.debug(f"LLM response for relevance: {response[:200]}...")
                    
                    # Try to extract JSON from response
                    json_start = response.find("{")
                    json_end = response.rfind("}")
                    
                    if json_start >= 0 and json_end > json_start:
                        json_text = response[json_start:json_end+1]
                        
                        # Clean up JSON
                        json_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
                        json_text = json_text.replace("'", '"')
                        json_text = re.sub(r',\s*}', '}', json_text)
                        
                        try:
                            llm_result = json.loads(json_text)
                            relevance_score = llm_result.get("relevance_score", min_threshold)
                            is_relevant = llm_result.get("is_relevant", relevance_score >= min_threshold)
                            explanation = llm_result.get("explanation", f"LLM assessed relevance to {subject}")
                            
                            # Ensure score is within bounds
                            relevance_score = max(0, min(100, relevance_score))
                            
                            logger.info(f"LLM relevance assessment: {relevance_score}% (relevant: {is_relevant})")
                            
                            return {
                                "status": "PASSED" if is_relevant and relevance_score >= min_threshold else "FAILED",
                                "relevance_score": relevance_score,
                                "comments": explanation,
                                "validation_method": "llm_sample_based"
                            }
                            
                        except json.JSONDecodeError as je:
                            logger.warning(f"Failed to parse LLM JSON response: {je}")
                            
                            # Try to extract just the score number
                            score_match = re.search(r'\b(\d{1,3})\b', response)
                            if score_match:
                                score = min(100, max(0, int(score_match.group(1))))
                                logger.info(f"Extracted relevance score from LLM response: {score}")
                                return {
                                    "status": "PASSED" if score >= min_threshold else "FAILED",
                                    "relevance_score": score,
                                    "comments": f"LLM assessment extracted from response: {score}% relevance to {subject}",
                                    "validation_method": "llm_score_extraction"
                                }
                    
                    # If JSON parsing failed, try simple keyword analysis on the LLM response
                    if "relevant" in response.lower() or "related" in response.lower():
                        score = max(min_threshold + 10, 60)
                        logger.info("LLM response indicates relevance, assigning elevated score")
                    elif "not relevant" in response.lower() or "unrelated" in response.lower():
                        score = max(min_threshold - 10, 25)
                        logger.info("LLM response indicates irrelevance, assigning low score")
                    else:
                        score = min_threshold
                        logger.info(f"LLM response unclear, using threshold score: {min_threshold}%")
                    
                    return {
                        "status": "PASSED" if score >= min_threshold else "FAILED",
                        "relevance_score": score,
                        "comments": f"LLM assessment based on response analysis: {score}% relevance to {subject}",
                        "validation_method": "llm_response_analysis"
                    }
                    
                else:
                    logger.warning("LLM model not available for relevance check")
                    
            except Exception as e:
                logger.error(f"LLM relevance assessment failed: {e}")
        
        # Step 3: Default fallback - 45% relevance
        logger.info("All validation methods failed, using default 45% relevance")
        
        # Always use 45% as the default fallback regardless of subject presence
        default_score = 45
        default_status = "PASSED" if default_score >= min_threshold else "FAILED"
        default_comments = f"Default assessment: Using fixed 45% relevance for {subject} after all checks failed"
        
        return {
            "status": default_status,
            "relevance_score": default_score,
            "comments": default_comments,
            "validation_method": "default_fallback"
        }
    
    def _verify_network_isolation(self):
        """Verify that the sandbox is properly isolated from the network"""
        logger.info("Verifying network isolation...")
        try:
            # Try to connect to a public DNS server with a short timeout
            socket.setdefaulttimeout(2)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            # If we reach this line, the connection was successful - network is NOT isolated
            logger.error("!!! SECURITY WARNING: Network isolation is NOT working correctly!")
            logger.error("!!! The container can access the internet, which poses a security risk.")
            logger.error("!!! Use '--network=none' with Docker run to enforce isolation.")
        except socket.error:
            # If we get an error, it means the connection failed - good, we are isolated
            logger.info("✓ Network isolation verified - sandbox is correctly isolated")
        except Exception as e:
            logger.warning(f"Unable to verify network isolation: {e}")
            
    def _create_mock_ocr(self):
        """Create a mock OCR processor in case of initialization failure"""
        class MockOCR:
            def process_document(self, file_path):
                logger.info(f"Using mock OCR processing for {file_path}")
                if file_path.lower().endswith(".pdf"):
                    return f"This is mock OCR text from PDF file {os.path.basename(file_path)}. " \
                           f"In a real system, this would contain the actual text extracted from the PDF. " \
                           f"For testing purposes, we're just generating placeholder content."
                else:
                    return f"This is mock OCR text from image file {os.path.basename(file_path)}. " \
                           f"In a real system, this would contain the actual text extracted from the image. " \
                           f"For testing purposes, we're just generating placeholder content."
        return MockOCR()
    
    def _create_mock_references(self):
        """Create mock references in case no references are available"""
        self.reference_sources = [{
            "url": "https://example.com/mock-reference",
            "title": "Mock Reference Source",
            "content": "This is a mock reference source created because no valid references were found. " \
                      "In a production system, this would be actual content scraped from the web. " \
                      "This mock content contains keywords like: algorithms, programming, data structures, " \
                      "computation, software engineering, machine learning, artificial intelligence."
        }]
        
        # Write mock references to file
        with open("data/references_mock.json", "w", encoding="utf-8") as f:
            json.dump(self.reference_sources, f, ensure_ascii=False, indent=2)
        
        logger.info("Created 1 mock reference source")

    def _get_subject_info(self, text, subject):
        """Get enhanced subject information using subject detector"""
        try:
            import subject_detector
            
            # Get subject analysis
            detected = subject_detector.detect_document_subject(text)
            mismatch = subject_detector.check_subject_mismatch(text, subject)
            
            logger.info(f"Detected subject: {detected['subject']} (confidence: {detected['confidence']:.1f}%)")
            logger.info(f"Declared subject: {subject}")
            logger.info(f"Subject match: {mismatch['is_match']} (confidence: {mismatch['match_confidence']:.1f}%)")
            
            # Get declared and detected subjects for reference collection
            info = {}
            try:
                if os.path.exists("data/info.json"):
                    with open("data/info.json", "r") as f:
                        info = json.load(f)
                        
                    # Add detected subject to info.json if not already there
                    if "detected_subject" not in info:
                        info["detected_subject"] = detected["subject"]
                        with open("data/info.json", "w") as f:
                            json.dump(info, f, indent=4)
            except Exception as e:
                logger.error(f"Error updating info.json: {e}")
            
            # Check if subject mismatch is extreme (strong sign of AI generation)
            significant_mismatch = mismatch['is_mismatch'] and mismatch['mismatch_severity'] == "high"
            
            return {
                "detected_subject": detected["subject"],
                "confidence": detected["confidence"],
                "is_match": mismatch["is_match"],
                "match_confidence": mismatch["match_confidence"],
                "mismatch_severity": mismatch["mismatch_severity"],
                "significant_mismatch": significant_mismatch,
                "keywords": detected["keywords"]
            }
        except ImportError:
            logger.warning("Subject detector not available")
            # Fallback to simple matching
            is_match = subject.lower() in text.lower()
            return {
                "detected_subject": "unknown",
                "is_match": is_match,
                "match_confidence": 100 if is_match else 0,
                "significant_mismatch": False
            }
        except Exception as e:
            logger.error(f"Error in subject detection: {e}")
            return {
                "detected_subject": "error",
                "is_match": True,  # Default to match to avoid false positives
                "match_confidence": 50,
                "significant_mismatch": False
            }
    
    def process_assignment(self, file_path, subject, assignment_id):
        try:
            logger.info("="*50)
            logger.info(f"PROCESSING ASSIGNMENT: {assignment_id}")
            logger.info(f"Subject: {subject}")
            logger.info(f"File: {file_path}")
            logger.info("="*50)
            
            # Create result structure for tracking status
            result = {
                "subject": subject,
                "assignment_id": assignment_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "sandbox_mode": True,
                "status": "PROCESSING"
            }
            
            # Verify file exists
            if not os.path.exists(file_path):
                logger.error(f"Assignment file not found: {file_path}")
                result["error"] = "Assignment file not found"
                result["status"] = "ERROR"
                return result
            
            # Extract text with OCR
            try:
                logger.info("Starting OCR text extraction...")
                start_time = datetime.datetime.now()
                ocr_text = self.ocr.process_document(file_path)
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                logger.info(f"OCR completed in {processing_time:.2f} seconds")
                
                if not ocr_text:
                    logger.error("OCR processing failed or returned no text")
                    result["error"] = "OCR processing failed or extracted no text"
                    result["status"] = "ERROR"
                    return result
                
                logger.info(f"✓ Successfully extracted {len(ocr_text)} characters of text")
                result["ocr_text_preview"] = ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text
                result["ocr_text_length"] = len(ocr_text)
                
                # Check if we have enough text to analyze
                if len(ocr_text) < 100:
                    logger.warning(f"⚠️ Extracted text is very short ({len(ocr_text)} chars), results may be unreliable")
                    result["warning"] = "Extracted text is very short, results may be unreliable"
            except Exception as e:
                logger.error(f"OCR processing error: {e}")
                result["error"] = f"OCR processing error: {str(e)}"
                result["status"] = "ERROR"
                return result
            
            # Analyze with LLM in sandbox
            try:
                logger.info("Running plagiarism check...")
                start_time = datetime.datetime.now()
                plagiarism_results = self.llm.check_plagiarism(ocr_text, self.reference_sources)
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                logger.info(f"Plagiarism check completed in {processing_time:.2f} seconds")
                logger.info(f"✓ Plagiarism percentage: {plagiarism_results.get('plagiarism_percentage', 0)}%")
                
                result["plagiarism_check"] = plagiarism_results
            except Exception as e:
                logger.error(f"Plagiarism checking error: {e}")
                result["plagiarism_check"] = {
                    "status": "error",
                    "plagiarism_percentage": 0,
                    "error": str(e),
                    "similar_sources": []
                }
            
            # Default validation values
            validation_status = "FAILED"
            relevance_score = 0
            
            try:
                logger.info("Validating content relevance against Wikipedia references...")
                start_time = datetime.datetime.now()
                
                # Use direct keyword validation first as a hard check
                try:
                    import subject_validation
                    is_valid, confidence, reason = subject_validation.validate_subject_keywords(ocr_text, subject)
                    
                    # If the direct validation strongly indicates a mismatch, override LLM validation
                    if not is_valid and confidence <= 20:
                        logger.warning(f"Direct keyword validation detected subject mismatch: {reason}")
                        validation = {
                            "status": "FAILED",
                            "relevance_score": confidence,
                            "comments": reason
                        }
                        logger.info("Used direct keyword validation - Subject mismatch detected")
                    else:
                        # Try to use the improved semantic validation
                        try:
                            validation = self.llm.validate_content_semantic(ocr_text, subject, self.reference_sources)
                            logger.info("Used enhanced semantic relevance detection")
                        except Exception as e:
                            logger.warning(f"Enhanced relevance detection failed: {e}, falling back to standard method")
                            validation = self.llm.validate_content(ocr_text, subject, self.reference_sources)
                except Exception as e:
                    logger.warning(f"Direct keyword validation failed: {e}, falling back to standard LLM method")
                    # Fall back to LLM validation
                    try:
                        validation = self.llm.validate_content_semantic(ocr_text, subject, self.reference_sources)
                        logger.info("Used enhanced semantic relevance detection")
                    except Exception as e:
                        logger.warning(f"Enhanced relevance detection failed: {e}, falling back to standard method")
                        validation = self.llm.validate_content(ocr_text, subject, self.reference_sources)
                
                processing_time = (datetime.datetime.now() - start_time).total_seconds()
                logger.info(f"Content validation completed in {processing_time:.2f} seconds")
                logger.info(f"✓ Relevance score: {validation.get('relevance_score', 0)}/100")
                logger.info(f"✓ Status: {validation.get('status', 'UNKNOWN')}")
                
                # Extract validation results
                validation_status = validation.get("status", "FAILED")
                relevance_score = validation.get("relevance_score", 0)
                
                result["content_validation"] = validation
            except Exception as e:
                logger.error(f"Content validation error: {e}")
                result["content_validation"] = {
                    "status": "ERROR",
                    "relevance_score": 0,
                    "comments": str(e)
                }
                validation_status = "ERROR"
                relevance_score = 0
            
            # Extract all plagiarism and AI detection information
            plagiarism_percentage = plagiarism_results.get("plagiarism_percentage", 0)
            llm_similarity = plagiarism_results.get("llm_similarity", 0)
            emoji_detected = plagiarism_results.get("emoji_detected", False)
            emoji_count = plagiarism_results.get("emoji_count", 0)
            
            # Enhanced AI detection features
            ai_patterns_detected = plagiarism_results.get("ai_patterns_detected", False)
            ai_confidence = plagiarism_results.get("ai_confidence", 0)
            ai_patterns = plagiarism_results.get("ai_patterns", [])
            
            # Add additional metrics to result
            result["ai_detection"] = {
                "ai_patterns_detected": ai_patterns_detected,
                "ai_confidence": ai_confidence,
                "patterns": ai_patterns
            }
            
            if llm_similarity > 0:
                logger.info(f"LLM-enhanced plagiarism detection score: {llm_similarity}%")
                
            if ai_patterns_detected:
                logger.warning(f"AI-generated content detected with {ai_confidence}% confidence")
            
            # Assignment passes if:
            # 1. Semantic similarity (plagiarism_percentage) is below threshold (< 40%)
            # 2. No emojis detected (indicates AI-generated content)
            # 3. No AI-generated patterns detected
            # 4. AI confidence is below threshold (< 60%)
            # 5. Relevance is above 35%
            
            # Check failure conditions
            failure_reasons = []
            
            # Check for subject mismatch (most severe issue)
            subject_mismatch = plagiarism_results.get("subject_mismatch", False)
            
            if subject_mismatch:
                mismatch_details = plagiarism_results.get("subject_mismatch_details", {})
                claimed = mismatch_details.get("claimed_subject", subject)
                detected = mismatch_details.get("detected_subjects", [])
                detected_subject = detected[0]["subject"] if detected else "unknown"
                
                failure_reasons.append(f"Subject-content mismatch: Paper claims to be about '{claimed}' but contains content about '{detected_subject}' - clear indication of AI-generated content")
            elif validation_status != "PASSED":
                if relevance_score < 30:
                    failure_reasons.append(f"Content is about a different subject than {subject} (relevance score: {relevance_score}%)")
                else:
                    failure_reasons.append(f"Content not sufficiently relevant to {subject} (score: {relevance_score}%)")
            
            # Get strict detection mode
            strict_mode = False
            try:
                if os.path.exists("data/info.json"):
                    with open("data/info.json", "r") as f:
                        info = json.load(f)
                        strict_mode = info.get("strict_ai_detection", False)
            except:
                pass
            
            # Use lower thresholds in strict mode
            if strict_mode:
                plagiarism_threshold = 35
                ai_confidence_threshold = 30
                logger.info("Using strict plagiarism/AI detection thresholds")
            else:
                plagiarism_threshold = 40
                ai_confidence_threshold = 60
            
            if plagiarism_percentage > plagiarism_threshold:
                failure_reasons.append(f"High plagiarism detected ({plagiarism_percentage}%)")
            
            if ai_confidence > ai_confidence_threshold:
                failure_reasons.append(f"High confidence AI-generated content detected ({ai_confidence}%)")
                
            if ai_patterns_detected:
                # Any AI pattern detection results in immediate failure
                failure_reasons.append(f"AI-generated content patterns detected - assignment fails academic integrity check")
                
            if emoji_detected:
                # Any emoji presence results in immediate failure
                failure_reasons.append(f"Inappropriate emoji usage detected ({emoji_count} emojis) - suggests AI-generated content")
            
            if not failure_reasons:
                result["status"] = "PASSED"
                logger.info("✓ Assignment PASSED validation")
            else:
                result["status"] = "FAILED"
                primary_reason = failure_reasons[0]
                result["failure_reason"] = primary_reason
                result["all_failure_reasons"] = failure_reasons
                logger.info(f"✗ Assignment FAILED: {primary_reason}")
            
            # Save full results to file
            try:
                output_file = f"data/result_{assignment_id}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"✓ Results saved to {output_file}")
                
                # Save full OCR text to a separate file for reference
                ocr_text_file = f"data/ocr_text_{assignment_id}.txt"
                with open(ocr_text_file, 'w', encoding='utf-8') as f:
                    f.write(ocr_text)
                logger.info(f"✓ Full OCR text saved to {ocr_text_file}")
            except Exception as e:
                logger.error(f"Error saving results: {e}")
            
            logger.info("="*50)
            logger.info(f"PROCESSING COMPLETE: {result['status']}")
            logger.info("="*50)
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in process_assignment: {e}")
            return {
                "subject": subject,
                "assignment_id": assignment_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "ERROR",
                "error": f"Unexpected error: {str(e)}",
                "sandbox_mode": True
            }

    def validate(self):
        """Validate the document"""
        # Use OCR to extract text from file
        logger.info(f"Performing OCR on file: {self.file_path}")
        
        try:
            ocr_output_file = f"data/ocr_text_{self.assignment_id}.txt"
            
            # Check if the OCR was already done
            if os.path.exists(ocr_output_file):
                with open(ocr_output_file, 'r') as f:
                    text = f.read()
                    logger.info(f"Using existing OCR text from {ocr_output_file}")
            else:
                text = self.ocr.process_document(self.file_path, ocr_output_file)
                logger.info(f"OCR complete, saved to {ocr_output_file}")
            
            # Load reference materials
            references = self._load_references()
            
            # Get subject info and use detected subject if confidence is high
            subject_info = self._get_subject_info(text, self.subject)
            effective_subject = self.subject
            
            # Use detected subject if it's significantly different and high confidence
            if subject_info["confidence"] > 70 and not subject_info["is_match"]:
                detected_subject = subject_info["detected_subject"]
                logger.warning(f"Using detected subject '{detected_subject}' instead of declared '{self.subject}'")
                effective_subject = detected_subject
                
                # Update info.json with detected subject
                try:
                    if os.path.exists("data/info.json"):
                        with open("data/info.json", "r") as f:
                            info = json.load(f)
                        info["detected_subject"] = detected_subject
                        with open("data/info.json", "w") as f:
                            json.dump(info, f, indent=4)
                except Exception as e:
                    logger.error(f"Error updating info.json with detected subject: {e}")
            
            # Pass both declared and detected subjects to llm
            validation_result = self.llm.validate_content(text, effective_subject, references)
            
            # Check for plagiarism
            plagiarism_result = self.llm.check_plagiarism(text, references)
            
            # Build validation result
            result = {
                "status": "PASSED",
                "id": self.assignment_id,
                "subject": self.subject,
                "detected_subject": subject_info.get("detected_subject", "unknown"),
                "subject_match": subject_info.get("is_match", True),
                "validation_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "plagiarism_check": plagiarism_result,
                "content_validation": validation_result
            }
            
            return result
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return {
                "status": "ERROR",
                "error": str(e)
            }

def main():
    parser = argparse.ArgumentParser(description="Assignment Validation System")
    parser.add_argument("--file", required=True, help="Path to assignment file (PDF or image)")
    parser.add_argument("--subject", required=True, help="Subject of the assignment")
    parser.add_argument("--id", required=True, help="Assignment ID")
    parser.add_argument("--model", default="models/llama-3-8b-instruct.gguf", help="Path to LLM model file")
    parser.add_argument("--references", default="data/references.json", help="Path to reference data JSON file")
    args = parser.parse_args()
    
    validator = AssignmentValidator(args.model, references_path=args.references)
    result = validator.process_assignment(args.file, args.subject, args.id)
    
    print("\n=== ASSIGNMENT VALIDATION RESULTS ===")
    print(f"Subject: {args.subject}")
    print(f"Assignment ID: {args.id}")
    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Plagiarism: {result.get('plagiarism_check', {}).get('plagiarism_percentage', 0)}%")
    print(f"Relevance: {result.get('content_validation', {}).get('relevance_score', 0)}/100")
    print(f"Comments: {result.get('content_validation', {}).get('comments', 'No comments')}")
    
    if "error" in result:
        print(f"\nERROR: {result['error']}")
    if "failure_reason" in result:
        print(f"\nFailure reason: {result['failure_reason']}")
    
    print(f"\nFull results saved to data/result_{args.id}.json")
    print(f"Full OCR text saved to data/ocr_text_{args.id}.txt")

if __name__ == "__main__":
    main()
