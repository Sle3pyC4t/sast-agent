#!/bin/bash
# 快速运行测试的脚本

# 激活虚拟环境
source venv/bin/activate

# 进入测试目录
cd tests

# 运行测试
python run_tests.py $@

# 显示完成消息
echo ""
echo "测试运行完成，完整日志请查看 tests/logs 目录" 