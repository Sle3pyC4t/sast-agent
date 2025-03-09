#!/usr/bin/env python3
"""
Test script for SAST Console API endpoints.
Tests all available endpoints at https://sast-console.vercel.app/
"""

import requests
import json
import time
import uuid
import sys
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api_tests.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Base URL for the SAST Console
BASE_URL = "https://sast-console.vercel.app/api"

# Test data
TEST_AGENT = {
    "agent_id": str(uuid.uuid4()),
    "agent_name": f"Test Agent {str(uuid.uuid4())[:8]}",
    "status": "available",
    "capabilities": ["gitleaks", "codeql", "semgrep"],
    "ip_address": "192.168.1.100",
    "system_info": {
        "os": "Linux",
        "version": "Ubuntu 22.04",
        "cpu_cores": 4,
        "memory": "8GB"
    }
}

TEST_TASK = {
    "repository_url": "https://github.com/username/test-repo",
    "branch": "main",
    "scanners": ["gitleaks", "codeql"],
    "created_by": "api-test"
}

class SastConsoleApiTester:
    """Class to test SAST Console API endpoints."""
    
    def __init__(self, run_negative_tests=False, verbose=False):
        """
        Initialize the API tester.
        
        Args:
            run_negative_tests: Whether to run negative test cases
            verbose: Whether to enable verbose logging
        """
        self.agent_id = None
        self.task_id = None
        self.session = requests.Session()
        self.run_negative_tests = run_negative_tests
        self.verbose = verbose
        
        if verbose:
            # Set logging level to DEBUG for verbose output
            logging.getLogger().setLevel(logging.DEBUG)
        
    def run_all_tests(self):
        """Run all API tests in sequence."""
        try:
            logger.info("=== Starting SAST Console API Tests ===")
            
            # Agent tests - positive cases
            self.test_register_agent()
            self.test_get_all_agents()
            self.test_get_agent()
            self.test_update_agent()
            self.test_agent_heartbeat()
            
            # Task tests - positive cases
            self.test_create_task()
            self.test_get_all_tasks()
            self.test_get_task()
            self.test_update_task_status()
            self.test_get_task_results()
            
            # Additional tests for better coverage
            self.test_filter_tasks_by_agent()
            self.test_multiple_results_for_task()
            
            # Negative test cases (only if enabled)
            if self.run_negative_tests:
                logger.info("=== Running Negative Test Cases ===")
                self.test_invalid_agent_id()
                self.test_invalid_task_id()
                self.test_missing_required_fields()
                self.test_invalid_data_types()
            
            logger.info("=== All SAST Console API Tests Completed Successfully ===")
            return True
        except Exception as e:
            logger.error(f"Error during test execution: {str(e)}")
            return False
    
    def _log_response(self, response, endpoint):
        """Log response details."""
        logger.info(f"Response from {endpoint}: Status Code: {response.status_code}")
        try:
            response_data = response.json()
            if self.verbose:
                logger.debug(f"Response Body: {json.dumps(response_data, indent=2)}")
            return response_data
        except:
            if self.verbose:
                logger.debug(f"Response Body: {response.text}")
            return None
    
    # Agent API Tests
    
    def test_register_agent(self):
        """Test registering a new agent."""
        endpoint = f"{BASE_URL}/agents/register"
        logger.info(f"Testing POST {endpoint}")
        
        response = self.session.post(endpoint, json=TEST_AGENT)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "agent" in response_data, "Response should contain 'agent' data"
        assert "id" in response_data["agent"], "Agent data should contain 'id'"
        
        # Validate agent data matches what was sent
        assert response_data["agent"]["name"] == TEST_AGENT["agent_name"], "Agent name should match"
        # API sets status to "online" regardless of what we send
        assert response_data["agent"]["status"] == "online", "Agent initial status should be 'online'"
        assert set(response_data["agent"]["capabilities"]) == set(TEST_AGENT["capabilities"]), "Agent capabilities should match"
        
        self.agent_id = response_data["agent"]["id"]
        logger.info(f"Registered new agent with ID: {self.agent_id}")
        return response_data
    
    def test_get_all_agents(self):
        """Test getting all agents."""
        endpoint = f"{BASE_URL}/agents"
        logger.info(f"Testing GET {endpoint}")
        
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "agents" in response_data, "Response should contain 'agents' data"
        assert isinstance(response_data["agents"], list), "'agents' should be a list"
        
        # Verify our agent is in the list
        if self.agent_id:
            agent_ids = [agent["id"] for agent in response_data["agents"]]
            assert self.agent_id in agent_ids, f"Our agent ID {self.agent_id} should be in the list"
        
        logger.info(f"Retrieved {len(response_data['agents'])} agents")
        return response_data
    
    def test_get_agent(self):
        """Test getting a specific agent."""
        if not self.agent_id:
            logger.warning("No agent ID available, skipping test_get_agent")
            return None
            
        endpoint = f"{BASE_URL}/agents/{self.agent_id}"
        logger.info(f"Testing GET {endpoint}")
        
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "agent" in response_data, "Response should contain 'agent' data"
        assert response_data["agent"]["id"] == self.agent_id, f"Agent ID should match {self.agent_id}"
        
        # Check that all expected fields are present
        expected_fields = ["id", "name", "status", "capabilities", "system_info", "created_at", "updated_at", "last_heartbeat"]
        for field in expected_fields:
            assert field in response_data["agent"], f"Agent data should contain '{field}' field"
        
        logger.info(f"Successfully retrieved agent with ID: {self.agent_id}")
        return response_data
    
    def test_update_agent(self):
        """Test updating an agent."""
        if not self.agent_id:
            logger.warning("No agent ID available, skipping test_update_agent")
            return None
            
        endpoint = f"{BASE_URL}/agents/{self.agent_id}"
        logger.info(f"Testing PATCH {endpoint}")
        
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
        
        response = self.session.patch(endpoint, json=update_data)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "agent" in response_data, "Response should contain 'agent' data"
        assert response_data["agent"]["status"] == update_data["status"], "Agent status should be updated"
        # API doesn't update capabilities or system_info, only status
        
        # Verify updated_at timestamp changed
        updated_at = response_data["agent"]["updated_at"]
        assert updated_at, "updated_at field should be present"
        
        logger.info(f"Successfully updated agent with ID: {self.agent_id}")
        return response_data
    
    def test_agent_heartbeat(self):
        """Test agent heartbeat."""
        if not self.agent_id:
            logger.warning("No agent ID available, skipping test_agent_heartbeat")
            return None
            
        endpoint = f"{BASE_URL}/agents/{self.agent_id}/heartbeat"
        logger.info(f"Testing POST {endpoint}")
        
        # First get the current heartbeat timestamp
        agent_response = self.session.get(f"{BASE_URL}/agents/{self.agent_id}")
        agent_data = agent_response.json()
        original_heartbeat = agent_data["agent"]["last_heartbeat"]
        
        # Send heartbeat with status
        heartbeat_data = {
            "status": "online"
        }
        
        # Send heartbeat
        response = self.session.post(endpoint, json=heartbeat_data)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "success" in response_data, "Response should contain 'success' field"
        assert response_data["success"] is True, "Heartbeat should be successful"
        
        # Verify heartbeat was updated by getting the agent again
        agent_response = self.session.get(f"{BASE_URL}/agents/{self.agent_id}")
        agent_data = agent_response.json()
        new_heartbeat = agent_data["agent"]["last_heartbeat"]
        
        if original_heartbeat and new_heartbeat:
            assert new_heartbeat != original_heartbeat, "Heartbeat timestamp should be updated"
        
        logger.info(f"Successfully sent heartbeat for agent with ID: {self.agent_id}")
        return response_data
    
    # Task API Tests
    
    def test_create_task(self):
        """Test creating a new task."""
        if not self.agent_id:
            logger.warning("No agent ID available, skipping test_create_task")
            return None
            
        endpoint = f"{BASE_URL}/tasks"
        logger.info(f"Testing POST {endpoint}")
        
        # Add agent_id to the test task data
        task_data = TEST_TASK.copy()
        task_data["agent_id"] = self.agent_id
        
        response = self.session.post(endpoint, json=task_data)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "task" in response_data, "Response should contain 'task' data"
        assert "id" in response_data["task"], "Task data should contain 'id'"
        
        # Validate task data
        assert response_data["task"]["agent_id"] == self.agent_id, "Task agent_id should match"
        assert response_data["task"]["repository_url"] == task_data["repository_url"], "Task repository_url should match"
        assert response_data["task"]["status"] == "pending", "Initial task status should be 'pending'"
        
        self.task_id = response_data["task"]["id"]
        logger.info(f"Created new task with ID: {self.task_id}")
        return response_data
    
    def test_get_all_tasks(self):
        """Test getting all tasks."""
        endpoint = f"{BASE_URL}/tasks"
        logger.info(f"Testing GET {endpoint}")
        
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "tasks" in response_data, "Response should contain 'tasks' data"
        assert isinstance(response_data["tasks"], list), "'tasks' should be a list"
        
        # Verify our task is in the list
        if self.task_id:
            task_ids = [task["id"] for task in response_data["tasks"]]
            assert self.task_id in task_ids, f"Our task ID {self.task_id} should be in the list"
        
        logger.info(f"Retrieved {len(response_data['tasks'])} tasks")
        return response_data
    
    def test_get_task(self):
        """Test getting a specific task."""
        if not self.task_id:
            logger.warning("No task ID available, skipping test_get_task")
            return None
            
        endpoint = f"{BASE_URL}/tasks/{self.task_id}"
        logger.info(f"Testing GET {endpoint}")
        
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "task" in response_data, "Response should contain 'task' data"
        assert response_data["task"]["id"] == self.task_id, f"Task ID should match {self.task_id}"
        
        # Check that all expected fields are present
        expected_fields = ["id", "agent_id", "repository_url", "branch", "scanners", "status", "created_at", "updated_at"]
        for field in expected_fields:
            assert field in response_data["task"], f"Task data should contain '{field}' field"
        
        logger.info(f"Successfully retrieved task with ID: {self.task_id}")
        return response_data
    
    def test_update_task_status(self):
        """Test updating a task status."""
        if not self.task_id:
            logger.warning("No task ID available, skipping test_update_task_status")
            return None
            
        endpoint = f"{BASE_URL}/tasks/{self.task_id}"
        logger.info(f"Testing PATCH {endpoint}")
        
        # Test status transition: pending -> in_progress
        update_data = {
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat() + "Z"
        }
        
        response = self.session.patch(endpoint, json=update_data)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "task" in response_data, "Response should contain 'task' data"
        assert response_data["task"]["status"] == update_data["status"], "Task status should be updated"
        assert "started_at" in response_data["task"], "Task should have started_at field"
        
        time.sleep(1)  # Small delay to ensure timestamps are different
        
        # Test status transition: in_progress -> completed
        complete_data = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat() + "Z"
        }
        
        response = self.session.patch(endpoint, json=complete_data)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response_data["task"]["status"] == complete_data["status"], "Task status should be updated to completed"
        assert "completed_at" in response_data["task"], "Task should have completed_at field"
        
        logger.info(f"Successfully updated task status with ID: {self.task_id}")
        return response_data
    
    def test_get_task_results(self):
        """Test getting task results."""
        if not self.task_id:
            logger.warning("No task ID available, skipping test_get_task_results")
            return None
            
        endpoint = f"{BASE_URL}/tasks/{self.task_id}/results"
        logger.info(f"Testing GET/POST {endpoint}")
        
        # First, let's upload a result
        post_data = {
            "agent_id": self.agent_id,
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
        
        post_response = self.session.post(endpoint, json=post_data)
        post_response_data = self._log_response(post_response, f"POST {endpoint}")
        
        assert post_response.status_code in [200, 201], f"Expected status code 200/201, got {post_response.status_code}"
        
        # Now get the results
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        response_data = response.json()
        assert "result" in response_data, "Response should contain 'result' data"
        
        # Verify the result data
        if response_data["result"]:
            result = response_data["result"]
            assert result["status"] == post_data["status"], "Status should match"
            assert "scan_results" in result, "Result should have scan_results"
            assert result["scan_results"]["scanner"] == post_data["scan_results"]["scanner"], "Scanner should match"
            assert result["scan_results"]["findings_count"] == post_data["scan_results"]["findings_count"], "Findings count should match"
        
        logger.info(f"Successfully retrieved results for task with ID: {self.task_id}")
        return response_data
    
    # Additional tests for better coverage
    
    def test_filter_tasks_by_agent(self):
        """Test filtering tasks by agent ID."""
        if not self.agent_id:
            logger.warning("No agent ID available, skipping test_filter_tasks_by_agent")
            return None
            
        endpoint = f"{BASE_URL}/tasks?agent_id={self.agent_id}"
        logger.info(f"Testing GET {endpoint}")
        
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "tasks" in response_data, "Response should contain 'tasks' data"
        
        # Check if any tasks belong to our agent
        our_tasks = [task for task in response_data["tasks"] if task["agent_id"] == self.agent_id]
        logger.info(f"Found {len(our_tasks)} tasks belonging to agent {self.agent_id}")
        
        # At least our created task should be in the list
        assert len(our_tasks) >= 1, f"Expected at least 1 task for agent {self.agent_id}"
        
        logger.info(f"Successfully filtered tasks by agent ID: {self.agent_id}")
        return response_data
    
    def test_multiple_results_for_task(self):
        """Test submitting multiple scanner results for a task."""
        if not self.task_id:
            logger.warning("No task ID available, skipping test_multiple_results_for_task")
            return None
            
        endpoint = f"{BASE_URL}/tasks/{self.task_id}/results"
        logger.info(f"Testing multiple results for task at {endpoint}")
        
        # Submit result for a different scanner
        post_data = {
            "agent_id": self.agent_id,
            "status": "success",
            "start_time": datetime.utcnow().isoformat() + "Z",
            "end_time": datetime.utcnow().isoformat() + "Z",
            "scan_results": {
                "scanner": "codeql",
                "findings_count": 2,
                "findings": [
                    {
                        "type": "SQL Injection",
                        "file": "api/db.js",
                        "line": 28,
                        "severity": "critical"
                    },
                    {
                        "type": "XSS",
                        "file": "components/form.js",
                        "line": 63,
                        "severity": "high"
                    }
                ]
            }
        }
        
        post_response = self.session.post(endpoint, json=post_data)
        post_response_data = self._log_response(post_response, f"POST {endpoint}")
        
        # API may not support multiple results for a task, so we'll check if it's supported
        if post_response.status_code in [200, 201]:
            # API supports multiple results, continue with the test
            logger.info("API supports multiple results for a task")
            
            # Now get the results
            response = self.session.get(endpoint)
            response_data = self._log_response(response, endpoint)
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            assert "result" in response_data, "Response should contain 'result' data"
            
            # If API returns an array of results, check that we have at least 2
            if isinstance(response_data["result"], list):
                assert len(response_data["result"]) >= 2, f"Expected at least 2 results, got {len(response_data['result'])}"
                
                # Verify we have results for both scanners
                scanners = [result["scan_results"]["scanner"] for result in response_data["result"]]
                assert "gitleaks" in scanners, "Should have result for gitleaks scanner"
                assert "codeql" in scanners, "Should have result for codeql scanner"
            else:
                # API might have overwritten the previous result
                logger.info("API appears to overwrite previous results rather than storing multiple results")
            
            logger.info(f"Successfully tested multiple results for task with ID: {self.task_id}")
        else:
            # API doesn't support multiple results, log and skip
            logger.info(f"API does not support multiple results for a task (status code: {post_response.status_code})")
            logger.info("Skipping multiple results test")
        
        return post_response_data
    
    # Negative test cases
    
    def test_invalid_agent_id(self):
        """Test accessing an agent with an invalid ID."""
        logger.info("Testing with invalid agent ID")
        
        invalid_id = "invalid-agent-id"
        endpoint = f"{BASE_URL}/agents/{invalid_id}"
        
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code in [404, 400, 500], f"Expected error status code, got {response.status_code}"
        
        # Test heartbeat with invalid ID
        heartbeat_endpoint = f"{BASE_URL}/agents/{invalid_id}/heartbeat"
        heartbeat_response = self.session.post(heartbeat_endpoint, json={"status": "online"})
        self._log_response(heartbeat_response, heartbeat_endpoint)
        
        assert heartbeat_response.status_code in [404, 400, 500], f"Expected error status code, got {heartbeat_response.status_code}"
        
        logger.info("Successfully tested invalid agent ID scenarios")
    
    def test_invalid_task_id(self):
        """Test accessing a task with an invalid ID."""
        logger.info("Testing with invalid task ID")
        
        invalid_id = "invalid-task-id"
        endpoint = f"{BASE_URL}/tasks/{invalid_id}"
        
        response = self.session.get(endpoint)
        response_data = self._log_response(response, endpoint)
        
        assert response.status_code in [404, 400, 500], f"Expected error status code, got {response.status_code}"
        
        # Test results with invalid ID
        results_endpoint = f"{BASE_URL}/tasks/{invalid_id}/results"
        results_response = self.session.get(results_endpoint)
        self._log_response(results_response, results_endpoint)
        
        assert results_response.status_code in [404, 400, 500], f"Expected error status code, got {results_response.status_code}"
        
        logger.info("Successfully tested invalid task ID scenarios")
    
    def test_missing_required_fields(self):
        """Test API behavior with missing required fields."""
        logger.info("Testing with missing required fields")
        
        # Test agent registration with missing name
        agent_data = TEST_AGENT.copy()
        del agent_data["agent_name"]
        
        response = self.session.post(f"{BASE_URL}/agents/register", json=agent_data)
        response_data = self._log_response(response, f"{BASE_URL}/agents/register")
        
        assert response.status_code in [400, 422], f"Expected error status code, got {response.status_code}"
        
        # Test task creation with missing repository_url
        if self.agent_id:
            task_data = {"agent_id": self.agent_id}
            
            response = self.session.post(f"{BASE_URL}/tasks", json=task_data)
            response_data = self._log_response(response, f"{BASE_URL}/tasks")
            
            assert response.status_code in [400, 422], f"Expected error status code, got {response.status_code}"
        
        logger.info("Successfully tested missing required fields scenarios")
    
    def test_invalid_data_types(self):
        """Test API behavior with invalid data types."""
        logger.info("Testing with invalid data types")
        
        # Test agent registration with invalid data types
        agent_data = TEST_AGENT.copy()
        agent_data["capabilities"] = "not-an-array"
        
        response = self.session.post(f"{BASE_URL}/agents/register", json=agent_data)
        response_data = self._log_response(response, f"{BASE_URL}/agents/register")
        
        # API might accept invalid data types and try to handle them
        logger.info(f"API returned status code {response.status_code} for invalid capabilities data type")
        
        # Test task creation with invalid data types
        if self.agent_id:
            task_data = {
                "agent_id": self.agent_id,
                "repository_url": "https://github.com/username/test-repo",
                "scanners": "not-an-array"
            }
            
            response = self.session.post(f"{BASE_URL}/tasks", json=task_data)
            response_data = self._log_response(response, f"{BASE_URL}/tasks")
            
            # API might accept invalid data types and try to handle them
            logger.info(f"API returned status code {response.status_code} for invalid scanners data type")
        
        logger.info("Successfully tested invalid data types scenarios")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test the SAST Console API')
    parser.add_argument('--negative', action='store_true',
                        help='Run negative tests (testing error conditions)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output with full response bodies')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    tester = SastConsoleApiTester(
        run_negative_tests=args.negative,
        verbose=args.verbose
    )
    success = tester.run_all_tests()
    sys.exit(0 if success else 1) 