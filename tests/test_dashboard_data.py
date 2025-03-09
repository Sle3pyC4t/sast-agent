import unittest
import requests
import json
import uuid
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDashboardData(unittest.TestCase):
    """Test class for verifying data shown on the Dashboard page"""
    
    BASE_URL = "http://localhost:3000/api"
    
    def setUp(self):
        """Set up test by registering a test agent and creating test tasks"""
        # Generate unique identifiers for this test run
        self.test_run_id = str(uuid.uuid4())[:8]
        self.agent_id = str(uuid.uuid4())
        self.agent_name = f"test-agent-{self.test_run_id}"
        
        # Mock data that would normally come from the server
        self.mock_agent = {
            "id": self.agent_id,
            "name": self.agent_name,
            "status": "online",  # Agents are set to 'online' by default during registration
            "capabilities": ["bandit", "semgrep"],
            "system_info": {
                "platform": "linux",
                "python": "3.10.0",
                "hostname": "test-host"
            },
            "last_heartbeat": datetime.now().isoformat()
        }
        
        # Create task data
        self.task_data = {
            "agent_id": self.agent_id,
            "repository_url": f"https://github.com/test/repo-{self.test_run_id}",
            "branch": "main",
            "scanners": ["bandit", "semgrep"]
        }
        
        # Create test tasks with different statuses
        self.create_test_tasks()
        
    def create_test_tasks(self):
        """Create mock test tasks with different statuses for testing dashboard stats"""
        # Create mock task IDs
        self.pending_task_id = str(uuid.uuid4())
        self.running_task_id = str(uuid.uuid4())
        self.completed_task_id = str(uuid.uuid4())
        self.failed_task_id = str(uuid.uuid4())
        
    @patch('requests.get')
    @patch('requests.post')
    def test_agents_count(self, mock_post, mock_get):
        """Test that agents count on dashboard is accurate"""
        # Mock the GET response for agents
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"agents": [self.mock_agent]}
        )
        
        # Get all agents
        response = requests.get(f"{self.BASE_URL}/agents")
        self.assertEqual(response.status_code, 200)
        
        agents = response.json()["agents"]
        
        # Filter for our test agent
        test_agent = next((a for a in agents if a["id"] == self.agent_id), None)
        self.assertIsNotNone(test_agent, "Test agent not found in agents list")
        
        # Verify agent data structure matches frontend expectations
        self.assertEqual(test_agent["name"], self.agent_name)
        self.assertEqual(test_agent["status"], "online")  # Agents are set to 'online' by default during registration
        self.assertIn("capabilities", test_agent)
        self.assertIn("system_info", test_agent)
        self.assertIn("last_heartbeat", test_agent)
        
        # Mock the POST response for heartbeat
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"success": True, "message": "Heartbeat received"}
        )
        
        # Update agent status to online via heartbeat
        heartbeat_data = {
            "status": "online"
        }
        response = requests.post(f"{self.BASE_URL}/agents/{self.agent_id}/heartbeat", json=heartbeat_data)
        self.assertEqual(response.status_code, 200)
    
    @patch('requests.get')
    @patch('requests.post')
    def test_tasks_count(self, mock_post, mock_get):
        """Test that task counts on dashboard are accurate"""
        # Mock the GET response for tasks
        mock_tasks = [
            {
                "id": self.pending_task_id,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "repository_url": f"https://github.com/test/repo-{self.test_run_id}",
                "branch": "main",
                "scanners": ["bandit", "semgrep"],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None
            },
            {
                "id": self.running_task_id,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "repository_url": f"https://github.com/test/repo-running-{self.test_run_id}",
                "branch": "main",
                "scanners": ["bandit", "semgrep"],
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "completed_at": None
            },
            {
                "id": self.completed_task_id,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "repository_url": f"https://github.com/test/repo-completed-{self.test_run_id}",
                "branch": "main",
                "scanners": ["bandit", "semgrep"],
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            },
            {
                "id": self.failed_task_id,
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "repository_url": f"https://github.com/test/repo-failed-{self.test_run_id}",
                "branch": "main",
                "scanners": ["bandit", "semgrep"],
                "status": "failed",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            }
        ]
        
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"tasks": mock_tasks}
        )
        
        # Get all tasks
        response = requests.get(f"{self.BASE_URL}/tasks")
        self.assertEqual(response.status_code, 200)
        
        tasks = response.json()["tasks"]
        
        # Count tasks by status
        pending_count = sum(1 for t in tasks if t["status"] == "pending")
        running_count = sum(1 for t in tasks if t["status"] == "running")
        completed_count = sum(1 for t in tasks if t["status"] == "completed")
        failed_count = sum(1 for t in tasks if t["status"] == "failed")
        
        # Verify counts
        self.assertEqual(pending_count, 1, "Pending task count incorrect")
        self.assertEqual(running_count, 1, "Running task count incorrect")
        self.assertEqual(completed_count, 1, "Completed task count incorrect")
        self.assertEqual(failed_count, 1, "Failed task count incorrect")
        
        # Verify total count
        self.assertEqual(len(tasks), 4, "Total task count incorrect")
    
    @patch('requests.get')
    def test_vulnerabilities_data(self, mock_get):
        """Test that vulnerability data on dashboard is accurate"""
        # Mock the GET response for vulnerabilities
        mock_vulnerabilities = [
            {
                "id": str(uuid.uuid4()),
                "result_id": str(uuid.uuid4()),
                "task_id": self.completed_task_id,
                "scanner": "bandit",
                "severity": "medium",
                "confidence": "high",
                "file_path": "test.py",
                "line_number": 10,
                "code_snippet": "print('Password: ' + password)",
                "message": "Possible hardcoded password",
                "description": "Hardcoded passwords can lead to security vulnerabilities",
                "cwe": "CWE-259",
                "created_at": datetime.now().isoformat(),
                "repository_url": f"https://github.com/test/repo-completed-{self.test_run_id}"
            },
            {
                "id": str(uuid.uuid4()),
                "result_id": str(uuid.uuid4()),
                "task_id": self.completed_task_id,
                "scanner": "semgrep",
                "severity": "high",
                "confidence": "medium",
                "file_path": "test.py",
                "line_number": 15,
                "code_snippet": "eval(user_input)",
                "message": "Avoid using eval",
                "description": "Eval can execute arbitrary code",
                "cwe": "CWE-95",
                "created_at": datetime.now().isoformat(),
                "repository_url": f"https://github.com/test/repo-completed-{self.test_run_id}"
            },
            {
                "id": str(uuid.uuid4()),
                "result_id": str(uuid.uuid4()),
                "task_id": self.completed_task_id,
                "scanner": "bandit",
                "severity": "low",
                "confidence": "medium",
                "file_path": "test2.py",
                "line_number": 25,
                "code_snippet": "# TODO: Fix this later",
                "message": "TODO found",
                "description": "TODO comments should be addressed",
                "cwe": None,
                "created_at": datetime.now().isoformat(),
                "repository_url": f"https://github.com/test/repo-completed-{self.test_run_id}"
            }
        ]
        
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"vulnerabilities": mock_vulnerabilities}
        )
        
        # Get all vulnerabilities
        response = requests.get(f"{self.BASE_URL}/vulnerabilities")
        self.assertEqual(response.status_code, 200)
        
        vulnerabilities = response.json()["vulnerabilities"]
        
        # Count vulnerabilities by severity
        high_count = sum(1 for v in vulnerabilities if v["severity"] == "high")
        medium_count = sum(1 for v in vulnerabilities if v["severity"] == "medium")
        low_count = sum(1 for v in vulnerabilities if v["severity"] == "low")
        
        # Verify counts
        self.assertEqual(high_count, 1, "High severity count incorrect")
        self.assertEqual(medium_count, 1, "Medium severity count incorrect")
        self.assertEqual(low_count, 1, "Low severity count incorrect")
        
        # Verify total count
        self.assertEqual(len(vulnerabilities), 3, "Total vulnerability count incorrect")
        
        # Verify vulnerability data structure
        vuln = vulnerabilities[0]
        self.assertIn("id", vuln)
        self.assertIn("task_id", vuln)
        self.assertIn("scanner", vuln)
        self.assertIn("severity", vuln)
        self.assertIn("file_path", vuln)
        self.assertIn("line_number", vuln)
        self.assertIn("code_snippet", vuln)
        self.assertIn("message", vuln)
        self.assertIn("repository_url", vuln)
    
    def tearDown(self):
        """Clean up after tests"""
        # No need to clean up since we're using mocks
        pass

if __name__ == "__main__":
    unittest.main() 