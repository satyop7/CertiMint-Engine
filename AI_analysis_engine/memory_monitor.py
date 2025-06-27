#!/usr/bin/env python3
import psutil
import os
import gc
import logging

logger = logging.getLogger(__name__)

def check_memory_usage():
    """Check current memory usage and warn if high"""
    memory = psutil.virtual_memory()
    used_gb = memory.used / (1024**3)
    total_gb = memory.total / (1024**3)
    percent = memory.percent
    
    logger.info(f"Memory usage: {used_gb:.1f}GB / {total_gb:.1f}GB ({percent:.1f}%)")
    
    if percent > 80:
        logger.warning(f"High memory usage detected: {percent:.1f}%")
        return False
    return True

def force_garbage_collection():
    """Force garbage collection to free memory"""
    logger.info("Running garbage collection...")
    collected = gc.collect()
    logger.info(f"Garbage collection freed {collected} objects")

def set_memory_limits():
    """Set memory limits for the process"""
    try:
        import resource
        # Set memory limit to 12GB (leave 4GB for system)
        memory_limit = 12 * 1024 * 1024 * 1024  # 12GB in bytes
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        logger.info("Memory limit set to 12GB")
    except Exception as e:
        logger.warning(f"Could not set memory limit: {e}")

if __name__ == "__main__":
    check_memory_usage()