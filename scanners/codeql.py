#!/usr/bin/env python3
import os
import json
import tempfile
import uuid
import shutil
from .base import BaseScanner

class CodeQLScanner(BaseScanner):
    """CodeQL scanner implementation"""
    
    def __init__(self, default_timeout=1800, codeql_path=None):  # Default timeout 30 minutes
        """
        Initialize CodeQL scanner
        
        Args:
            default_timeout (int): Default timeout in seconds
            codeql_path (str): Optional path to codeql executable
        """
        super().__init__("codeql", default_timeout)
        self.codeql_path = codeql_path or "codeql"  # Use provided path or fallback to command name
        self.logger.info(f"Using CodeQL executable: {self.codeql_path}")
        
    def scan(self, target_dir, options=None, timeout=None):
        """
        Run CodeQL scan on target directory
        
        Args:
            target_dir (str): Target directory to scan
            options (dict): Additional options for CodeQL
            timeout (int): Timeout in seconds
            
        Returns:
            dict: Scan results
        """
        if options is None:
            options = {}
            
        # Create temporary directory for CodeQL database and results
        temp_db_dir = tempfile.mkdtemp(prefix="codeql_db_")
        output_file = os.path.join(tempfile.gettempdir(), f"codeql_results_{uuid.uuid4()}.sarif")
        
        try:
            # Determine language if not specified
            language = options.get("language")
            if not language:
                language = self._detect_language(target_dir)
                if not language:
                    return {
                        "success": False,
                        "error": "Failed to detect language for CodeQL analysis"
                    }
            
            # Step 1: Create CodeQL database
            self.logger.info(f"Creating CodeQL database for {language}")
            create_cmd = [
                self.codeql_path, "database", "create", 
                "--language", language,
                "--source-root", target_dir,
                temp_db_dir
            ]
            
            # Add additional database creation options
            if options.get("threads"):
                create_cmd.extend(["--threads", str(options["threads"])])
            
            create_result = self.run_process(create_cmd, timeout)
            if not create_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to create CodeQL database",
                    "stdout": create_result.get("stdout", ""),
                    "stderr": create_result.get("stderr", ""),
                    "execution_time": create_result.get("execution_time")
                }
            
            # Step 2: Analyze the database
            self.logger.info("Analyzing CodeQL database")
            query_suite = options.get("query_suite", f"{language}-security-and-quality")
            
            analyze_cmd = [
                self.codeql_path, "database", "analyze",
                "--format", "sarif-latest",
                "--output", output_file,
                temp_db_dir, query_suite
            ]
            
            analyze_result = self.run_process(analyze_cmd, timeout)
            
            # Process results
            if analyze_result["success"] and os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        # Parse SARIF results
                        sarif_results = json.load(f)
                        
                    total_execution_time = (
                        create_result.get("execution_time", 0) + 
                        analyze_result.get("execution_time", 0)
                    )
                    
                    return {
                        "success": True,
                        "exit_code": analyze_result.get("exit_code", 0),
                        "findings": sarif_results,
                        "execution_time": total_execution_time,
                        "language": language
                    }
                except Exception as e:
                    self.logger.error(f"Error parsing CodeQL results: {e}")
                    return {
                        "success": False,
                        "error": f"Error parsing results: {str(e)}",
                        "execution_time": (
                            create_result.get("execution_time", 0) + 
                            analyze_result.get("execution_time", 0)
                        )
                    }
            else:
                return {
                    "success": False,
                    "error": "CodeQL analysis failed or output file not found",
                    "stdout": analyze_result.get("stdout", ""),
                    "stderr": analyze_result.get("stderr", ""),
                    "execution_time": (
                        create_result.get("execution_time", 0) + 
                        analyze_result.get("execution_time", 0)
                    )
                }
        finally:
            # Clean up
            if os.path.exists(temp_db_dir):
                shutil.rmtree(temp_db_dir, ignore_errors=True)
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def _detect_language(self, target_dir):
        """
        Attempt to detect the primary language for CodeQL analysis
        
        Args:
            target_dir (str): Target directory to analyze
            
        Returns:
            str: Detected language or None if detection fails
        """
        # Simple language detection based on file extensions
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'javascript',  # TypeScript uses JavaScript analysis in CodeQL
            '.java': 'java',
            '.c': 'cpp',
            '.cpp': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rb': 'ruby'
        }
        
        # Count files by language
        lang_count = {}
        
        for root, _, files in os.walk(target_dir):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in extension_map:
                    lang = extension_map[ext]
                    lang_count[lang] = lang_count.get(lang, 0) + 1
        
        # Return the most common language or None if no supported languages found
        if lang_count:
            return max(lang_count.items(), key=lambda x: x[1])[0]
        return None
