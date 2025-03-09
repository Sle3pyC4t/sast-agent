#!/bin/bash
# 数据库清理脚本

# 设置颜色
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示脚本说明
echo -e "${YELLOW}SAST Console数据库清理工具${NC}"
echo "此脚本将清除数据库中的测试数据，包括测试代理和测试任务。"
echo ""

# 激活虚拟环境
source venv/bin/activate

# 检查是否要执行干运行（只显示，不删除）
DRY_RUN=""
if [ "$1" == "--dry-run" ]; then
    DRY_RUN="--dry-run"
    echo -e "${YELLOW}执行干运行模式 - 只显示要删除的内容，不实际删除${NC}"
else
    # 提示确认
    echo -e "${RED}警告：此操作将从数据库中删除所有测试数据，该操作不可撤销。${NC}"
    read -p "确认继续? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 0
    fi
fi

# 进入tests目录
cd tests

# 运行清理脚本
echo -e "${GREEN}开始清理数据库...${NC}"
python cleanup_database.py $DRY_RUN

# 返回到原目录
cd ..

# 显示完成消息
echo ""
if [ "$DRY_RUN" == "--dry-run" ]; then
    echo -e "${YELLOW}干运行完成。要实际删除数据，请不带--dry-run参数运行。${NC}"
else
    echo -e "${GREEN}数据库清理完成。${NC}"
fi

# 退出虚拟环境
deactivate 