import os
import json
import time
import logging
import numpy as np
import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llm_sandbox')

# Set environment variables to enforce offline mode
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

class SandboxedLLM:
    def __init__(self, model_path=None, max_attempts=3):
        """Initialize sandboxed LLM environment with no internet access"""
        self.model_path = model_path
        self.model_loaded = False
        self.llm = None
        self.text_splitter = None
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents='unicode',
            ngram_range=(1, 2),
            max_df=0.85,
            min_df=2,
            max_features=10000
        )
        
        logger.info(f"LLM sandbox initialized in offline mode")
        
        if model_path and os.path.exists(model_path):
            try:
                # Check if we have a real model file or should use mock mode
                is_real_model = False
                try:
                    file_size = os.path.getsize(model_path)
                    is_real_model = file_size > 1000000  # If file is more than 1MB
                    logger.info(f"Model file size: {file_size/1024/1024:.2f} MB")
                except Exception as e:
                    logger.error(f"Error checking model file size: {e}")
                
                if is_real_model:
                    logger.info(f"Loading LLM model from {model_path}")
                    
                    # Attempt to load model with retries
                    attempt = 0
                    while attempt < max_attempts:
                        attempt += 1
                        try:
                            # Try to load Llama model using llama-cpp-python
                            from llama_cpp import Llama
                            
                            # Check model file permissions
                            if not os.access(model_path, os.R_OK):
                                logger.warning(f"Model file permissions issue, fixing...")
                                try:
                                    os.chmod(model_path, 0o644)
                                    logger.info(f"Fixed model file permissions")
                                except Exception as perm_err:
                                    logger.error(f"Failed to fix model permissions: {perm_err}")
                            
                            # Load the Phi-2 model with appropriate parameters
                            # With llama-cpp-python v0.3.9+, Phi-2 architecture is natively supported
                            # Using smaller context size for faster performance
                            self.llm = Llama(
                                model_path=model_path,
                                n_ctx=2048,  # Reduced context window for faster inference
                                n_gpu_layers=-1,  # Auto-detect GPU layers
                                n_batch=512,
                                verbose=True
                            )
                            self.model_loaded = True
                            logger.info(f"Phi-2 model loaded successfully")
                            break
                        except ImportError as e:
                            logger.error(f"Missing dependency: {e}")
                            logger.info("Cannot load Llama model due to missing dependencies")
                            break  # Don't retry on import error
                        except Exception as e:
                            logger.error(f"Failed to load Llama model (attempt {attempt}/{max_attempts}): {e}")
                            if attempt == max_attempts:
                                logger.error("Maximum retry attempts reached")
                            else:
                                logger.info(f"Retrying in 2 seconds...")
                                time.sleep(2)
                    
                    if not self.model_loaded:
                        logger.error("Failed to load the Phi-2 model after maximum attempts")
                        raise RuntimeError("Failed to load the Phi-2 model. Please check the model file.")
                else:
                    logger.error(f"Model file too small or corrupt")
                    raise RuntimeError("Model file is too small or corrupt. Please provide a valid Phi-2 model file.")
            except Exception as e:
                logger.error(f"Error checking model file: {e}")
                raise
        else:
            logger.error(f"No model path provided or file not found at: {model_path}")
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        
        # Setup text chunking
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            logger.info("Text splitter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize text splitter: {e}")
            
    def _split_text(self, text):
        """Split text into chunks for processing"""
        if self.text_splitter:
            try:
                chunks = self.text_splitter.split_text(text)
                return chunks
            except Exception as e:
                logger.error(f"Error splitting text: {e}")
        
        # Fallback manual chunking if text_splitter fails
        chunks = []
        words = text.split()
        chunk_size = 500  # approx words per chunk
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i+chunk_size])
            chunks.append(chunk)
        return chunks
    
    def check_plagiarism(self, text, reference_sources):
        """
        Check plagiarism using enhanced detection:
        1. TF-IDF vector similarity for semantic similarity (plagiarism_percentage)
        2. AI pattern detection with linguistic and statistical analysis
        3. N-gram comparison for exact matches
        4. Emoji detection to catch AI-generated content
        
        Thresholds for failure:
        - Semantic similarity > 75%: Fail
        - AI patterns detected: Fail
        - Any emoji detected: Fail
        """
        logger.info(f"Starting enhanced plagiarism check on {len(text)} chars against {len(reference_sources)} sources")
        
        # Check for strict AI detection in info.json
        strict_ai_detection = False
        try:
            if os.path.exists("data/info.json"):
                with open("data/info.json", "r") as f:
                    info = json.load(f)
                    strict_ai_detection = info.get("strict_ai_detection", False)
                    if strict_ai_detection:
                        logger.info("Strict AI detection enabled in info.json")
        except Exception as e:
            logger.warning(f"Error reading info.json for detection mode: {e}")
        
        try:
            # Try to use enhanced plagiarism detector
            import enhanced_plagiarism_detector
            
            # Log that we're using the enhanced detector
            logger.info("Using enhanced plagiarism detector with multi-method analysis")
            
            # Run enhanced plagiarism detection
            enhanced_results = enhanced_plagiarism_detector.detect_enhanced_plagiarism(text, reference_sources)
            logger.info(f"Enhanced plagiarism check complete: {enhanced_results.get('plagiarism_percentage', 0):.1f}% similarity")
            
            # Log detailed results
            logger.info(f"AI patterns detected: {enhanced_results.get('ai_patterns_detected', False)}")
            logger.info(f"AI confidence: {enhanced_results.get('ai_confidence', 0):.1f}%")
            logger.info(f"Statistical similarity: {enhanced_results.get('statistical_similarity', 0):.1f}%")
            logger.info(f"N-gram similarity: {enhanced_results.get('ngram_similarity', 0):.1f}%")
            
            if enhanced_results.get("ai_patterns_detected"):
                logger.warning("AI-generated content patterns detected")
                
            if enhanced_results.get("emoji_detected"):
                logger.warning(f"Detected {enhanced_results.get('emoji_count', 0)} emojis in the text")
                
            # If strict AI detection is enabled, increase the plagiarism score for AI-generated content
            if strict_ai_detection and enhanced_results.get("ai_confidence", 0) > 65:
                logger.warning("Strict AI detection active - increasing plagiarism score due to AI confidence")
                enhanced_results["plagiarism_percentage"] = max(
                    enhanced_results["plagiarism_percentage"],
                    enhanced_results["ai_confidence"]
                )
                
            return enhanced_results
                
        except ImportError as e:
            logger.warning(f"Enhanced plagiarism detector not available: {e}")
            logger.warning("Falling back to basic plagiarism detection")
            return self._legacy_plagiarism_check(text, reference_sources)
        except Exception as e:
            logger.error(f"Error in enhanced plagiarism check: {e}")
            logger.warning("Falling back to basic plagiarism detection")
            return self._legacy_plagiarism_check(text, reference_sources)
    
    def _legacy_plagiarism_check(self, text, reference_sources):
        """Legacy plagiarism detection method - used as fallback"""
        # Initialize plagiarism results structure
        plagiarism_results = {
            "status": "checked",
            "plagiarism_percentage": 0,  # Semantic similarity percentage
            "similar_sources": [],       # Examples of similar content
            "emoji_detected": False,     # Flag for emoji detection
            "emoji_count": 0,            # Count of emojis found
            "emoji_list": [],            # Sample of emojis found
            "llm_similarity": 0,         # LLM-assessed similarity percentage
            "ai_patterns_detected": False, # Flag for AI pattern detection
            "ai_patterns": []            # List of AI patterns found
        }
        
        # Check for emoji usage - academic assignments shouldn't have emojis
        emojis_found = self._detect_emojis(text)
        if emojis_found:
            plagiarism_results["emoji_detected"] = True
            plagiarism_results["emoji_count"] = len(emojis_found)
            plagiarism_results["emoji_list"] = emojis_found[:10]  # Limit to first 10 emojis
            logger.info(f"Detected {len(emojis_found)} emojis in the text")
        
        # Check for common AI-generated text patterns
        ai_patterns = self._detect_ai_patterns(text)
        if ai_patterns:
            plagiarism_results["ai_patterns_detected"] = True
            plagiarism_results["ai_patterns"] = ai_patterns
            logger.info(f"Detected {len(ai_patterns)} AI-generated text patterns:")
        
        if not reference_sources or len(reference_sources) == 0:
            logger.warning("No reference sources provided for plagiarism check")
            plagiarism_results["status"] = "no_references"
            return plagiarism_results
        
        try:
            # Split text into chunks
            assignment_chunks = self._split_text(text)
            logger.info(f"Split assignment into {len(assignment_chunks)} chunks")
            
            # Prepare reference content
            references = []
            for source in reference_sources:
                if "content" in source and source["content"]:
                    # Split reference content into chunks too
                    ref_chunks = self._split_text(source["content"])
                    for chunk in ref_chunks:
                        references.append({
                            "content": chunk,
                            "url": source.get("url", ""),
                            "title": source.get("title", "Unknown source")
                        })
            
            logger.info(f"Processed {len(references)} reference chunks")
            
            if not references:
                logger.warning("No valid reference content found")
                return {
                    "status": "no_valid_references",
                    "plagiarism_percentage": 0,
                    "similar_sources": []
                }
            
            # Create corpus of all text chunks (assignment + references)
            corpus = [chunk for chunk in assignment_chunks]
            corpus.extend([ref["content"] for ref in references])
            
            # Compute TF-IDF vectors
            try:
                tfidf_matrix = self.vectorizer.fit_transform(corpus)
                
                # Compute similarity between assignment chunks and reference chunks
                similar_chunks = []
                plagiarized_chunks = 0
                
                for i, assignment_chunk in enumerate(assignment_chunks):
                    # Get vector for this assignment chunk
                    chunk_vector = tfidf_matrix[i]
                    
                    # Compare with all reference chunks
                    highest_similarity = 0
                    most_similar_ref = None
                    
                    for j, ref in enumerate(references, start=len(assignment_chunks)):
                        ref_vector = tfidf_matrix[j]
                        similarity = cosine_similarity(chunk_vector, ref_vector)[0][0]
                        
                        if similarity > highest_similarity:
                            highest_similarity = similarity
                            most_similar_ref = ref
                    
                    # If similarity above threshold, consider it plagiarized
                    # Lower threshold to 0.3 to catch more subtle plagiarism
                    if highest_similarity > 0.3 and most_similar_ref:
                        plagiarized_chunks += 1
                        if len(similar_chunks) < 3:  # Limit to 3 examples
                            similar_chunks.append({
                                "assignment_chunk": assignment_chunk[:200] + "..." if len(assignment_chunk) > 200 else assignment_chunk,
                                "matched_source": most_similar_ref["url"],
                                "source_title": most_similar_ref["title"],
                                "similarity_score": round(highest_similarity * 100, 1)
                            })
                
                # Calculate overall plagiarism percentage
                plagiarism_percentage = round((plagiarized_chunks / len(assignment_chunks)) * 100, 1) if assignment_chunks else 0
                
                # Add detailed logging about plagiarism detection
                logger.info(f"Plagiarism check results: {plagiarized_chunks} out of {len(assignment_chunks)} chunks flagged")
                logger.info(f"Overall plagiarism percentage: {plagiarism_percentage}%")
                if similar_chunks:
                    logger.info(f"Top similar chunk has similarity score: {similar_chunks[0]['similarity_score']}%")
                else:
                    logger.info("No chunks above similarity threshold")
                
                # Always use the real Phi-2 model via llama.cpp for enhanced plagiarism detection
                if not self.model_loaded or not self.llm:
                    # This should never happen as we verify the model during initialization
                    logger.error("Real Phi-2 model via llama.cpp is required for plagiarism detection")
                    plagiarism_results.update({
                        "status": "checked",
                        "plagiarism_percentage": plagiarism_percentage,
                        "similar_sources": similar_chunks,
                        "llm_similarity": 50.0  # Default to moderate similarity when model can't be used
                    })
                    return plagiarism_results
                    
                try:
                    # Use a smaller sample for faster processing
                    content_sample = text[:1000] if len(text) > 1000 else text
                    
                    # Prepare reference sample - shorter for faster processing
                    ref_sample = ""
                    for ref in references[:2]:  # limit to first 2 references
                        ref_sample += f"Reference from {ref.get('title', 'Unknown')}:\n"
                        ref_sample += f"{ref.get('content', '')[:300]}...\n\n"
                    
                    # Create a more concise prompt for the LLM to assess plagiarism and AI generation
                    prompt = f"""
                    You are a plagiarism and AI-text detector with expertise in academic integrity. 
                    
                    Analyze this text sample and determine:
                    1. The similarity percentage to the reference material (0-100)
                    2. If the text appears to be AI-generated based on structure, phrasing, or tone
                    
                    Give a higher similarity score if you detect AI-generated writing patterns.

                    TEXT:
                    {content_sample}
                    
                    REFERENCE:
                    {ref_sample}
                    
                    Respond with just a number between 0-100 representing your assessment:
                    """
                    
                    # Use the model to get similarity score
                    result = self.llm(prompt, max_tokens=10, temperature=0.1)
                    response = result["choices"][0]["text"] if isinstance(result, dict) else result
                    
                    # Extract just the number from the response
                    import re
                    num_match = re.search(r'(\d+(?:\.\d+)?)', response)
                    if num_match:
                        llm_similarity = float(num_match.group(1))
                        # Ensure it's within bounds
                        llm_similarity = max(0, min(100, llm_similarity))
                        logger.info(f"Phi-2 model assessed plagiarism similarity: {llm_similarity:.1f}%")
                    else:
                        # If we can't extract a number, compute a score based on TF-IDF results
                        highest_similarity = max([chunk.get('similarity_score', 0) for chunk in similar_chunks]) if similar_chunks else 0
                        llm_similarity = min(100, plagiarism_percentage * 1.5 + highest_similarity * 0.2)
                        logger.info(f"Using TF-IDF based plagiarism score: {llm_similarity:.1f}%")
                except Exception as e:
                    logger.error(f"Error using LLM for plagiarism detection: {e}")
                    # Use a fallback method that doesn't rely on the LLM
                    highest_similarity = max([chunk.get('similarity_score', 0) for chunk in similar_chunks]) if similar_chunks else 0
                    llm_similarity = min(100, plagiarism_percentage * 1.5 + highest_similarity * 0.2)
                    logger.info(f"Using TF-IDF based fallback plagiarism score: {llm_similarity:.1f}%")
                
                # Update the plagiarism results
                plagiarism_results.update({
                    "status": "checked",
                    "plagiarism_percentage": plagiarism_percentage,
                    "similar_sources": similar_chunks,
                    "llm_similarity": round(llm_similarity, 1)
                })
                
                return plagiarism_results
                
            except Exception as e:
                logger.error(f"Error in TF-IDF computation: {e}")
                plagiarism_results["status"] = "error"
                plagiarism_results["error"] = str(e)
                return plagiarism_results
        
        except Exception as e:
            logger.error(f"Error in legacy plagiarism check: {e}")
            plagiarism_results["status"] = "error"
            plagiarism_results["error"] = str(e)
            return plagiarism_results
    def validate_content(self, text, subject, reference_sources=None):
        """Validate if content is relevant to subject and reference materials"""
        logger.info(f"Validating content relevance for subject: {subject}")
        
        # First do a quick pattern check for the assignment
        text_lower = text.lower()
        subject_lower = subject.lower()
        
        # Perform subject mismatch check
        # Check for obvious mismatches between subject and content
        subject_mismatch_dict = {
            "history": ["quantum mechanics", "quantum physics", "artificial intelligence", "machine learning", "neural networks", "computer science"],
            "computer science": ["ancient history", "world war", "medieval history", "ancient civilization"],
            "physics": ["literature", "novels", "poetry", "ancient history"],
            "literature": ["quantum mechanics", "artificial intelligence", "physics equations"],
            "artificial intelligence": ["ancient history", "medieval times", "literature classics"]
        }
        
        # Check for clear mismatch between subject and content
        if subject_lower in subject_mismatch_dict:
            for mismatch_term in subject_mismatch_dict[subject_lower]:
                if mismatch_term in text_lower[:500]:
                    logger.info(f"Found clear subject mismatch: Document mentions '{mismatch_term}' but subject is '{subject}'")
                    return {
                        "status": "FAILED",
                        "relevance_score": 10,
                        "comments": f"The document appears to be about {mismatch_term} which is not related to {subject}."
                    }
        
        # If the text title/intro explicitly mentions the subject in assignment context,
        # we can immediately return high relevance without using the LLM
        if (f"assignment on {subject_lower}" in text_lower[:200] or 
            (subject_lower in text_lower[:200] and "assignment" in text_lower[:200])):
            logger.info(f"Found explicit mention of '{subject}' assignment in the text. Highly relevant.")
            return {
                "status": "PASSED",
                "relevance_score": 90,
                "comments": f"The document is highly relevant to {subject} as it explicitly mentions being an assignment on this subject."
            }
        
        # Quick check for AI-specific patterns
        if subject_lower == "artificial intelligence":
            ai_patterns_count = 0
            # Check for "AI" acronym
            if re.search(r'\b(AI|A\.I\.)\b', text):
                ai_patterns_count += 1
            
            # Check for mentions of AI types like "narrow AI", "general AI"
            if re.search(r'\b(narrow|general|strong)\s+(AI|intelligence)\b', text_lower):
                ai_patterns_count += 1
                
            # Check for mentions of AI applications
            if re.search(r'applications\s+of\s+(AI|artificial intelligence)', text_lower):
                ai_patterns_count += 1
                
            # If we found multiple AI patterns, it's likely relevant
            if ai_patterns_count >= 2:
                logger.info(f"Found {ai_patterns_count} AI-specific patterns in text. Highly relevant.")
                return {
                    "status": "PASSED",
                    "relevance_score": 80,
                    "comments": f"The content is highly relevant to Artificial Intelligence based on multiple AI-specific terminology and patterns."
                }
        
        # If the quick checks didn't confirm relevance, use the LLM
        if self.model_loaded and self.llm:
            try:
                # Use the real LLM for content validation with a more rigorous prompt
                prompt = f"""
                TASK: Analyze if the text is actually about {subject}. 
                Be strict and critical - identify if the content specifically addresses {subject} or if it's about something else.
                
                Criteria for relevance:
                - Content must specifically discuss topics central to {subject}
                - Main themes and terminology should match {subject} field
                - Document shouldn't primarily be about another unrelated subject
                - Brief mentions of {subject} aren't enough for high relevance
                
                TEXT: {text[:500]}
                
                Rate relevance 0-100 where:
                0-30: Clearly about a different subject
                31-60: Has some relation but is not primarily about {subject}
                61-100: Primarily about {subject}
                
                Provide JSON response with ONLY these fields:
                {{"relevance_score": number, "status": "PASSED" or "FAILED", "comments": "specific explanation with evidence from text"}}
                """
                
                result = self.llm(prompt, max_tokens=200, temperature=0.1)
                
                # Parse the JSON from the response
                try:
                    # Get the text and find the JSON
                    json_text = result["choices"][0]["text"] if isinstance(result, dict) else result
                    json_text = json_text.strip()
                    
                    logger.debug(f"Raw LLM response: {json_text[:500]}")
                    
                    # Try multiple JSON extraction strategies
                    import re
                    
                    # Strategy 1: Find JSON between curly braces
                    json_start = json_text.find("{")
                    json_end = json_text.rfind("}")
                    
                    if json_start >= 0 and json_end > json_start:
                        json_text = json_text[json_start:json_end+1]
                        logger.debug(f"Extracted JSON using braces: {json_text[:100]}...")

                    # Clean up the JSON text
                    json_text = json_text.replace('\\n', ' ').replace('\\t', ' ')
                    
                    # Fix common JSON formatting issues with regex
                    json_text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text)
                    json_text = re.sub(r':\s*\'([^\']+)\'', r':"\1"', json_text)
                    json_text = json_text.replace("'", '"')
                    
                    # Advanced JSON cleaning: Fix trailing commas which are invalid JSON
                    json_text = re.sub(r',\s*}', '}', json_text)
                    
                    # Try to parse the cleaned JSON
                    try:
                        validation = json.loads(json_text)
                        logger.info(f"Successfully parsed JSON response from LLM: {validation.keys()}")
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"JSON parsing error: {json_err}. Trying alternative extraction methods.")
                        
                        # Strategy 2: Try to find JSON object with key-value structure
                        json_pattern = r'{(?:[^{}]|"[^"]*")*}'
                        json_matches = re.findall(json_pattern, json_text)
                        
                        if json_matches:
                            for potential_json in json_matches:
                                try:
                                    # Try to fix JSON format issues
                                    fixed_json = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', potential_json)
                                    fixed_json = fixed_json.replace("'", '"')
                                    validation = json.loads(fixed_json)
                                    logger.info(f"Successfully parsed JSON using pattern matching")
                                    break
                                except:
                                    continue
                        
                        # Strategy 3: Extract score directly
                        if 'validation' not in locals():
                            number_match = re.search(r'\b(\d{1,3})\b', json_text)
                            if number_match:
                                relevance_score = min(100, max(0, int(number_match.group(1))))
                                validation = {
                                    "status": "PASSED" if relevance_score > 60 else "FAILED",
                                    "relevance_score": relevance_score,
                                    "comments": f"Content relevance to {subject}: {relevance_score}%"
                                }
                                logger.info(f"Extracted relevance score directly: {relevance_score}")
                            else:
                                # Strategy 4: Use subject count based evaluation
                                subject_count = text_lower.count(subject_lower)
                                keywords_found = [word for word in subject_lower.split() if word in text_lower and len(word) > 3]
                                is_relevant = (subject_count > 2 or len(keywords_found) >= 2) and (subject_lower in text_lower[:500])
                                
                                logger.info(f"Using keyword analysis: found subject {subject_count} times, keywords: {keywords_found}")
                                validation = {
                                    "status": "PASSED" if is_relevant else "FAILED",
                                    "relevance_score": 70 if is_relevant else 30,
                                    "comments": f"Content appears {'relevant' if is_relevant else 'not very relevant'} to {subject}. {'Found multiple direct mentions of the subject.' if subject_count > 2 else 'Found few mentions of the subject.'}"
                                }
                    
                    # Ensure all required fields are present
                    if "relevance_score" not in validation:
                        validation["relevance_score"] = 60 if subject_lower in text_lower else 0
                    if "status" not in validation:
                        validation["status"] = "PASSED" if validation["relevance_score"] > 60 else "FAILED"
                    if "comments" not in validation:
                        validation["comments"] = f"The content's relevance to {subject} is {validation['relevance_score']}%"
                        
                    logger.info(f"LLM relevance assessment: {validation['relevance_score']}% for subject '{subject}'")
                    return validation
                except Exception as parsing_error:
                    logger.error(f"Failed to parse LLM response: {parsing_error}")
                    # Fall back to rule-based relevance detection
                    is_relevant = subject_lower in text_lower
                    score = 60 if is_relevant else 20
                    return {
                        "status": "PASSED" if is_relevant else "FAILED",
                        "relevance_score": score,
                        "comments": f"Fallback assessment: Content appears to be {'relevant' if is_relevant else 'not relevant'} to {subject}."
                    }
            except Exception as e:
                logger.error(f"Error using LLM for validation: {e}")
                # Fall back to rule-based relevance detection
                is_relevant = subject_lower in text_lower
                score = 60 if is_relevant else 20
                return {
                    "status": "PASSED" if is_relevant else "FAILED",
                    "relevance_score": score,
                    "comments": f"Fallback assessment: Content appears to be {'relevant' if is_relevant else 'not relevant'} to {subject}."
                }
        
        # If no LLM available, use a simple rule-based approach
        logger.warning("No LLM available - using rule-based relevance detection")
        is_relevant = subject_lower in text_lower
        score = 60 if is_relevant else 20
        return {
            "status": "PASSED" if is_relevant else "FAILED",
            "relevance_score": score,
            "comments": f"Rule-based assessment: Content appears to be {'relevant' if is_relevant else 'not relevant'} to {subject}."
        }
    
    def validate_content_semantic(self, text, subject, reference_sources=None):
        """
        Legacy method maintained for backward compatibility.
        
        This function now simply forwards to validate_content which handles both
        quick pattern-based checks and LLM-based semantic validation in one method.
        Projects using the old API will continue to work without changes.
        """
        logger.info("validate_content_semantic called (forwarding to unified validate_content)")
        return self.validate_content(text, subject, reference_sources)
    
    
    def _detect_emojis(self, text):
        """Detect emojis in text and return a list of emojis found"""
        # Function to check if a character is an emoji
        def is_emoji(char):
            return unicodedata.category(char) == 'So' or char in '🤔😀😃😄😁😆😅🤣😂🙂🙃😉😊😇🥰😍🤩😘😗😚😙🥲😋😛😜🤪😝🤑🤗🤭🤫🤔🤐🤨😐😑😶😏😒🙄😬🤥😌😔😪🤤😴😷🤒🤕🤢🤮🤧🥵🥶🥴😵🤯'
        
        emojis_found = []
        # Find all individual emojis
        for char in text:
            if is_emoji(char):
                emojis_found.append(char)
                
        # Also check for common emoji patterns with colons
        emoji_pattern = re.compile(r':[a-zA-Z0-9_]+:')
        emojis_found.extend(emoji_pattern.findall(text))
        
        return emojis_found
        
    def _detect_ai_patterns(self, text):
        """
        Detect common patterns found in AI-generated text
        Returns a dictionary with detected patterns and examples
        """
        text_lower = text.lower()
        patterns_found = {
            "detected": False,
            "patterns": [],
            "examples": []
        }
        
        # Common AI-generated text patterns
        ai_patterns = [
            # Self-references and disclaimers
            (r'\b(as an ai|as an assistant|as a language model|i\'m an ai|i am an ai)\b', 'AI self-reference'),
            (r'\bi (cannot|can\'t) (access|browse|view|search) the (internet|web)', 'Internet limitation disclaimer'),
            (r'\bi don\'t have (personal|subjective|political|religious) (opinions|views|beliefs)\b', 'Opinion disclaimer'),
            
            # Formulaic structures common in AI responses
            (r'\b(pros and cons|advantages and disadvantages)\b', 'Pros/cons structure'),
            (r'\b(firstly|secondly|thirdly|finally)[,:]', 'Numbered points structure'),
            (r'\bin conclusion|to summarize|to sum up', 'Formulaic conclusion'),
            
            # Repetitive or overly-balanced phrases
            (r'on one hand.*on the other hand', 'Balanced perspective phrasing'),
            (r'it\'s important to note that|it\'s worth mentioning that', 'Importance qualifier'),
            
            # Overly academic or formal tone compared to subject
            (r'\b(utilizing|aforementioned|nevertheless|notwithstanding|furthermore)\b', 'Overly formal language'),
            
            # Hedging language
            (r'\b(may|might|could) (suggest|indicate|imply)\b', 'Excessive hedging'),
            
            # Awkward repetition or phrasing
            (r'(?:[A-Za-z]{4,}) (?:the same|this) (?:[A-Za-z]{4,}) multiple times', 'Awkward repetition')
        ]
        
        # Check for each pattern
        for pattern, description in ai_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                patterns_found["detected"] = True
                if description not in patterns_found["patterns"]:
                    patterns_found["patterns"].append(description)
                
                # Get some context around the match for an example
                for match in matches[:2]:  # Limit to first 2 matches per pattern
                    # Find the match in the original text to get context
                    match_pos = text_lower.find(match if isinstance(match, str) else match[0])
                    if match_pos >= 0:
                        start_pos = max(0, match_pos - 20)
                        end_pos = min(len(text), match_pos + len(match if isinstance(match, str) else match[0]) + 20)
                        context = text[start_pos:end_pos].replace('\n', ' ').strip()
                        patterns_found["examples"].append({
                            "pattern": description,
                            "text": context
                        })
                        
                        # Stop after collecting a few examples to avoid overwhelming results
                        if len(patterns_found["examples"]) >= 5:
                            break
        
        # Check for paragraph structure patterns common in AI text
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) >= 5:
            # Check for very uniform paragraph lengths (a common AI pattern)
            lengths = [len(p) for p in paragraphs]
            avg_length = sum(lengths) / len(lengths)
            
            uniform_count = 0
            for length in lengths:
                # If paragraph is within 20% of average length, consider it uniform
                if abs(length - avg_length) / avg_length < 0.2:
                    uniform_count += 1
            
            # If more than 70% of paragraphs have similar length, flag it
            if uniform_count / len(paragraphs) > 0.7:
                patterns_found["detected"] = True
                patterns_found["patterns"].append("Uniform paragraph structure")
        
        return patterns_found
