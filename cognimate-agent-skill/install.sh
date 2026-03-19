#!/bin/bash
# CogniMate Agent - 自动安装脚本

echo "🚀 安装 CogniMate Agent Skill..."
echo "================================"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "📌 Python 版本: $python_version"

if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
    echo "❌ 需要 Python 3.8+"
    exit 1
fi

# 安装依赖（仅当需要运行服务器时）
if [ "$1" == "--with-server" ]; then
    echo "📦 安装服务器依赖..."
    pip3 install -r requirements.txt -q
    echo "✅ 依赖安装完成"
else
    echo "ℹ️  核心模块使用 Python 标准库，无需安装依赖"
    echo "💡 如需运行 API 服务器，请执行: ./install.sh --with-server"
fi

# 初始化工作目录
echo "📁 初始化工作目录..."
python3 -c "
from pathlib import Path
import os

workspace = os.getenv('OPENCLAW_WORKSPACE', os.getcwd())
learnings_dir = Path(workspace) / '.learnings'
learnings_dir.mkdir(exist_ok=True)

files = {
    learnings_dir / 'LEARNINGS.md': '# Learnings Log\n\n',
    learnings_dir / 'ERRORS.md': '# Errors Log\n\n',
    learnings_dir / 'FEATURE_REQUESTS.md': '# Feature Requests Log\n\n'
}

for filepath, content in files.items():
    if not filepath.exists():
        filepath.write_text(content)
        print(f'  创建: {filepath}')

print('✅ 初始化完成')
"

echo ""
echo "✅ CogniMate Agent 安装完成！"
echo ""
echo "使用方法:"
echo "  1. 复制 templates/SOUL.md.template 到工作目录并定制"
echo "  2. 在代码中导入: from core.learning_logger import get_logger"
echo "  3. 开始使用！"
echo ""
echo "示例:"
echo "  python3 -c \"from core.learning_logger import get_logger; logger = get_logger(); print('Ready!')\""
