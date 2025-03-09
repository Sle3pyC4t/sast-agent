#!/usr/bin/env python3
import os
import json
import tempfile
import uuid
from .base import BaseScanner

class GitLeaksScanner(BaseScanner):
    """GitLeaks scanner implementation"""
    
    def __init__(self, default_timeout=300):
        """Initialize GitLeaks scanner"""
        super().__init__("gitleaks", default_timeout)
        
    def scan(self, target_dir, options=None, timeout=None):
        """
        Run GitLeaks scan on target directory
        
        Args:
            target_dir (str): Target directory to scan
            options (dict): Additional options for GitLeaks
            timeout (int): Timeout in seconds
            
        Returns:
            dict: Scan results
        """
        if options is None:
            options = {}
            
        # Create temporary file for results
        output_file = os.path.join(tempfile.gettempdir(), f"gitleaks_results_{uuid.uuid4()}.json")
        
        # Build command
        command = ["gitleaks", "detect", "--source", target_dir, "--report-path", output_file, "--report-format", "json"]
        
        # Add additional options
        if options.get("config_path"):
            command.extend(["--config-path", options["config_path"]])
        
        if options.get("redact"):
            command.append("--redact")
            
        # Run scan
        process_result = self.run_process(command, timeout)
        
        # Process results
        if process_result["success"] or process_result.get("exit_code") == 1:  # Exit code 1 means issues found
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        # Parse JSON results
                        gitleaks_results = json.load(f)
                    
                    # Remove temp file
                    os.remove(output_file)
                    
                    return {
                        "success": True,
                        "exit_code": process_result.get("exit_code", 0),
                        "findings": gitleaks_results,
                        "execution_time": process_result.get("execution_time")
                    }
                except Exception as e:
                    self.logger.error(f"Error parsing GitLeaks results: {e}")
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    return {
                        "success": False,
                        "error": f"Error parsing results: {str(e)}",
                        "execution_time": process_result.get("execution_time")
                    }
            else:
                return {
                    "success": False,
                    "error": "GitLeaks output file not found",
                    "stdout": process_result.get("stdout", ""),
                    "stderr": process_result.get("stderr", ""),
                    "execution_time": process_result.get("execution_time")
                }
        else:
            return {
                "success": False,
                "error": process_result.get("error", "GitLeaks scan failed"),
                "stdout": process_result.get("stdout", ""),
                "stderr": process_result.get("stderr", ""),
                "execution_time": process_result.get("execution_time")
            }
