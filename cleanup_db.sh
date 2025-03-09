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

# 处理命令行参数
DRY_RUN=""
AGENTS_ONLY=""
TASKS_ONLY=""
OLDER_THAN=""

show_help() {
    echo "用法: ./cleanup_db.sh [选项]"
    echo ""
    echo "选项:"
    echo "  --dry-run      只显示要删除的内容，不实际删除"
    echo "  --agents-only  只清理测试代理数据"
    echo "  --tasks-only   只清理测试任务数据"
    echo "  --older-than N 只清理早于N天的数据"
    echo "  --help         显示此帮助信息"
    echo ""
    exit 0
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --dry-run)
            DRY_RUN="--dry-run"
            echo -e "${YELLOW}执行干运行模式 - 只显示要删除的内容，不实际删除${NC}"
            shift
            ;;
        --agents-only)
            AGENTS_ONLY="--agents-only"
            echo -e "${YELLOW}只清理测试代理数据${NC}"
            shift
            ;;
        --tasks-only)
            TASKS_ONLY="--tasks-only"
            echo -e "${YELLOW}只清理测试任务数据${NC}"
            shift
            ;;
        --older-than)
            OLDER_THAN="--older-than $2"
            echo -e "${YELLOW}只清理早于${2}天的数据${NC}"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}未知参数: $key${NC}"
            show_help
            ;;
    esac
done

# 如果不是干运行并且没有指定其他参数，要求确认
if [ "$DRY_RUN" == "" ] && [ "$AGENTS_ONLY" == "" ] && [ "$TASKS_ONLY" == "" ] && [ "$OLDER_THAN" == "" ]; then
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
python cleanup_database.py $DRY_RUN $AGENTS_ONLY $TASKS_ONLY $OLDER_THAN

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