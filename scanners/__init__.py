#!/usr/bin/env python3
from .base import BaseScanner
from .gitleaks import GitLeaksScanner
from .codeql import CodeQLScanner

# Dictionary of available scanners
AVAILABLE_SCANNERS = {
    "gitleaks": GitLeaksScanner,
    "codeql": CodeQLScanner
}

def get_scanner(scanner_name, **kwargs):
    """
    Factory function to get a scanner instance
    
    Args:
        scanner_name (str): Name of the scanner
        **kwargs: Additional arguments to pass to the scanner constructor
        
    Returns:
        BaseScanner: Instance of the requested scanner or None if not found
    """
    scanner_class = AVAILABLE_SCANNERS.get(scanner_name.lower())
    if scanner_class:
        return scanner_class(**kwargs)
    return None

def list_available_scanners():
    """
    Get a list of available scanners
    
    Returns:
        list: List of available scanner names
    """
    return list(AVAILABLE_SCANNERS.keys())
