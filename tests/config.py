"""
测试配置文件
"""

# API基础URL配置
# 本地开发环境URL
LOCAL_API_URL = "http://localhost:3000/api"

# 生产环境URL
PROD_API_URL = "https://sast-console.vercel.app/api"

# 当前使用的URL - 修改此变量来切换环境
# 如果本地服务器没有运行，请使用PROD_API_URL
API_URL = PROD_API_URL 