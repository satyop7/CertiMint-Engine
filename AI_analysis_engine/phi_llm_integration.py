"""
Phi LLM integration for sandbox processing
"""
import os
import logging

logger = logging.getLogger('phi_llm')

class PhiLLM:
    def __init__(self, model_path="models/phi-2.gguf"):
        self.model_path = model_path
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load Phi model in offline mode"""
        try:
            from llm_loader import load_model
            logger.info(f"Loading Phi model: {self.model_path}")
            self.model, success, error = load_model(self.model_path)
            if success:
                logger.info("Phi model loaded successfully")
            else:
                logger.error(f"Failed to load Phi model: {error}")
        except Exception as e:
            logger.error(f"Error loading Phi model: {e}")
            self.model = None
    
    def check_content_relevance(self, text_300, subject):
        """Use Phi LLM to check content relevance"""
        if not self.model:
            logger.warning("Phi model not available, using fallback")
            return self._fallback_relevance_check(text_300, subject)
        
        try:
            prompt = f"""Analyze if this text is relevant to the subject "{subject}". 
Text: {text_300}

Rate relevance from 0-100 where:
- 0-30: Not relevant
- 31-60: Somewhat relevant  
- 61-100: Highly relevant

Respond with only a number:"""
            
            # Call Phi model
            response = self.model(prompt, max_tokens=5, temperature=0.1)
            result_text = response.get("choices", [{}])[0].get("text", "").strip()
            
            # Extract number from response
            import re
            match = re.search(r'(\d+)', result_text)
            if match:
                score = int(match.group(1))
                score = max(0, min(100, score))  # Clamp to 0-100
                logger.info(f"Phi LLM relevance score: {score}%")
                return score
            else:
                logger.warning("Could not parse Phi LLM response, using fallback")
                return self._fallback_relevance_check(text_300, subject)
                
        except Exception as e:
            logger.error(f"Error calling Phi LLM: {e}")
            return self._fallback_relevance_check(text_300, subject)
    
    def _fallback_relevance_check(self, text, subject):
        """Fallback relevance check when Phi LLM unavailable"""
        text_lower = text.lower()
        subject_lower = subject.lower()
        
        # Check if subject is mentioned
        if subject_lower in text_lower:
            base_score = 60.0
        else:
            base_score = 30.0
        
        # Check for subject-related keywords
        subject_keywords = {
            "physics": ["quantum", "mechanics", "particle", "wave", "energy"],
            "chemistry": ["molecule", "atom", "reaction", "compound", "element"],
            "biology": ["cell", "organism", "evolution", "gene", "dna"],
            "mathematics": ["equation", "function", "theorem", "algebra", "geometry"],
            "computer science": ["algorithm", "data", "programming", "code", "software"]
        }
        
        keywords = subject_keywords.get(subject_lower, [])
        keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)
        keyword_bonus = min(keyword_matches * 8, 40.0)
        
        final_score = min(base_score + keyword_bonus, 100.0)
        return round(final_score, 2)