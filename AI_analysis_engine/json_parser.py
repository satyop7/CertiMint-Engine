#!/usr/bin/env python3
"""
JSON Parser module for handling LLM outputs

This module provides robust JSON parsing utilities for handling potentially
malformed JSON outputs from LLMs.
"""
import re
import json
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger('json_parser')

def extract_and_clean_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and clean JSON from text containing potential JSON objects
    
    Handles common issues in LLM-generated JSON:
    - Unquoted keys
    - Single-quoted strings
    - Trailing commas
    - Extra text before/after JSON
    
    Args:
        text: Raw text potentially containing a JSON object
        
    Returns:
        Parsed JSON as dict if successful, None otherwise
    """
    if not text or text.strip() == "":
        logger.warning("Empty text provided to JSON parser")
        return None
        
    # Log the raw text for debugging (truncated to avoid massive logs)
    logger.debug(f"Raw text to parse ({len(text)} chars): {text[:200]}...")
    
    # Strategy 1: Find JSON-like structure between curly braces
    json_start = text.find("{")
    json_end = text.rfind("}")
    
    if json_start < 0 or json_end <= json_start:
        logger.warning("No JSON-like structure found (no matching braces)")
        return None
    
    # Extract and clean JSON-like text
    json_text = text[json_start:json_end+1]
    json_text = json_text.strip()
    
    logger.debug(f"Extracted JSON candidate ({len(json_text)} chars): {json_text[:200]}...")
    
    # Apply progressive fixes and try to parse at each step
    for step, fixer in enumerate(get_json_fixers(), 1):
        fixed_text = fixer(json_text)
        try:
            result = json.loads(fixed_text)
            logger.debug(f"Successfully parsed JSON at step {step}")
            return result
        except json.JSONDecodeError:
            # Continue to next fixer if this one didn't work
            pass
    
    # If progressive fixes failed, try regex extraction
    try:
        # Match patterns that look like JSON objects
        json_pattern = r'{(?:[^{}]|"[^"]*")*}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            # Apply all fixers to each match
            for fixer in get_json_fixers():
                cleaned = fixer(match)
                try:
                    result = json.loads(cleaned)
                    logger.debug("Successfully parsed JSON using pattern matching")
                    return result
                except:
                    continue
    except Exception as e:
        logger.error(f"Error in regex extraction: {e}")
    
    logger.error("All JSON parsing attempts failed")
    return None

def get_json_fixers():
    """Return a sequence of JSON fixing functions to try"""
    return [
        # Basic cleanup
        lambda x: x.replace('\\n', ' ').replace('\\t', ' '),
        
        # Fix unquoted keys: {key: value} → {"key": value}
        lambda x: re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', x),
        
        # Fix single-quoted strings: {'key': 'value'} → {"key": "value"}
        lambda x: re.sub(r':\s*\'([^\']+)\'', r':"\1"', x).replace("'", '"'),
        
        # Fix trailing commas: {"key": value,} → {"key": value}
        lambda x: re.sub(r',\s*}', '}', x),
        
        # Fix missing quotes around string values:  {"key": value} → {"key": "value"} 
        lambda x: re.sub(r':\s*([a-zA-Z][a-zA-Z0-9_\s]+)([,}])', r':"\1"\2', x),
        
        # Comprehensive fixer that combines all of the above
        lambda x: comprehensive_json_fixer(x)
    ]

def comprehensive_json_fixer(json_text: str) -> str:
    """Apply all fixes to the JSON text in the right order"""
    # Clean whitespace and escapes
    result = json_text.replace('\\n', ' ').replace('\\t', ' ')
    
    # Fix unquoted keys
    result = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', result)
    
    # Fix single quotes
    result = re.sub(r':\s*\'([^\']+)\'', r':"\1"', result)
    result = result.replace("'", '"')
    
    # Fix trailing commas
    result = re.sub(r',\s*}', '}', result)
    result = re.sub(r',\s*]', ']', result)
    
    # Fix unquoted string values (but not true/false/null/numbers)
    def fix_unquoted(match):
        value = match.group(1).strip()
        if value.lower() in ['true', 'false', 'null'] or re.match(r'^-?\d+(\.\d+)?$', value):
            return f': {value}{match.group(2)}'  # Leave true/false/null/numbers unquoted
        else:
            return f': "{value}"{match.group(2)}'  # Quote strings
    
    result = re.sub(r':\s*([a-zA-Z][a-zA-Z0-9_\s]+)([,}])', fix_unquoted, result)
    
    return result

def extract_number_from_text(text: str, default: float = 0.0) -> float:
    """
    Extract a numeric value from text, useful for getting scores when JSON parsing fails
    
    Args:
        text: Text to search for numbers
        default: Default value to return if no number is found
        
    Returns:
        Extracted number or default
    """
    if not text:
        return default
        
    # Look for percentages first
    pct_match = re.search(r'(\d+(?:\.\d+)?)%', text)
    if pct_match:
        try:
            return float(pct_match.group(1))
        except:
            pass
    
    # Look for any number
    num_match = re.search(r'(\d+(?:\.\d+)?)', text)
    if num_match:
        try:
            return float(num_match.group(1))
        except:
            pass
            
    return default

# Example usage
if __name__ == "__main__":
    test_cases = [
        '{"key": "value"}',
        'Some text before {"key": "value"} and after',
        'Result: {key: "value"}',
        '{key: value, status: "success"}',
        '{key: "value", list: [1, 2, 3], "quoted": "text", trailing: 100,}',
        "{'single': 'quotes', list: [1, 2, 3]}"
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\nTest {i+1}: {test}")
        result = extract_and_clean_json(test)
        print(f"Result: {result}")
