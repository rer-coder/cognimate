#!/bin/bash
# CogniMate Server 启动脚本

cd "$(dirname "$0")"

echo "🚀 启动 CogniMate Server..."
echo "================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查依赖
pip3 show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📦 安装依赖..."
    pip3 install fastapi uvicorn -q
fi

# 启动服务器
echo "📍 服务器地址: http://localhost:8000"
echo "📖 API 文档: http://localhost:8000/docs"
echo "================================"
python3 main.py
