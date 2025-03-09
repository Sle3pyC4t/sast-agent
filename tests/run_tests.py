#!/usr/bin/env python3
"""
Master script to run all SAST Console API tests.
This script will run the functional tests and load tests in sequence,
and provide a summary of the results.
"""

import os
import sys
import time
import subprocess
import argparse
import logging
from datetime import datetime

# 获取当前脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "all_tests.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_test(test_script, args=None):
    """Run a test script and return the result."""
    start_time = time.time()
    cmd = [sys.executable, test_script]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running {test_script} with args: {args if args else 'none'}")
    
    try:
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        success = result.returncode == 0
        duration = time.time() - start_time
        
        status = "SUCCESS" if success else "FAILURE"
        logger.info(f"{test_script} completed with status: {status} in {duration:.2f} seconds")
        
        # Log stdout and stderr if there was a failure or in verbose mode
        if not success or args and "--verbose" in args:
            if result.stdout:
                logger.info(f"STDOUT from {test_script}:\n{result.stdout}")
            if result.stderr:
                logger.error(f"STDERR from {test_script}:\n{result.stderr}")
        
        return {
            "script": test_script,
            "success": success,
            "duration": duration,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        logger.error(f"Error running {test_script}: {str(e)}")
        return {
            "script": test_script,
            "success": False,
            "duration": time.time() - start_time,
            "error": str(e)
        }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run all SAST Console API tests')
    parser.add_argument('--functional-only', action='store_true',
                        help='Run only functional tests')
    parser.add_argument('--load-only', action='store_true',
                        help='Run only load tests')
    parser.add_argument('--frontend-only', action='store_true',
                        help='Run only frontend data validation tests')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--load-agents', type=int, default=5,
                        help='Number of agents for load test (default: 5)')
    parser.add_argument('--load-tasks', type=int, default=2,
                        help='Tasks per agent for load test (default: 2)')
    parser.add_argument('--load-concurrent', type=int, default=3,
                        help='Concurrent requests for load test (default: 3)')
    parser.add_argument('--negative', action='store_true',
                        help='Run negative tests (testing error conditions)')
    return parser.parse_args()

def main():
    """Run the tests and summarize results."""
    args = parse_args()
    results = []
    
    # Make sure logs directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger.info("=== Starting SAST Console API Test Suite ===")
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Test run started at: {timestamp}")
    
    # Run basic functional tests
    if not args.load_only and not args.frontend_only:
        func_args = ["--negative"] if args.negative else None
        if args.verbose:
            func_args = func_args or []
            func_args.append("--verbose")
        
        # 使用当前目录的相对路径
        func_result = run_test(os.path.join(SCRIPT_DIR, "test_console_api.py"), func_args)
        results.append(func_result)
    
    # Run load tests
    if not args.functional_only and not args.frontend_only:
        load_args = []
        if args.load_agents != 5:
            load_args.extend(["--agents", str(args.load_agents)])
        if args.load_tasks != 2:
            load_args.extend(["--tasks-per-agent", str(args.load_tasks)])
        if args.load_concurrent != 3:
            load_args.extend(["--concurrent", str(args.load_concurrent)])
        if args.verbose:
            load_args.append("--verbose")
            
        # 使用当前目录的相对路径
        load_result = run_test(os.path.join(SCRIPT_DIR, "load_test_console_api.py"), load_args or None)
        results.append(load_result)
    
    # Run frontend data validation tests
    if not args.functional_only and not args.load_only:
        verbose_arg = ["--verbose"] if args.verbose else None
        
        # Run dashboard data tests
        dashboard_result = run_test(os.path.join(SCRIPT_DIR, "test_dashboard_data.py"), verbose_arg)
        results.append(dashboard_result)
        
        # Run agents data tests
        agents_result = run_test(os.path.join(SCRIPT_DIR, "test_agents_data.py"), verbose_arg)
        results.append(agents_result)
        
        # Run vulnerability data tests
        vulnerability_result = run_test(os.path.join(SCRIPT_DIR, "test_vulnerability_data.py"), verbose_arg)
        results.append(vulnerability_result)
    
    # Summarize results
    total_duration = time.time() - start_time
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    logger.info("\n=== Test Run Summary ===")
    logger.info(f"Total tests run: {len(results)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Total duration: {total_duration:.2f} seconds")
    logger.info("\n=== Detailed Results ===")
    
    for result in results:
        status = "SUCCESS" if result["success"] else "FAILURE"
        logger.info(f"{result['script']}: {status} ({result['duration']:.2f}s)")
        if not result["success"] and "error" in result:
            logger.error(f"  Error: {result['error']}")
    
    logger.info("=== End of Test Run ===")
    
    # Return exit code based on success/failure
    return 0 if all(r["success"] for r in results) else 1

if __name__ == "__main__":
    sys.exit(main()) 