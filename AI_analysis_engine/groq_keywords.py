"""
Generate keywords using Groq API based on subject name
"""
import os
import json
import logging
import requests

logger = logging.getLogger('groq_keywords')

def generate_keywords_from_subject(subject, count=8):
    """Generate keywords for a subject using Groq API"""
    try:
        # Get API key from environment or use a default for testing
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            logger.warning("No Groq API key found, using fallback keywords")
            return get_fallback_keywords(subject)
            
        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Create prompt for keyword generation
        prompt = f"""Generate exactly {count} important keywords related to the academic subject: "{subject}".
        Return ONLY a JSON array of strings with no explanation or other text.
        Example: ["keyword1", "keyword2", "keyword3"]"""
        
        # Make the API request
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 200
            }
        )
        
        # Parse the response
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            # Extract JSON array from response
            try:
                # Find the JSON array in the response
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    keywords = json.loads(json_str)
                    if isinstance(keywords, list) and len(keywords) > 0:
                        return keywords[:count]  # Ensure we have exactly the requested count
                
                # If we couldn't parse properly, use fallback
                logger.warning(f"Failed to parse Groq response: {content}")
                return get_fallback_keywords(subject)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in Groq response: {content}")
                return get_fallback_keywords(subject)
        else:
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            return get_fallback_keywords(subject)
            
    except Exception as e:
        logger.error(f"Error generating keywords: {e}")
        return get_fallback_keywords(subject)

def get_fallback_keywords(subject):
    """Generate fallback keywords based on subject name"""
    # Simple fallback: use the subject words and some generic academic terms
    words = subject.lower().split()
    keywords = [w for w in words if len(w) > 3]
    
    # Add some generic academic terms
    generic_terms = ["theory", "concept", "analysis", "research", 
                    "methodology", "framework", "application", "study",
                    "development", "principles", "fundamentals", "practice"]
    
    # Combine subject words with generic terms
    while len(keywords) < 8:
        if generic_terms:
            keywords.append(generic_terms.pop(0))
        else:
            # If we run out of generic terms, duplicate existing keywords
            keywords.append(keywords[0] if keywords else "topic")
    
    return keywords[:8]  # Return exactly 8 keywords

if __name__ == "__main__":
    # Test the function
    test_subject = "Computer Science"
    keywords = generate_keywords_from_subject(test_subject)
    print(f"Keywords for '{test_subject}': {keywords}")