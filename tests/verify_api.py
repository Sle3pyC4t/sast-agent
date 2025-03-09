import requests
import json
import os
import sys
from datetime import datetime

# 添加父目录到路径，以便能导入agent包中的模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verify_agents_api():
    """验证agents API返回的数据"""
    url = "http://localhost:3000/api/agents"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("Agents API 返回状态: 成功")
        print(f"返回的agents数量: {len(data.get('agents', []))}")
        
        # 打印agents数据的详细信息
        for i, agent in enumerate(data.get('agents', [])):
            print(f"\nAgent #{i+1}:")
            print(f"  ID: {agent.get('id', 'N/A')}")
            print(f"  Name: {agent.get('name', 'N/A')}")
            print(f"  Status: {agent.get('status', 'N/A')}")
            print(f"  Capabilities: {agent.get('capabilities', [])}")
            print(f"  System Info: {agent.get('system_info', {})}")
            print(f"  Last Heartbeat: {agent.get('last_heartbeat', 'N/A')}")
    else:
        print(f"Agents API 请求失败，状态码: {response.status_code}")
        print(response.text)

def verify_tasks_api():
    """验证tasks API返回的数据"""
    url = "http://localhost:3000/api/tasks"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("\nTasks API 返回状态: 成功")
        print(f"返回的tasks数量: {len(data.get('tasks', []))}")
        
        # 打印tasks数据的详细信息
        for i, task in enumerate(data.get('tasks', [])):
            print(f"\nTask #{i+1}:")
            print(f"  ID: {task.get('id', 'N/A')}")
            print(f"  Agent ID: {task.get('agent_id', 'N/A')}")
            print(f"  Agent Name: {task.get('agent_name', 'N/A')}")
            print(f"  Repository: {task.get('repository_url', 'N/A')}")
            print(f"  Status: {task.get('status', 'N/A')}")
            print(f"  Created At: {task.get('created_at', 'N/A')}")
    else:
        print(f"Tasks API 请求失败，状态码: {response.status_code}")
        print(response.text)

def verify_vulnerabilities_api():
    """验证vulnerabilities API返回的数据"""
    url = "http://localhost:3000/api/vulnerabilities"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("\nVulnerabilities API 返回状态: 成功")
        print(f"返回的vulnerabilities数量: {len(data.get('vulnerabilities', []))}")
        
        # 打印vulnerabilities数据的详细信息
        for i, vuln in enumerate(data.get('vulnerabilities', [])[:3]):  # 只打印前3个
            print(f"\nVulnerability #{i+1}:")
            print(f"  ID: {vuln.get('id', 'N/A')}")
            print(f"  Task ID: {vuln.get('task_id', 'N/A')}")
            print(f"  Severity: {vuln.get('severity', 'N/A')}")
            print(f"  File: {vuln.get('file_path', 'N/A')}:{vuln.get('line_number', 'N/A')}")
            print(f"  Message: {vuln.get('message', 'N/A')}")
    else:
        print(f"Vulnerabilities API 请求失败，状态码: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("开始验证API...\n")
    verify_agents_api()
    verify_tasks_api()
    verify_vulnerabilities_api()
    print("\n验证完成") 