#!/usr/bin/env python3
"""
CogniMate Agent - 依赖检查工具
自动检测并提示安装所需依赖
"""

import sys
import subprocess

def check_dependencies():
    """检查依赖"""
    print("🔍 检查 CogniMate Agent 依赖...\n")
    
    # 检查 Python 版本
    py_version = sys.version_info
    print(f"Python 版本: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print("❌ 需要 Python 3.8+")
        return False
    print("✅ Python 版本满足要求\n")
    
    # 核心模块依赖（标准库）
    core_deps = [
        ('os', '标准库'),
        ('pathlib', '标准库'),
        ('datetime', '标准库'),
        ('json', '标准库'),
        ('typing', '标准库'),
    ]
    
    print("核心模块依赖（标准库）:")
    for dep, desc in core_deps:
        try:
            __import__(dep)
            print(f"  ✅ {dep}: {desc}")
        except ImportError:
            print(f"  ❌ {dep}: 缺失")
    
    print("\n服务器模块依赖（第三方）:")
    server_deps = [
        ('fastapi', 'FastAPI', 'pip3 install fastapi'),
        ('uvicorn', 'Uvicorn', 'pip3 install uvicorn'),
    ]
    
    missing = []
    for module, name, install_cmd in server_deps:
        try:
            __import__(module)
            print(f"  ✅ {name}: 已安装")
        except ImportError:
            print(f"  ⚠️  {name}: 未安装（如需服务器功能，请运行: {install_cmd}）")
            missing.append((name, install_cmd))
    
    print("\n" + "="*50)
    if missing:
        print("💡 如需完整功能，请安装以下依赖:")
        for name, cmd in missing:
            print(f"   {cmd}")
        print("\n或运行: pip3 install -r requirements.txt")
    else:
        print("🎉 所有依赖已安装！")
    
    print("\n核心功能（学习记录、决策辅助）可直接使用，无需额外安装。")
    return True

if __name__ == "__main__":
    check_dependencies()