# Create a simple prompt tester for direct model interaction
def test_phi2_model(model_path, prompt, max_tokens=500, temperature=0.7):
    """Simple function to test the Phi-2 model with a prompt"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
        
    # Check file size to ensure it's a real model
    file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
    if file_size_mb < 500:  # Less than 500MB is suspicious for a real model
        raise ValueError(f"Model file is too small ({file_size_mb:.1f} MB). Expected a multi-GB file.")
    
    print(f"Loading Phi-2 model from {model_path} ({file_size_mb:.1f} MB)")
    
    try:
        from llama_cpp import Llama
        
        # Load the model with appropriate parameters
        model = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_gpu_layers=-1,  # Auto-detect GPU layers
            n_batch=512,
            verbose=True
        )
        
        print("\nGenerating response...\n")
        print(f"Prompt: {prompt}\n")
        print("-" * 50)
        
        # Call the model to generate a response
        response = model(
            prompt, 
            max_tokens=max_tokens, 
            temperature=temperature,
            echo=True  # Include prompt in the output
        )
        
        return response
    except ImportError as e:
        print(f"Failed to import llama_cpp: {e}")
        print("Please ensure the llama-cpp-python package is installed with: pip install llama-cpp-python")
        raise
    except Exception as e:
        print(f"Error using model: {e}")
        print(f"Details: {e}")
        raise

# Example usage
if __name__ == "__main__":
    # Use the locally available Phi-2 model instead of the default path
    model_path = "/home/rick/projects/llama-sandbox-clean/phi-2.Q4_K_M.gguf"
    
    # Choose one of the two test modes:
    test_mode = "both"  # Options: "validate", "direct", "plagiarism", "both"
    
    if test_mode in ["validate", "both"]:
        # Test the content validation
        print("\n===== Testing Content Validation =====")
        llm = SandboxedLLM(model_path)
        sample_text = "Neural networks are computational models inspired by the human brain. They consist of layers of interconnected nodes or 'neurons' that can learn patterns from data."
        validation = llm.validate_content(sample_text, "Machine Learning")
        print(json.dumps(validation, indent=2))
        
    if test_mode in ["plagiarism", "both"]:
        # Test plagiarism detection
        print("\n===== Testing Plagiarism Detection =====")
        llm = SandboxedLLM(model_path)
        content = """
        Neural networks are computational models inspired by the human brain. They consist of layers of interconnected nodes or 'neurons' that can learn patterns from data. These networks form the backbone of modern machine learning approaches, particularly deep learning.
        """
        
        reference = [{
            "url": "https://example.com/reference",
            "title": "Neural Networks Overview",
            "content": """Neural networks, a cornerstone of artificial intelligence, are designed to mimic the human brain's structure and function. 
            At their core, they comprise interconnected nodes (neurons) organized in layers that process and transform data. 
            Through training on examples, these networks can identify patterns and relationships in complex data."""
        }]
        
        result = llm.check_plagiarism(content, reference)
        print(json.dumps(result, indent=2))
    
    if test_mode in ["direct", "both"]:
        # Direct model testing with a custom prompt
        print("\n===== Testing Direct Model Interaction =====")
        prompt = """
You are Phi-2, a helpful and harmless language model. Please answer the following question:

What are the main applications of large language models in academic research?
Provide a concise but comprehensive answer covering at least 3 key areas.
"""
        result = test_phi2_model(model_path, prompt, max_tokens=500, temperature=0.7)
        print(result["choices"][0]["text"])
