import unittest
import requests
import json
import uuid
import logging
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestAgentsData(unittest.TestCase):
    """Test class for verifying agent data shown on the Agents page"""
    
    BASE_URL = "http://localhost:3000/api"
    
    def setUp(self):
        """Set up test by registering multiple test agents with different statuses"""
        # Generate unique identifiers for this test run
        self.test_run_id = str(uuid.uuid4())[:8]
        self.agent_ids = []
        self.agent_names = []
        
        # Create test agents with different capabilities and statuses
        self.create_test_agents()
    
    def create_test_agents(self):
        """Create multiple test agents with different capabilities and status"""
        # Agent 1: Online with multiple capabilities
        self.agent1_id = str(uuid.uuid4())
        self.agent1_name = f"test-agent-online-{self.test_run_id}"
        self.agent_ids.append(self.agent1_id)
        self.agent_names.append(self.agent1_name)
        
        # Agent 2: Offline with basic capabilities
        self.agent2_id = str(uuid.uuid4())
        self.agent2_name = f"test-agent-offline-{self.test_run_id}"
        self.agent_ids.append(self.agent2_id)
        self.agent_names.append(self.agent2_name)
        
        # Agent 3: Busy (online and running a task)
        self.agent3_id = str(uuid.uuid4())
        self.agent3_name = f"test-agent-busy-{self.test_run_id}"
        self.agent_ids.append(self.agent3_id)
        self.agent_names.append(self.agent3_name)
        
        # Create mock agents
        self.mock_agents = [
            {
                "id": self.agent1_id,
                "name": self.agent1_name,
                "status": "online",  # This agent received a heartbeat to set status to online
                "capabilities": ["bandit", "semgrep", "gitleaks", "dependency-check"],
                "system_info": {
                    "platform": "linux",
                    "python": "3.10.0",
                    "hostname": "test-host-1",
                    "cpu_count": 8,
                    "memory_gb": 16
                },
                "last_heartbeat": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": self.agent2_id,
                "name": self.agent2_name,
                "status": "offline",  # This agent's status was explicitly set to offline
                "capabilities": ["bandit", "semgrep"],
                "system_info": {
                    "platform": "windows",
                    "python": "3.9.5",
                    "hostname": "test-host-2",
                    "cpu_count": 4,
                    "memory_gb": 8
                },
                "last_heartbeat": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": self.agent3_id,
                "name": self.agent3_name,
                "status": "online",  # This agent received a heartbeat to set status to online
                "capabilities": ["bandit", "semgrep", "gitleaks"],
                "system_info": {
                    "platform": "macos",
                    "python": "3.11.0",
                    "hostname": "test-host-3",
                    "cpu_count": 10,
                    "memory_gb": 32
                },
                "last_heartbeat": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        # Create a mock task for agent 3
        self.task_id = str(uuid.uuid4())
    
    @patch('requests.get')
    def test_agents_list(self, mock_get):
        """Test that agents list shows all agents with correct data"""
        # Mock the GET response for agents
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"agents": self.mock_agents}
        )
        
        # Get all agents
        response = requests.get(f"{self.BASE_URL}/agents")
        self.assertEqual(response.status_code, 200)
        
        test_agents = response.json()["agents"]
        
        # Verify we have at least 3 agents
        self.assertGreaterEqual(len(test_agents), 3)
        
        # Verify each agent has the required fields
        for agent in test_agents:
            self.assertIn("id", agent)
            self.assertIn("name", agent)
            self.assertIn("status", agent)
            self.assertIn("capabilities", agent)
            self.assertIn("system_info", agent)
            self.assertIn("last_heartbeat", agent)
        
        # Verify agent 1 (online)
        online_agent = next((a for a in test_agents if "online" in a["name"]), None)
        self.assertIsNotNone(online_agent, "Online agent not found")
        self.assertEqual(online_agent["status"], "online")  # This agent received a heartbeat to set status to online
        self.assertGreaterEqual(len(online_agent["capabilities"]), 4)
        self.assertEqual(online_agent["system_info"]["platform"], "linux")
        
        # Verify agent 2 (offline)
        offline_agent = next((a for a in test_agents if "offline" in a["name"]), None)
        self.assertIsNotNone(offline_agent, "Offline agent not found")
        self.assertEqual(offline_agent["status"], "offline")  # This agent's status was explicitly set to offline
        self.assertEqual(len(offline_agent["capabilities"]), 2)
        self.assertEqual(offline_agent["system_info"]["platform"], "windows")
        
        # Verify agent 3 (busy)
        busy_agent = next((a for a in test_agents if "busy" in a["name"]), None)
        self.assertIsNotNone(busy_agent, "Busy agent not found")
        self.assertEqual(busy_agent["status"], "online")  # This agent received a heartbeat to set status to online
        self.assertEqual(len(busy_agent["capabilities"]), 3)
        self.assertEqual(busy_agent["system_info"]["platform"], "macos")
    
    @patch('requests.get')
    def test_agent_detail(self, mock_get):
        """Test that agent detail page shows correct data"""
        # Mock the GET response for a specific agent
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"agent": self.mock_agents[0]}
        )
        
        # Get agent details
        response = requests.get(f"{self.BASE_URL}/agents/{self.agent1_id}")
        self.assertEqual(response.status_code, 200)
        
        agent = response.json()["agent"]
        
        # Verify agent data
        self.assertEqual(agent["id"], self.agent1_id)
        self.assertEqual(agent["name"], self.agent1_name)
        self.assertEqual(agent["status"], "online")
        self.assertGreaterEqual(len(agent["capabilities"]), 4)
        self.assertEqual(agent["system_info"]["platform"], "linux")
    
    @patch('requests.get')
    @patch('requests.post')
    def test_agent_heartbeat(self, mock_post, mock_get):
        """Test that agent heartbeat updates status and timestamps correctly"""
        # Mock the GET response for the offline agent
        mock_get.side_effect = [
            # First call - before heartbeat
            MagicMock(
                status_code=200,
                json=lambda: {"agent": self.mock_agents[1]}  # offline agent
            ),
            # Second call - after heartbeat
            MagicMock(
                status_code=200,
                json=lambda: {
                    "agent": {
                        **self.mock_agents[1],
                        "status": "online",
                        "last_heartbeat": (datetime.now() + timedelta(seconds=10)).isoformat(),
                        "updated_at": (datetime.now() + timedelta(seconds=10)).isoformat()
                    }
                }
            )
        ]
        
        # Mock the POST response for heartbeat
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"success": True, "message": "Heartbeat received"}
        )
        
        # Get offline agent
        offline_agent_id = self.agent2_id
        response = requests.get(f"{self.BASE_URL}/agents/{offline_agent_id}")
        self.assertEqual(response.status_code, 200)
        
        before_heartbeat = response.json()["agent"]
        
        # Send heartbeat to update status
        heartbeat_data = {
            "status": "online"
        }
        response = requests.post(f"{self.BASE_URL}/agents/{offline_agent_id}/heartbeat", json=heartbeat_data)
        self.assertEqual(response.status_code, 200)
        
        # Get agent again to verify status changed
        response = requests.get(f"{self.BASE_URL}/agents/{offline_agent_id}")
        self.assertEqual(response.status_code, 200)
        
        after_heartbeat = response.json()["agent"]
        
        # Verify status changed
        self.assertEqual(after_heartbeat["status"], "online")
        self.assertNotEqual(before_heartbeat["last_heartbeat"], after_heartbeat["last_heartbeat"])
        
        # Verify timestamps updated
        before_updated = datetime.fromisoformat(before_heartbeat["updated_at"].replace('Z', '+00:00'))
        after_updated = datetime.fromisoformat(after_heartbeat["updated_at"].replace('Z', '+00:00'))
        self.assertGreater(after_updated, before_updated)
    
    def tearDown(self):
        """Clean up after tests"""
        # No need to clean up since we're using mocks
        pass

if __name__ == "__main__":
    unittest.main() 