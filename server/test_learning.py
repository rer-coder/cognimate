#!/usr/bin/env python3
"""
CogniMate 学习记录功能测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("\n🩺 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务正常运行: {response.json()}")
            return True
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("💡 请先启动服务器: ./server/start.sh")
        return False

def test_log_learning():
    """测试记录学习"""
    print("\n📝 测试记录学习...")
    payload = {
        "function_name": "log_learning",
        "arguments": {
            "category": "best_practice",
            "summary": "测试学习记录功能",
            "details": "这是一个测试条目，验证学习记录功能是否正常工作",
            "suggested_action": "观察测试结果",
            "priority": "low",
            "area": "general",
            "source": "test",
            "tags": ["test", "learning"],
            "related_files": "server/test_learning.py"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/log_learning",
            json=payload,
            timeout=5
        )
        result = response.json()
        if result.get("status") == "success":
            print(f"✅ 学习记录成功: {result['result']}")
            return True
        else:
            print(f"❌ 学习记录失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_log_error():
    """测试记录错误"""
    print("\n❌ 测试记录错误...")
    payload = {
        "function_name": "log_error",
        "arguments": {
            "summary": "测试错误记录",
            "details": "这是一个测试错误条目",
            "suggested_action": "无需处理",
            "priority": "low",
            "area": "general",
            "source": "test",
            "tags": ["test", "error"]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/log_error",
            json=payload,
            timeout=5
        )
        result = response.json()
        if result.get("status") == "success":
            print(f"✅ 错误记录成功")
            return True
        else:
            print(f"❌ 错误记录失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_log_feature():
    """测试记录功能请求"""
    print("\n💡 测试记录功能请求...")
    payload = {
        "function_name": "log_feature_request",
        "arguments": {
            "summary": "测试功能请求记录",
            "details": "这是一个测试功能请求",
            "suggested_action": "观察效果",
            "priority": "low",
            "area": "general",
            "source": "test",
            "tags": ["test", "feature"]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/log_feature_request",
            json=payload,
            timeout=5
        )
        result = response.json()
        if result.get("status") == "success":
            print(f"✅ 功能请求记录成功")
            return True
        else:
            print(f"❌ 功能请求记录失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_query_learnings():
    """测试查询学习记录"""
    print("\n🔍 测试查询学习记录...")
    payload = {
        "function_name": "query_learnings",
        "arguments": {
            "query": "测试",
            "limit": 5
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/query_learnings",
            json=payload,
            timeout=5
        )
        result = response.json()
        if result.get("status") == "success":
            count = result["result"]["count"]
            print(f"✅ 查询成功，找到 {count} 条记录")
            return True
        else:
            print(f"❌ 查询失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_get_stats():
    """测试获取统计"""
    print("\n📊 测试获取统计...")
    payload = {
        "function_name": "get_learning_stats",
        "arguments": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/get_learning_stats",
            json=payload,
            timeout=5
        )
        result = response.json()
        if result.get("status") == "success":
            stats = result["result"]
            print(f"✅ 统计信息:")
            print(f"   学习记录: {stats.get('learnings', 0)}")
            print(f"   错误记录: {stats.get('errors', 0)}")
            print(f"   功能请求: {stats.get('features', 0)}")
            print(f"   总计: {stats.get('total', 0)}")
            return True
        else:
            print(f"❌ 获取统计失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 50)
    print("🧪 CogniMate 学习记录功能测试")
    print("=" * 50)
    
    # 检查服务是否运行
    if not test_health():
        print("\n⚠️  服务未运行，请先执行: ./server/start.sh")
        return
    
    # 运行测试
    tests = [
        test_log_learning,
        test_log_error,
        test_log_feature,
        test_query_learnings,
        test_get_stats
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append(False)
    
    # 汇总
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"📋 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！学习记录功能正常工作。")
    else:
        print("⚠️  部分测试失败，请检查日志。")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
