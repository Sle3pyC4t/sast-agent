#!/usr/bin/env python3
"""
Load testing script for SAST Console API endpoints.
Tests the API's performance under load by simulating multiple concurrent requests.
"""

import requests
import json
import time
import uuid
import sys
import logging
import argparse
import threading
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/load_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Base URL for the SAST Console
BASE_URL = "https://sast-console.vercel.app/api"


class SastConsoleLoadTester:
    """Class to perform load testing on SAST Console API endpoints."""
    
    def __init__(self, num_agents=5, num_tasks_per_agent=2, num_concurrent=3):
        """
        Initialize the load tester.
        
        Args:
            num_agents: Number of agents to create for testing
            num_tasks_per_agent: Number of tasks to create per agent
            num_concurrent: Number of concurrent requests to make
        """
        self.num_agents = num_agents
        self.num_tasks_per_agent = num_tasks_per_agent
        self.num_concurrent = num_concurrent
        self.agents = []
        self.tasks = []
        self.response_times = {
            "register_agent": [],
            "get_agents": [],
            "get_agent": [],
            "update_agent": [],
            "agent_heartbeat": [],
            "create_task": [],
            "get_tasks": [],
            "get_task": [],
            "update_task": [],
            "submit_result": [],
            "get_results": []
        }
        self.session = requests.Session()
        self.lock = threading.Lock()
    
    def run_load_test(self):
        """Run the complete load test."""
        start_time = time.time()
        logger.info(f"=== Starting SAST Console API Load Test ===")
        logger.info(f"Configuration: {self.num_agents} agents, {self.num_tasks_per_agent} tasks per agent, {self.num_concurrent} concurrent requests")
        
        try:
            # Create agents
            self._create_agents()
            
            # Get all agents (test endpoint under load)
            self._test_get_agents_concurrently()
            
            # Get, update and heartbeat for agents concurrently
            self._test_agent_operations_concurrently()
            
            # Create tasks for each agent
            self._create_tasks()
            
            # Get all tasks (test endpoint under load)
            self._test_get_tasks_concurrently()
            
            # Get and update tasks concurrently
            self._test_task_operations_concurrently()
            
            # Submit and get results concurrently
            self._test_results_operations_concurrently()
            
            # Print performance summary
            self._print_performance_summary()
            
            duration = time.time() - start_time
            logger.info(f"=== Load Test Completed in {duration:.2f} seconds ===")
            return True
        except Exception as e:
            logger.error(f"Error during load test: {str(e)}")
            return False
    
    def _create_agents(self):
        """Create the specified number of test agents."""
        logger.info(f"Creating {self.num_agents} test agents...")
        
        with ThreadPoolExecutor(max_workers=self.num_concurrent) as executor:
            futures = []
            for i in range(self.num_agents):
                agent_data = {
                    "agent_id": str(uuid.uuid4()),
                    "agent_name": f"Load Test Agent {i+1}-{str(uuid.uuid4())[:8]}",
                    "status": "available",
                    "capabilities": ["gitleaks", "codeql", "semgrep"],
                    "ip_address": f"192.168.1.{100+i}",
                    "system_info": {
                        "os": "Linux",
                        "version": "Ubuntu 22.04",
                        "cpu_cores": 4,
                        "memory": "8GB"
                    }
                }
                futures.append(executor.submit(self._register_agent, agent_data))
            
            for future in as_completed(futures):
                try:
                    agent = future.result()
                    if agent:
                        with self.lock:
                            self.agents.append(agent)
                except Exception as e:
                    logger.error(f"Error creating agent: {str(e)}")
        
        logger.info(f"Created {len(self.agents)} agents successfully")
    
    def _register_agent(self, agent_data):
        """Register a new agent and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.post(f"{BASE_URL}/agents/register", json=agent_data)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                agent = response.json().get("agent")
                logger.debug(f"Registered agent: {agent['name']} (ID: {agent['id']}) in {duration:.3f}s")
                with self.lock:
                    self.response_times["register_agent"].append(duration)
                return agent
            else:
                logger.error(f"Failed to register agent: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception during agent registration: {str(e)}")
            return None
    
    def _test_get_agents_concurrently(self):
        """Test getting all agents with concurrent requests."""
        logger.info("Testing GET /agents with concurrent requests...")
        
        with ThreadPoolExecutor(max_workers=self.num_concurrent) as executor:
            futures = [executor.submit(self._get_all_agents) for _ in range(self.num_concurrent)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error getting agents: {str(e)}")
    
    def _get_all_agents(self):
        """Get all agents and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BASE_URL}/agents")
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["get_agents"].append(duration)
            
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                logger.debug(f"Got {len(agents)} agents in {duration:.3f}s")
                return agents
            else:
                logger.error(f"Failed to get agents: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception getting agents: {str(e)}")
            return []
    
    def _test_agent_operations_concurrently(self):
        """Test agent operations (get, update, heartbeat) concurrently."""
        if not self.agents:
            logger.warning("No agents to test operations on")
            return
        
        logger.info(f"Testing agent operations concurrently on {len(self.agents)} agents...")
        
        with ThreadPoolExecutor(max_workers=self.num_concurrent) as executor:
            futures = []
            
            # Get agent details
            for agent in self.agents:
                futures.append(executor.submit(self._get_agent, agent["id"]))
            
            # Update agents
            for agent in self.agents:
                update_data = {
                    "status": "busy",
                    "capabilities": ["gitleaks", "codeql", "semgrep", "bandit"],
                    "system_info": {
                        "os": "Linux",
                        "version": "Ubuntu 22.04",
                        "cpu_cores": 8,
                        "memory": "16GB"
                    }
                }
                futures.append(executor.submit(self._update_agent, agent["id"], update_data))
            
            # Send heartbeats
            for agent in self.agents:
                futures.append(executor.submit(self._agent_heartbeat, agent["id"]))
            
            # Wait for all operations to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in agent operation: {str(e)}")
    
    def _get_agent(self, agent_id):
        """Get a specific agent and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BASE_URL}/agents/{agent_id}")
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["get_agent"].append(duration)
            
            if response.status_code == 200:
                agent = response.json().get("agent")
                logger.debug(f"Got agent {agent_id} in {duration:.3f}s")
                return agent
            else:
                logger.error(f"Failed to get agent {agent_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception getting agent {agent_id}: {str(e)}")
            return None
    
    def _update_agent(self, agent_id, update_data):
        """Update an agent and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.patch(f"{BASE_URL}/agents/{agent_id}", json=update_data)
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["update_agent"].append(duration)
            
            if response.status_code == 200:
                agent = response.json().get("agent")
                logger.debug(f"Updated agent {agent_id} in {duration:.3f}s")
                return agent
            else:
                logger.error(f"Failed to update agent {agent_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception updating agent {agent_id}: {str(e)}")
            return None
    
    def _agent_heartbeat(self, agent_id):
        """Send a heartbeat for an agent and record the response time."""
        start_time = time.time()
        
        try:
            # Send heartbeat with status
            heartbeat_data = {
                "status": "online"
            }
            response = self.session.post(f"{BASE_URL}/agents/{agent_id}/heartbeat", json=heartbeat_data)
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["agent_heartbeat"].append(duration)
            
            if response.status_code == 200:
                logger.debug(f"Sent heartbeat for agent {agent_id} in {duration:.3f}s")
                return True
            else:
                logger.error(f"Failed to send heartbeat for agent {agent_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception sending heartbeat for agent {agent_id}: {str(e)}")
            return False
    
    def _create_tasks(self):
        """Create tasks for each agent."""
        if not self.agents:
            logger.warning("No agents to create tasks for")
            return
        
        total_tasks = len(self.agents) * self.num_tasks_per_agent
        logger.info(f"Creating {total_tasks} tasks ({self.num_tasks_per_agent} for each of {len(self.agents)} agents)...")
        
        with ThreadPoolExecutor(max_workers=self.num_concurrent) as executor:
            futures = []
            
            for agent in self.agents:
                for i in range(self.num_tasks_per_agent):
                    task_data = {
                        "agent_id": agent["id"],
                        "repository_url": f"https://github.com/username/repo-{i+1}",
                        "branch": "main",
                        "scanners": ["gitleaks", "codeql"],
                        "created_by": "load-test"
                    }
                    futures.append(executor.submit(self._create_task, task_data))
            
            for future in as_completed(futures):
                try:
                    task = future.result()
                    if task:
                        with self.lock:
                            self.tasks.append(task)
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
        
        logger.info(f"Created {len(self.tasks)} tasks successfully")
    
    def _create_task(self, task_data):
        """Create a task and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.post(f"{BASE_URL}/tasks", json=task_data)
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["create_task"].append(duration)
            
            if response.status_code == 200:
                task = response.json().get("task")
                logger.debug(f"Created task for agent {task_data['agent_id']} in {duration:.3f}s")
                return task
            else:
                logger.error(f"Failed to create task: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception creating task: {str(e)}")
            return None
    
    def _test_get_tasks_concurrently(self):
        """Test getting all tasks with concurrent requests."""
        logger.info("Testing GET /tasks with concurrent requests...")
        
        with ThreadPoolExecutor(max_workers=self.num_concurrent) as executor:
            futures = [executor.submit(self._get_all_tasks) for _ in range(self.num_concurrent)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error getting tasks: {str(e)}")
    
    def _get_all_tasks(self):
        """Get all tasks and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BASE_URL}/tasks")
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["get_tasks"].append(duration)
            
            if response.status_code == 200:
                tasks = response.json().get("tasks", [])
                logger.debug(f"Got {len(tasks)} tasks in {duration:.3f}s")
                return tasks
            else:
                logger.error(f"Failed to get tasks: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception getting tasks: {str(e)}")
            return []
    
    def _test_task_operations_concurrently(self):
        """Test task operations (get, update) concurrently."""
        if not self.tasks:
            logger.warning("No tasks to test operations on")
            return
        
        logger.info(f"Testing task operations concurrently on {len(self.tasks)} tasks...")
        
        with ThreadPoolExecutor(max_workers=self.num_concurrent) as executor:
            futures = []
            
            # Get task details
            for task in self.tasks:
                futures.append(executor.submit(self._get_task, task["id"]))
            
            # Update tasks
            for task in self.tasks:
                update_data = {
                    "status": "in_progress",
                    "started_at": datetime.utcnow().isoformat() + "Z"
                }
                futures.append(executor.submit(self._update_task, task["id"], update_data))
            
            # Wait for all operations to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in task operation: {str(e)}")
    
    def _get_task(self, task_id):
        """Get a specific task and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BASE_URL}/tasks/{task_id}")
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["get_task"].append(duration)
            
            if response.status_code == 200:
                task = response.json().get("task")
                logger.debug(f"Got task {task_id} in {duration:.3f}s")
                return task
            else:
                logger.error(f"Failed to get task {task_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception getting task {task_id}: {str(e)}")
            return None
    
    def _update_task(self, task_id, update_data):
        """Update a task and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.patch(f"{BASE_URL}/tasks/{task_id}", json=update_data)
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["update_task"].append(duration)
            
            if response.status_code == 200:
                task = response.json().get("task")
                logger.debug(f"Updated task {task_id} in {duration:.3f}s")
                return task
            else:
                logger.error(f"Failed to update task {task_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception updating task {task_id}: {str(e)}")
            return None
    
    def _test_results_operations_concurrently(self):
        """Test result operations (submit, get) concurrently."""
        if not self.tasks:
            logger.warning("No tasks to test result operations on")
            return
        
        logger.info(f"Testing result operations concurrently on {len(self.tasks)} tasks...")
        
        with ThreadPoolExecutor(max_workers=self.num_concurrent) as executor:
            futures = []
            
            # Submit results
            for task in self.tasks:
                result_data = {
                    "agent_id": task["agent_id"],
                    "status": "success",
                    "start_time": datetime.utcnow().isoformat() + "Z",
                    "end_time": datetime.utcnow().isoformat() + "Z",
                    "scan_results": {
                        "scanner": "gitleaks",
                        "findings_count": 3,
                        "findings": [
                            {
                                "type": "AWS Secret Key",
                                "file": "config.js",
                                "line": 42,
                                "severity": "high"
                            },
                            {
                                "type": "Password",
                                "file": "settings.json",
                                "line": 17,
                                "severity": "medium"
                            },
                            {
                                "type": "API Key",
                                "file": "api/client.js",
                                "line": 5,
                                "severity": "critical"
                            }
                        ]
                    }
                }
                futures.append(executor.submit(self._submit_result, task["id"], result_data))
            
            # Wait for all submissions to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in result submission: {str(e)}")
            
            # Get results
            futures = []
            for task in self.tasks:
                futures.append(executor.submit(self._get_results, task["id"]))
            
            # Wait for all get results to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error in get results: {str(e)}")
    
    def _submit_result(self, task_id, result_data):
        """Submit a result for a task and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.post(f"{BASE_URL}/tasks/{task_id}/results", json=result_data)
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["submit_result"].append(duration)
            
            if response.status_code in [200, 201]:
                logger.debug(f"Submitted result for task {task_id} in {duration:.3f}s")
                return True
            else:
                logger.error(f"Failed to submit result for task {task_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception submitting result for task {task_id}: {str(e)}")
            return False
    
    def _get_results(self, task_id):
        """Get results for a task and record the response time."""
        start_time = time.time()
        
        try:
            response = self.session.get(f"{BASE_URL}/tasks/{task_id}/results")
            duration = time.time() - start_time
            
            with self.lock:
                self.response_times["get_results"].append(duration)
            
            if response.status_code == 200:
                results = response.json().get("result")
                logger.debug(f"Got results for task {task_id} in {duration:.3f}s")
                return results
            else:
                logger.error(f"Failed to get results for task {task_id}: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception getting results for task {task_id}: {str(e)}")
            return []
    
    def _print_performance_summary(self):
        """Print a summary of the performance metrics."""
        logger.info("=== Performance Summary ===")
        logger.info(f"Total agents created: {len(self.agents)}")
        logger.info(f"Total tasks created: {len(self.tasks)}")
        
        # Print table header
        logger.info("\nEndpoint Performance (seconds):")
        logger.info(f"{'Endpoint':<20} {'Count':<8} {'Min':<8} {'Max':<8} {'Avg':<8} {'Median':<8} {'95%':<8}")
        logger.info("-" * 70)
        
        # Print metrics for each endpoint
        for endpoint, times in self.response_times.items():
            if not times:
                continue
                
            count = len(times)
            min_time = min(times)
            max_time = max(times)
            avg_time = sum(times) / count
            median_time = statistics.median(times)
            percentile_95 = sorted(times)[int(count * 0.95)] if count > 1 else max_time
            
            logger.info(f"{endpoint:<20} {count:<8d} {min_time:<8.3f} {max_time:<8.3f} {avg_time:<8.3f} {median_time:<8.3f} {percentile_95:<8.3f}")
        
        # Calculate overall statistics
        all_times = []
        for times in self.response_times.values():
            all_times.extend(times)
        
        if all_times:
            count = len(all_times)
            min_time = min(all_times)
            max_time = max(all_times)
            avg_time = sum(all_times) / count
            median_time = statistics.median(all_times)
            percentile_95 = sorted(all_times)[int(count * 0.95)] if count > 1 else max_time
            
            logger.info("-" * 70)
            logger.info(f"{'OVERALL':<20} {count:<8d} {min_time:<8.3f} {max_time:<8.3f} {avg_time:<8.3f} {median_time:<8.3f} {percentile_95:<8.3f}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Load test the SAST Console API')
    parser.add_argument('--agents', type=int, default=5,
                        help='Number of agents to create for testing (default: 5)')
    parser.add_argument('--tasks-per-agent', type=int, default=2,
                        help='Number of tasks to create per agent (default: 2)')
    parser.add_argument('--concurrent', type=int, default=3,
                        help='Number of concurrent requests to make (default: 3)')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    tester = SastConsoleLoadTester(
        num_agents=args.agents,
        num_tasks_per_agent=args.tasks_per_agent,
        num_concurrent=args.concurrent
    )
    success = tester.run_load_test()
    sys.exit(0 if success else 1) 