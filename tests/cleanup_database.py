#!/usr/bin/env python3
"""
数据库清理脚本 - 用于删除测试过程中创建的数据

该脚本会识别和删除由测试脚本创建的数据，包括：
1. 测试代理（名称包含'test-agent'）
2. 与测试代理相关的任务
3. 与测试任务相关的扫描结果
4. 与测试任务相关的漏洞数据
"""

import requests
import json
import argparse
import logging
import sys
import os
import time
from datetime import datetime, timedelta

# 添加父目录到路径，以便能导入agent包中的模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tests.config import API_URL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'cleanup.log'))
    ]
)
logger = logging.getLogger(__name__)

# 确保日志目录存在
os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)

def get_all_agents():
    """获取所有代理"""
    url = f"{API_URL}/agents"
    logger.info(f"GET {url}")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('agents', [])
        else:
            logger.error(f"获取代理失败：状态码{response.status_code}")
            return []
    except Exception as e:
        logger.error(f"获取代理时发生错误：{str(e)}")
        return []

def get_all_tasks():
    """获取所有任务"""
    url = f"{API_URL}/tasks"
    logger.info(f"GET {url}")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('tasks', [])
        else:
            logger.error(f"获取任务失败：状态码{response.status_code}")
            return []
    except Exception as e:
        logger.error(f"获取任务时发生错误：{str(e)}")
        return []

def delete_agent(agent_id):
    """删除指定的代理"""
    url = f"{API_URL}/agents/{agent_id}"
    logger.info(f"DELETE {url}")
    
    try:
        response = requests.delete(url)
        if response.status_code == 200:
            logger.info(f"成功删除代理：{agent_id}")
            return True
        else:
            logger.error(f"删除代理失败：{agent_id}, 状态码{response.status_code}")
            return False
    except Exception as e:
        logger.error(f"删除代理时发生错误：{agent_id}, {str(e)}")
        return False

def delete_task(task_id):
    """删除指定的任务"""
    url = f"{API_URL}/tasks/{task_id}"
    logger.info(f"DELETE {url}")
    
    try:
        response = requests.delete(url)
        if response.status_code == 200:
            logger.info(f"成功删除任务：{task_id}")
            return True
        else:
            logger.error(f"删除任务失败：{task_id}, 状态码{response.status_code}")
            return False
    except Exception as e:
        logger.error(f"删除任务时发生错误：{task_id}, {str(e)}")
        return False

def is_test_agent(agent):
    """判断是否是测试代理"""
    if not agent or not isinstance(agent, dict):
        return False
    
    name = agent.get('name', '')
    # 测试代理通常包含'test-agent'或特定的测试标识
    return 'test-agent' in name.lower() or 'test_agent' in name.lower()

def is_test_task(task):
    """判断是否是测试任务"""
    if not task or not isinstance(task, dict):
        return False
    
    repo_url = task.get('repository_url', '')
    # 测试任务通常使用特定的测试仓库URL
    return 'test/repo' in repo_url.lower() or 'test-repo' in repo_url.lower() or 'security-vulnerabilities' in repo_url.lower()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='清理数据库中的测试数据')
    parser.add_argument('--dry-run', action='store_true', 
                        help='只显示将要删除的内容，不实际删除')
    parser.add_argument('--agents-only', action='store_true',
                        help='只清理测试代理数据')
    parser.add_argument('--tasks-only', action='store_true',
                        help='只清理测试任务数据')
    parser.add_argument('--older-than', type=int, default=0, 
                        help='只清理早于指定天数的数据 (例如：--older-than 7 清理7天前的数据)')
    return parser.parse_args()

def is_older_than_days(date_str, days):
    """判断日期是否早于指定天数"""
    if not date_str or not isinstance(date_str, str):
        return False
    
    try:
        # 处理ISO格式的日期时间字符串
        date_str = date_str.replace('Z', '+00:00')
        date_obj = datetime.fromisoformat(date_str)
        
        # 计算指定天数前的日期
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return date_obj < cutoff_date
    except (ValueError, TypeError):
        return False

def cleanup_all_test_data(dry_run=False, agents_only=False, tasks_only=False, older_than_days=0):
    """清理所有测试数据"""
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}开始清理测试数据...")
    
    # 获取所有代理和任务
    agents = [] if tasks_only else get_all_agents()
    tasks = [] if agents_only else get_all_tasks()
    
    logger.info(f"获取到 {len(agents)} 个代理")
    logger.info(f"获取到 {len(tasks)} 个任务")
    
    # 识别测试代理和与之相关的任务
    test_agents = [agent for agent in agents if is_test_agent(agent)]
    
    # 如果指定了older_than_days，过滤出早于指定天数的代理
    if older_than_days > 0:
        test_agents = [agent for agent in test_agents if is_older_than_days(agent.get('created_at'), older_than_days)]
    
    test_agent_ids = [agent['id'] for agent in test_agents]
    
    # 识别测试任务（包括基于URL的和与测试代理相关的）
    test_tasks = [task for task in tasks if is_test_task(task) or task.get('agent_id') in test_agent_ids]
    
    # 如果指定了older_than_days，过滤出早于指定天数的任务
    if older_than_days > 0:
        test_tasks = [task for task in test_tasks if is_older_than_days(task.get('created_at'), older_than_days)]
    
    logger.info(f"识别到 {len(test_agents)} 个测试代理")
    logger.info(f"识别到 {len(test_tasks)} 个测试任务")
    
    if dry_run:
        # 仅展示将要删除的内容，不实际删除
        if not tasks_only:
            logger.info("[DRY RUN] 将要删除的测试代理:")
            for agent in test_agents:
                logger.info(f"  - {agent.get('name', 'Unknown')} (ID: {agent.get('id', 'Unknown')})")
        
        if not agents_only:
            logger.info("[DRY RUN] 将要删除的测试任务:")
            for task in test_tasks:
                logger.info(f"  - {task.get('repository_url', 'Unknown')} (ID: {task.get('id', 'Unknown')})")
        
        logger.info("[DRY RUN] 操作完成。实际运行时将删除这些数据。")
        return
    
    # 先删除任务，因为任务可能引用代理
    deleted_tasks = 0
    if not agents_only:
        for task in test_tasks:
            task_id = task.get('id')
            if task_id and delete_task(task_id):
                deleted_tasks += 1
                # 短暂暂停，避免过多的请求
                time.sleep(0.1)
    
    # 然后删除代理
    deleted_agents = 0
    if not tasks_only:
        for agent in test_agents:
            agent_id = agent.get('id')
            if agent_id and delete_agent(agent_id):
                deleted_agents += 1
                # 短暂暂停，避免过多的请求
                time.sleep(0.1)
    
    logger.info(f"清理完成。删除了 {deleted_tasks} 个测试任务和 {deleted_agents} 个测试代理。")

if __name__ == "__main__":
    args = parse_args()
    cleanup_all_test_data(
        dry_run=args.dry_run, 
        agents_only=args.agents_only, 
        tasks_only=args.tasks_only,
        older_than_days=args.older_than
    ) 