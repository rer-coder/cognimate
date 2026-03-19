#!/usr/bin/env python3
"""
测试决策前查询学习记录 和 自动晋升功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试服务状态"""
    print("\n🩺 检查服务状态...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        data = response.json()
        print(f"✅ 服务正常 (v{data.get('version', 'unknown')})")
        print(f"   功能: {', '.join(data.get('features', []))}")
        return True
    except Exception as e:
        print(f"❌ 服务异常: {e}")
        return False

def test_contextual_advice():
    """测试决策前查询学习记录"""
    print("\n🔍 测试决策前查询学习记录...")
    
    test_cases = [
        {
            "name": "提醒时间相关",
            "context": "用户询问提醒时间",
            "area": "schedule"
        },
        {
            "name": "运动计划相关",
            "context": "用户状态不佳，需要调整运动",
            "area": "goal"
        }
    ]
    
    for case in test_cases:
        print(f"\n  测试: {case['name']}")
        payload = {
            "function_name": "get_contextual_advice",
            "arguments": {
                "context": case["context"],
                "area": case["area"]
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/tools/get_contextual_advice",
                json=payload,
                timeout=5
            )
            result = response.json()
            
            if result.get("status") == "success":
                data = result["result"]
                if data.get("has_learnings"):
                    print(f"    ✅ 找到 {len(data.get('learnings', []))} 条相关学习")
                    print(f"    💡 建议: {data.get('advice', '')[:60]}...")
                else:
                    print(f"    ℹ️  暂无相关学习记录")
            else:
                print(f"    ❌ 查询失败: {result.get('result', {}).get('error', 'unknown')}")
        except Exception as e:
            print(f"    ❌ 请求失败: {e}")

def test_auto_promote_dry_run():
    """测试自动晋升（试运行）"""
    print("\n🚀 测试自动晋升（试运行模式）...")
    
    payload = {
        "function_name": "auto_promote_learnings",
        "arguments": {
            "dry_run": True
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/auto_promote_learnings",
            json=payload,
            timeout=10
        )
        result = response.json()
        
        if result.get("status") == "success":
            data = result["result"]
            print(f"  ✅ 扫描完成")
            print(f"  📊 总记录: {data.get('total_scanned', 0)}")
            print(f"  📝 可晋升: {data.get('promotable_count', 0)}")
            
            promoted = data.get('promoted', [])
            if promoted:
                print(f"  ⬆️  晋升列表:")
                for item in promoted:
                    print(f"     - {item.get('id')}: {item.get('summary', '')[:40]}...")
            else:
                print(f"  ⏭️  本次无晋升")
        else:
            print(f"  ❌ 失败: {result.get('result', {}).get('error', 'unknown')}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

def test_adjustment_with_learning():
    """测试动态调整（带学习记录查询）"""
    print("\n🎯 测试动态调整方案（决策前查询学习）...")
    
    payload = {
        "function_name": "generate_dynamic_adjustment",
        "arguments": {
            "current_plan": {
                "time": "19:00",
                "event": "跑步30分钟"
            },
            "user_status": {
                "energy_level": "low"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/generate_dynamic_adjustment",
            json=payload,
            timeout=5
        )
        result = response.json()
        
        if result.get("status") == "success":
            data = result["result"]
            print(f"  ✅ 调整方案生成成功")
            print(f"  📋 调整: {data.get('adjusted_tasks', [{}])[0].get('new_task', 'N/A')}")
            print(f"  📝 原因: {data.get('reason', 'N/A')[:80]}...")
            print(f"  🧠 引用学习: {data.get('referenced_learnings', 0)} 条")
            print(f"  💡 有历史学习: {'是' if data.get('has_contextual_learning') else '否'}")
        else:
            print(f"  ❌ 失败: {result.get('result', {}).get('error', 'unknown')}")
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 CogniMate 决策前学习 + 自动晋升 功能测试")
    print("=" * 60)
    
    if not test_health():
        print("\n⚠️  请先启动服务器: ./server/start.sh")
        return
    
    # 运行测试
    test_contextual_advice()
    test_auto_promote_dry_run()
    test_adjustment_with_learning()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 决策前查询: 在生成建议前自动查询相关学习")
    print("   - 自动晋升: 运行 ./server/promotion.py --dry-run 查看")
    print("   - 也可通过 API POST /tools/auto_promote_learnings 触发")

if __name__ == "__main__":
    main()
