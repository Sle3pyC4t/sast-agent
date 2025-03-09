#!/usr/bin/env python3
import logging
import subprocess
import time
import json
from abc import ABC, abstractmethod

class BaseScanner(ABC):
    """Base class for all security scanners"""
    
    def __init__(self, name, default_timeout=600):
        """
        Initialize the scanner
        
        Args:
            name (str): Name of the scanner
            default_timeout (int): Default timeout in seconds
        """
        self.name = name
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(f"SAST_Agent.{name}")
        
    @abstractmethod
    def scan(self, target_dir, options=None, timeout=None):
        """
        Abstract method to be implemented by scanners
        
        Args:
            target_dir (str): Target directory to scan
            options (dict): Scanner-specific options
            timeout (int): Timeout in seconds
            
        Returns:
            dict: Scan results
        """
        pass
        
    def run_process(self, command, timeout=None):
        """
        Run a subprocess with timeout
        
        Args:
            command (list): Command to run
            timeout (int): Timeout in seconds (uses default if None)
            
        Returns:
            dict: Process results
        """
        if timeout is None:
            timeout = self.default_timeout
            
        self.logger.info(f"Running command: {' '.join(command)}")
        start_time = time.time()
        
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            self.logger.info(f"Command completed in {execution_time:.2f} seconds with exit code {process.returncode}")
            
            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.error(f"Command timed out after {execution_time:.2f} seconds")
            
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Error running command: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
