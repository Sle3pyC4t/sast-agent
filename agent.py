#!/usr/bin/env python3
import os
import sys
import time
import json
import uuid
import yaml
import logging
import requests
from datetime import datetime

# Import from local modules
from utils.logging_config import setup_logging, get_logger
from utils.repository import Repository
from scanners import get_scanner, list_available_scanners

# Setup logging
logger = setup_logging()

class SastAgent:
    def __init__(self, console_url, agent_name=None, default_timeout=3600, scanner_paths=None):
        """
        Initialize the SAST agent
        
        Args:
            console_url (str): URL of the SAST console
            agent_name (str): Name of the agent (default: auto-generated)
            default_timeout (int): Default timeout for operations in seconds
            scanner_paths (dict): Paths to scanner executables (e.g. {"codeql": "/path/to/codeql"})
        """
        self.console_url = console_url.rstrip('/')
        self.agent_id = str(uuid.uuid4())
        self.agent_name = agent_name or f"agent-{self.agent_id[:8]}"
        self.registered = False
        self.status = "idle"
        self.capabilities = list_available_scanners()
        self.current_task = None
        self.default_timeout = default_timeout
        self.scanner_paths = scanner_paths or {}
        self.repository = Repository(clone_timeout=300)
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
        
        # Try to load existing config if available
        self.load_config()
        
    def load_config(self):
        """Load configuration from file if it exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self.agent_id = config.get('agent_id', self.agent_id)
                self.agent_name = config.get('agent_name', self.agent_name)
                self.registered = config.get('registered', False)
                self.default_timeout = config.get('default_timeout', self.default_timeout)
                self.scanner_paths = config.get('scanner_paths', self.scanner_paths)
                logger.info(f"Loaded configuration for agent {self.agent_name}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
    def save_config(self):
        """Save configuration to file"""
        config = {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'registered': self.registered,
            'console_url': self.console_url,
            'default_timeout': self.default_timeout,
            'scanner_paths': self.scanner_paths
        }
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f)
            logger.info(f"Saved configuration for agent {self.agent_name}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
        
    def register(self):
        """
        Register the agent with the console
        
        Returns:
            bool: True if registration was successful, False otherwise
        """
        if self.registered:
            logger.info(f"Agent {self.agent_name} already registered")
            return True
        
        registration_data = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "capabilities": self.capabilities,
            "status": self.status,
            "system_info": self.get_system_info()
        }
        
        try:
            # 添加时间戳参数以防止缓存
            timestamp = int(time.time())
            response = requests.post(
                f"{self.console_url}/api/agents/register?t={timestamp}",
                json=registration_data,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                # 检查响应内容而不仅仅是状态码
                response_data = response.json()
                if response_data.get('success'):
                    self.registered = True
                    logger.info(f"Successfully registered agent {self.agent_name}")
                    self.save_config()
                    return True
                else:
                    logger.error(f"Failed to register agent. Response: {response.text}")
                    return False
            else:
                logger.error(f"Failed to register agent. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return False
            
    def get_system_info(self):
        """
        Get basic system information
        
        Returns:
            dict: System information
        """
        import platform
        return {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "hostname": platform.node(),
            "scanners": self.capabilities
        }
        
    def heartbeat(self):
        """
        Send heartbeat to console to indicate agent is alive
        
        Returns:
            bool: True if heartbeat was successful, False otherwise
        """
        if not self.registered:
            logger.warning("Agent not registered. Cannot send heartbeat.")
            return False
            
        heartbeat_data = {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_task": self.current_task,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 添加时间戳参数以防止缓存
            timestamp = int(time.time())
            response = requests.post(
                f"{self.console_url}/api/agents/{self.agent_id}/heartbeat?t={timestamp}",
                json=heartbeat_data,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success'):
                    logger.debug(f"Heartbeat sent successfully")
                    return True
                else:
                    logger.warning(f"Failed to send heartbeat. Response: {response.text}")
                    return False
            else:
                logger.warning(f"Failed to send heartbeat. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
    def poll_for_tasks(self):
        """
        Poll the console for new tasks
        
        Returns:
            dict: Task data or None if no tasks are available
        """
        if not self.registered:
            logger.warning("Agent not registered. Cannot poll for tasks.")
            return None
            
        if self.status != "idle":
            logger.debug(f"Agent is {self.status}. Skipping task poll.")
            return None
            
        try:
            response = requests.get(
                f"{self.console_url}/api/agents/{self.agent_id}/tasks",
                params={"status": "pending"},
                timeout=10
            )
            
            if response.status_code == 200:
                tasks = response.json().get("tasks", [])
                if tasks:
                    return tasks[0]  # Return the first pending task
                else:
                    logger.debug("No pending tasks found")
                    return None
            else:
                logger.warning(f"Failed to poll for tasks. Status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error polling for tasks: {e}")
            return None
    
    def execute_task(self, task):
        """
        Execute a scanning task
        
        Args:
            task (dict): Task data
            
        Returns:
            dict: Task results
        """
        self.status = "scanning"
        
        # 为向后兼容性处理id/task_id字段
        task_id = task.get("task_id", task.get("id"))
        if not task_id:
            logger.error("Task missing required ID field")
            self.status = "idle"
            self.current_task = None
            return {"error": "Task missing required ID field"}
            
        self.current_task = task_id
        
        # Update task status to running
        self.update_task_status(task_id, "running")
        
        results = {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "start_time": datetime.now().isoformat(),
            "status": "failed",
            "scan_results": {},
            "error": None
        }
        
        repo_path = None
        try:
            # Clone the repository
            repo_url = task.get("repository_url")
            if not repo_url:
                raise ValueError("Repository URL is required")
                
            branch = task.get("branch")
            depth = task.get("depth", 1)  # Default to shallow clone
            repo_path = self.repository.clone(repo_url, branch, depth)
            
            if not repo_path:
                raise ValueError("Failed to clone repository")
                
            # Run requested scanners
            scanners = task.get("scanners", self.capabilities)
            scan_results = {}
            
            # Common scanner options
            scan_timeout = task.get("timeout", self.default_timeout)
            logger.info(f"Task timeout set to {scan_timeout} seconds")
            
            # Run each requested scanner
            for scanner_name in scanners:
                if scanner_name in self.capabilities:
                    logger.info(f"Running {scanner_name} scanner")
                    
                    # Get scanner path if configured
                    scanner_path = self.scanner_paths.get(scanner_name)
                    if scanner_path:
                        logger.info(f"Using custom path for {scanner_name}: {scanner_path}")
                        
                        # 对每个扫描器使用正确的参数名称
                        if scanner_name == 'codeql':
                            scanner = get_scanner(scanner_name, codeql_path=scanner_path)
                        elif scanner_name == 'gitleaks':
                            scanner = get_scanner(scanner_name, gitleaks_path=scanner_path)
                        else:
                            # 默认使用扫描器名称作为参数名前缀
                            scanner = get_scanner(scanner_name, **{f"{scanner_name}_path": scanner_path})
                    else:
                        scanner = get_scanner(scanner_name)
                    
                    if scanner:
                        # Get scanner-specific options from task
                        scanner_options = task.get(f"{scanner_name}_options", {})
                        
                        # Run scan with timeout
                        scan_results[scanner_name] = scanner.scan(
                            repo_path, 
                            options=scanner_options,
                            timeout=scan_timeout
                        )
                    else:
                        logger.warning(f"Scanner '{scanner_name}' not available")
                        scan_results[scanner_name] = {
                            "success": False,
                            "error": f"Scanner '{scanner_name}' not available"
                        }
                else:
                    logger.warning(f"Scanner '{scanner_name}' not supported by this agent")
            
            # Update results
            if any(result.get("success", False) for result in scan_results.values()):
                results["status"] = "completed"
            else:
                results["status"] = "failed"
                results["error"] = "All scans failed"
                
            results["end_time"] = datetime.now().isoformat()
            results["scan_results"] = scan_results
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            results["end_time"] = datetime.now().isoformat()
            
        finally:
            # Clean up repository
            if repo_path:
                self.repository.cleanup(repo_path)
                
            # Send results back to console
            self.send_task_results(results)
            
            # Reset agent status
            self.status = "idle"
            self.current_task = None
            
            return results
            
    def update_task_status(self, task_id, status):
        """
        Update task status in the console
        
        Args:
            task_id (str): Task ID
            status (str): New status
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # 添加时间戳以防止缓存
            timestamp = int(time.time())
            response = requests.patch(
                f"{self.console_url}/api/tasks/{task_id}?t={timestamp}",
                json={"status": status},
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Task {task_id} status updated to {status}")
                return True
            else:
                logger.warning(f"Failed to update task status. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False
            
    def send_task_results(self, results):
        """
        Send task results back to the console
        
        Args:
            results (dict): Task results
            
        Returns:
            bool: True if send was successful, False otherwise
        """
        try:
            # 添加时间戳以防止缓存
            timestamp = int(time.time())
            response = requests.post(
                f"{self.console_url}/api/tasks/{results['task_id']}/results?t={timestamp}",
                json=results,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Task results sent successfully")
                return True
            else:
                logger.warning(f"Failed to send task results. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending task results: {e}")
            return False
            
    def run(self):
        """Main agent loop"""
        logger.info(f"Starting SAST agent {self.agent_name}")
        
        if not self.registered:
            if not self.register():
                logger.error("Failed to register agent. Exiting.")
                return
                
        logger.info(f"Agent registered with ID {self.agent_id}")
        logger.info(f"Agent capabilities: {', '.join(self.capabilities)}")
        
        try:
            heartbeat_interval = 30  # seconds
            last_heartbeat = 0
            
            while True:
                # Send heartbeat at regular intervals
                current_time = time.time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.heartbeat()
                    last_heartbeat = current_time
                
                # Poll for tasks when idle
                if self.status == "idle":
                    task = self.poll_for_tasks()
                    if task:
                        # 确保task_id字段存在
                        if 'id' in task and 'task_id' not in task:
                            task['task_id'] = task['id']
                            
                        logger.info(f"Received task {task.get('task_id', task.get('id', 'unknown'))}")
                        self.execute_task(task)
                
                # Sleep to avoid hammering the server
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Agent interrupted. Shutting down.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
        finally:
            # Clean up any resources
            self.repository.cleanup()
            
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SAST Agent")
    parser.add_argument("--console", default="https://sast-console.vercel.app", help="Console URL")
    parser.add_argument("--name", help="Agent name")
    parser.add_argument("--timeout", type=int, default=3600, help="Default operation timeout in seconds")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level")
    parser.add_argument("--codeql-path", help="Path to CodeQL executable")
    parser.add_argument("--gitleaks-path", help="Path to GitLeaks executable")
    args = parser.parse_args()
    
    # Set log level
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level=log_level)
    
    # Prepare scanner paths
    scanner_paths = {}
    if args.codeql_path:
        scanner_paths['codeql'] = args.codeql_path
    if args.gitleaks_path:
        scanner_paths['gitleaks'] = args.gitleaks_path
    
    # Create and run agent
    agent = SastAgent(args.console, args.name, args.timeout, scanner_paths)
    agent.run()

if __name__ == "__main__":
    main() 