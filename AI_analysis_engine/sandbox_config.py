"""
Sandbox configuration for offline mode
"""
import os

def configure_offline_sandbox():
    """Configure environment for offline sandbox mode"""
    # Set environment variables for offline mode
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1" 
    os.environ["LANGCHAIN_TRACING"] = "false"
    os.environ["SANDBOX_MODE"] = "true"
    
    print("Sandbox configured for offline mode:")
    print("- TRANSFORMERS_OFFLINE = 1")
    print("- HF_HUB_OFFLINE = 1")
    print("- LANGCHAIN_TRACING = false")
    print("- SANDBOX_MODE = true")

def verify_offline_mode():
    """Verify that offline mode is properly configured"""
    offline_vars = [
        ("TRANSFORMERS_OFFLINE", "1"),
        ("HF_HUB_OFFLINE", "1"),
        ("LANGCHAIN_TRACING", "false"),
        ("SANDBOX_MODE", "true")
    ]
    
    all_configured = True
    for var, expected in offline_vars:
        actual = os.environ.get(var)
        if actual != expected:
            print(f"Warning: {var} = {actual}, expected {expected}")
            all_configured = False
    
    if all_configured:
        print("✓ Offline sandbox mode properly configured")
    
    return all_configured