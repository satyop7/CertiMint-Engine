"""
Sandboxed Embedding LLM for offline processing
"""
import logging
from embedding_llm import EmbeddingLLM

logger = logging.getLogger('llm_sandbox')

class SandboxedLLM:
    def __init__(self, model_path=None):
        """Initialize SandboxedLLM with embedding models"""
        logger.info("Initializing sandboxed embedding models")
        try:
            self.embedding_llm = EmbeddingLLM()
            self.model_loaded = True
            logger.info("✓ Embedding models loaded in sandbox mode")
        except Exception as e:
            logger.error(f"Embedding model loading failed: {e}")
            self.embedding_llm = None
            self.model_loaded = False
    

    
    def check_plagiarism(self, text, references):
        """Check plagiarism using embedding models"""
        if self.model_loaded and self.embedding_llm:
            logger.info("Running plagiarism analysis with embedding models")
            return self.embedding_llm.check_plagiarism(text, references)
        
        # Fallback implementation
        logger.warning("Embedding models not available, using fallback")
        return {
            "plagiarism_detected": False,
            "plagiarism_percentage": 25,
            "ai_confidence": 20,
            "top_features_score": 25,
            "llm_similarity": 25,
            "subject_mismatch": False,
            "model_optimization": "fallback mode"
        }
    
    def validate_content(self, text, subject, references):
        """Validate content relevance using embedding models"""
        if self.model_loaded and self.embedding_llm:
            logger.info("Running content validation with embedding models")
            return self.embedding_llm.validate_content(text, subject, references)
        
        # Fallback implementation
        logger.warning("Embedding models not available, using fallback")
        return {
            "status": "FAILED",
            "relevance_score": 30,
            "comments": f"Fallback mode: Cannot validate relevance to {subject}",
            "model_optimization": "fallback mode"
        }
    
    def validate_content_semantic(self, text, subject, references):
        """Semantic validation using embedding models"""
        return self.validate_content(text, subject, references)