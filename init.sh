#!/bin/bash
# CogniMate 初始化脚本
# 使用方法: ./init.sh

set -e

echo "🚀 CogniMate 初始化脚本"
echo "========================"

# 检查 Python 版本
echo "📋 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 版本过低，需要 >= 3.9，当前: $python_version"
    exit 1
fi
echo "✅ Python 版本检查通过: $python_version"

# 创建虚拟环境
echo ""
echo "📦 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "🔌 激活虚拟环境..."
source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 安装依赖
echo ""
echo "📥 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ 依赖安装完成"

# 检查配置文件
echo ""
echo "⚙️  检查配置文件..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ 已创建 .env 文件（请编辑填入你的配置）"
    else
        echo "⚠️  .env.example 不存在，请手动创建 .env 文件"
    fi
else
    echo "✅ .env 文件已存在"
fi

if [ ! -f "config.json" ]; then
    if [ -f "config.example.json" ]; then
        cp config.example.json config.json
        echo "✅ 已创建 config.json 文件（请编辑填入你的配置）"
    else
        echo "⚠️  config.example.json 不存在，请手动创建 config.json 文件"
    fi
else
    echo "✅ config.json 文件已存在"
fi

# 创建必要目录
echo ""
echo "📁 创建必要目录..."
mkdir -p memory
echo "✅ 目录创建完成"

# 初始化数据库
echo ""
echo "🗄️  初始化数据库..."
python3 -c "
import sqlite3
import os

db_path = 'cognimate.db'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建打卡表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建目标表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            target TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print('✅ 数据库初始化完成')
else:
    print('✅ 数据库已存在')
"

echo ""
echo "========================"
echo "🎉 初始化完成！"
echo ""
echo "下一步操作："
echo ""
echo "1. 编辑配置文件："
echo "   nano .env"
echo ""
echo "2. 配置完成后，启动服务："
echo "   python server/main.py"
echo ""
echo "3. 访问 API 文档："
echo "   http://localhost:8000/docs"
echo ""
echo "📖 详细配置说明：docs/CONFIG.md"
echo ""
