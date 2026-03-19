#!/bin/bash
# CogniMate 智能日程管理系统 - 启动脚本

cd "$(dirname "$0")"

echo "🚀 CogniMate 智能日程管理系统"
echo "================================"

# 检查依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt

# 初始化数据库
echo "🗄️  初始化数据库..."
python database/migration.py

# 启动API服务
echo "🌐 启动API服务..."
echo "访问文档: http://localhost:8001/docs"
echo ""

python api/main.py
