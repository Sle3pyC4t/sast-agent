#!/usr/bin/env python3
"""
验证脚本，测试所有API接口是否工作正常
"""

import requests
import json
import uuid
import logging
import sys
import os
from datetime import datetime

# 添加父目录到路径，以便能导入agent包中的模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# API基础URL
# BASE_URL = "http://localhost:3000/api"
BASE_URL = "https://sast-console.vercel.app/api"

def test_agents_api():
    """测试agents API"""
    logger.info("=== 测试 Agents API ===")
    
    # 测试获取所有agents
    url = f"{BASE_URL}/agents"
    logger.info(f"GET {url}")
    response = requests.get(url)
    logger.info(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"返回的agents数量: {len(data.get('agents', []))}")
        
        # 打印agents数据的简略信息
        for i, agent in enumerate(data.get('agents', [])[:3]):  # 只显示前3个
            logger.info(f"Agent #{i+1}: {agent.get('name', 'N/A')} - {agent.get('status', 'N/A')}")
    else:
        logger.error(f"请求失败: {response.text}")
    
    # 测试注册一个新agent
    agent_id = str(uuid.uuid4())
    agent_name = f"test-agent-{agent_id[:8]}"
    
    url = f"{BASE_URL}/agents/register"
    data = {
        "id": agent_id,
        "name": agent_name,
        "status": "online",
        "capabilities": ["bandit", "semgrep"],
        "system_info": {
            "platform": "linux",
            "python": "3.10.0",
            "hostname": "test-host"
        }
    }
    
    logger.info(f"POST {url}")
    logger.info(f"数据: {json.dumps(data)}")
    
    response = requests.post(url, json=data)
    logger.info(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f"响应: {json.dumps(result)}")
        
        # 尝试获取新注册的agent
        url = f"{BASE_URL}/agents/{agent_id}"
        logger.info(f"GET {url}")
        response = requests.get(url)
        logger.info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"获取到agent: {json.dumps(data)}")
        else:
            logger.error(f"请求失败: {response.text}")
    else:
        logger.error(f"请求失败: {response.text}")
    
    return agent_id, agent_name

def test_tasks_api(agent_id, agent_name):
    """测试tasks API"""
    logger.info("\n=== 测试 Tasks API ===")
    
    # 测试获取所有tasks
    url = f"{BASE_URL}/tasks"
    logger.info(f"GET {url}")
    response = requests.get(url)
    logger.info(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"返回的tasks数量: {len(data.get('tasks', []))}")
        
        # 打印tasks数据的简略信息
        for i, task in enumerate(data.get('tasks', [])[:3]):  # 只显示前3个
            logger.info(f"Task #{i+1}: {task.get('repository_url', 'N/A')} - {task.get('status', 'N/A')}")
    else:
        logger.error(f"请求失败: {response.text}")
    
    # 创建一个新task
    task_data = {
        "agent_id": agent_id,
        "repository_url": "https://github.com/test/repo-test",
        "branch": "main",
        "scanners": ["bandit", "semgrep"]
    }
    
    url = f"{BASE_URL}/tasks"
    logger.info(f"POST {url}")
    logger.info(f"数据: {json.dumps(task_data)}")
    
    response = requests.post(url, json=task_data)
    logger.info(f"状态码: {response.status_code}")
    
    task_id = None
    if response.status_code == 200:
        result = response.json()
        logger.info(f"响应: {json.dumps(result)}")
        
        if "task" in result and "id" in result["task"]:
            task_id = result["task"]["id"]
            
            # 尝试获取新创建的task
            url = f"{BASE_URL}/tasks/{task_id}"
            logger.info(f"GET {url}")
            response = requests.get(url)
            logger.info(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"获取到task: {json.dumps(data)}")
            else:
                logger.error(f"请求失败: {response.text}")
    else:
        logger.error(f"请求失败: {response.text}")
    
    return task_id

def test_vulnerabilities_api():
    """测试vulnerabilities API"""
    logger.info("\n=== 测试 Vulnerabilities API ===")
    
    # 测试获取所有vulnerabilities
    url = f"{BASE_URL}/vulnerabilities"
    logger.info(f"GET {url}")
    response = requests.get(url)
    logger.info(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"返回的vulnerabilities数量: {len(data.get('vulnerabilities', []))}")
        
        # 打印vulnerabilities数据的简略信息
        for i, vuln in enumerate(data.get('vulnerabilities', [])[:3]):  # 只显示前3个
            logger.info(f"Vulnerability #{i+1}: {vuln.get('file_path', 'N/A')} - {vuln.get('severity', 'N/A')}")
    else:
        logger.error(f"请求失败: {response.text}")

def main():
    """主函数"""
    logger.info("开始验证API...")
    
    try:
        # 测试agents API并获取新创建的agent ID
        agent_id, agent_name = test_agents_api()
        
        # 测试tasks API并传入agent ID
        task_id = test_tasks_api(agent_id, agent_name)
        
        # 测试vulnerabilities API
        test_vulnerabilities_api()
        
        logger.info("\n所有API测试完成")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 