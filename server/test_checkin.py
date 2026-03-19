#!/usr/bin/env python3
"""
打卡系统测试用例
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def test_create_checkin():
    """测试创建打卡记录"""
    print("\n🧪 测试创建打卡记录...")
    
    scheduled_time = (datetime.now() + timedelta(hours=1)).isoformat()
    
    response = requests.post(f"{BASE_URL}/checkin", json={
        "type": "water",
        "title": "下午喝水提醒",
        "scheduled_time": scheduled_time,
        "note": "测试打卡"
    })
    
    result = response.json()
    assert result["status"] == "success", f"创建失败: {result}"
    print(f"✅ 创建打卡成功，ID: {result['result']['checkin_id']}")
    return result["result"]["checkin_id"]


def test_update_checkin(checkin_id):
    """测试更新打卡状态"""
    print(f"\n🧪 测试更新打卡状态 (ID: {checkin_id})...")
    
    actual_time = datetime.now().isoformat()
    
    response = requests.put(f"{BASE_URL}/checkin/{checkin_id}", json={
        "status": "completed",
        "actual_time": actual_time,
        "note": "已喝500ml温水"
    })
    
    result = response.json()
    assert result["status"] == "success", f"更新失败: {result}"
    print(f"✅ 更新成功: {result['result']['message']}")


def test_today_checkins():
    """测试获取今日打卡列表"""
    print("\n🧪 测试获取今日打卡列表...")
    
    response = requests.get(f"{BASE_URL}/checkin/today")
    result = response.json()
    
    assert result["status"] == "success", f"获取失败: {result}"
    print(f"✅ 今日打卡数: {result['result']['count']}")
    for checkin in result['result']['checkins']:
        print(f"   - [{checkin['status']}] {checkin['title']} ({checkin['type']})")


def test_checkin_stats():
    """测试获取打卡统计"""
    print("\n🧪 测试获取打卡统计...")
    
    response = requests.get(f"{BASE_URL}/checkin/stats?days=7")
    result = response.json()
    
    assert result["status"] == "success", f"获取统计失败: {result}"
    stats = result["result"]
    
    print(f"✅ 统计信息:")
    print(f"   总打卡数: {stats['total']}")
    print(f"   已完成: {stats['completed']}")
    print(f"   完成率: {stats['completion_rate']}%")
    print(f"   当前连续: {stats['current_streak']} 天")
    print(f"   最长连续: {stats['longest_streak']} 天")
    
    if stats.get('by_type'):
        print(f"   按类型统计:")
        for type_name, type_stats in stats['by_type'].items():
            print(f"     - {type_name}: {type_stats['rate']}% ({type_stats['completed']}/{type_stats['total']})")


def test_parse_response():
    """测试自动解析用户回复"""
    print("\n🧪 测试自动解析用户回复...")
    
    test_cases = [
        ("喝了", "completed"),
        ("✅", "completed"),
        ("完成", "completed"),
        ("没喝", "missed"),
        ("❌", "missed"),
        ("忘了", "missed"),
        ("跳过", "skipped"),
        ("不需要", "skipped"),
        ("今天天气真好", "pending"),  # 无法识别的回复
    ]
    
    for user_input, expected_status in test_cases:
        response = requests.post(f"{BASE_URL}/checkin/parse", json={
            "user_input": user_input
        })
        
        result = response.json()
        assert result["status"] == "success", f"解析失败: {result}"
        
        actual_status = result["result"]["status"]
        confidence = result["result"]["confidence"]
        
        status_match = "✅" if actual_status == expected_status else "❌"
        print(f"   {status_match} '{user_input}' -> {actual_status} (confidence: {confidence})")
        
        assert actual_status == expected_status, f"期望 {expected_status} 但得到 {actual_status}"
    
    print(f"✅ 所有解析测试通过！")


def test_parse_and_update():
    """测试解析并自动更新"""
    print("\n🧪 测试解析并自动更新打卡状态...")
    
    # 先创建一个新的打卡记录
    scheduled_time = datetime.now().isoformat()
    create_response = requests.post(f"{BASE_URL}/checkin", json={
        "type": "exercise",
        "title": "运动打卡",
        "scheduled_time": scheduled_time
    })
    
    checkin_id = create_response.json()["result"]["checkin_id"]
    
    # 测试解析并更新
    response = requests.post(f"{BASE_URL}/checkin/parse", json={
        "user_input": "刚刚完成了",
        "checkin_id": checkin_id
    })
    
    result = response.json()
    assert result["status"] == "success", f"失败: {result}"
    assert result["result"]["updated"] == True, "应该自动更新"
    assert result["result"]["status"] == "completed", "应该识别为completed"
    
    print(f"✅ 自动更新成功: 打卡 {checkin_id} 状态更新为 {result['result']['status']}")


def test_create_from_reminder():
    """测试从提醒创建打卡记录"""
    print("\n🧪 测试从提醒创建打卡记录...")
    
    response = requests.post(f"{BASE_URL}/tools/create_checkin_from_reminder", json={
        "reminder_type": "water",
        "scheduled_time": datetime.now().isoformat(),
        "message": "该喝水了！记得每天保持充足水分"
    })
    
    result = response.json()
    assert result["status"] == "success", f"失败: {result}"
    print(f"✅ 从提醒创建成功，ID: {result['result']['checkin_id']}")


def test_get_pending_checkins():
    """测试获取待处理打卡"""
    print("\n🧪 测试获取待处理打卡...")
    
    response = requests.post(f"{BASE_URL}/tools/get_pending_checkins", json={
        "arguments": {
            "user_id": "default",
            "limit": 5
        }
    })
    
    result = response.json()
    assert result["status"] == "success", f"失败: {result}"
    
    pending = result["result"]
    print(f"✅ 待处理打卡: {pending['count']} 个")
    
    if pending["has_pending"]:
        for checkin in pending["pending_checkins"]:
            print(f"   - [{checkin['id']}] {checkin['title']} ({checkin['type']})")
    
    return pending["pending_checkins"]


def test_multiple_checkins():
    """测试创建多个打卡并获取统计"""
    print("\n🧪 测试批量打卡...")
    
    types = ["water", "exercise", "work", "study"]
    ids = []
    
    # 创建多个打卡
    for i, checkin_type in enumerate(types):
        scheduled_time = (datetime.now() + timedelta(minutes=i*30)).isoformat()
        response = requests.post(f"{BASE_URL}/checkin", json={
            "type": checkin_type,
            "title": f"{checkin_type} 打卡",
            "scheduled_time": scheduled_time
        })
        ids.append(response.json()["result"]["checkin_id"])
    
    print(f"✅ 创建了 {len(ids)} 个打卡记录")
    
    # 更新其中一些为完成状态
    for checkin_id in ids[:2]:
        requests.put(f"{BASE_URL}/checkin/{checkin_id}", json={
            "status": "completed",
            "actual_time": datetime.now().isoformat()
        })
    
    # 更新一个为跳过
    requests.put(f"{BASE_URL}/checkin/{ids[2]}", json={
        "status": "skipped"
    })
    
    # 获取统计
    response = requests.get(f"{BASE_URL}/checkin/stats?days=1")
    stats = response.json()["result"]
    
    print(f"✅ 批量测试统计:")
    print(f"   总计: {stats['total']}")
    print(f"   完成: {stats['completed']}")
    print(f"   跳过: {stats['skipped']}")
    print(f"   待处理: {stats['pending']}")
    print(f"   完成率: {stats['completion_rate']}%")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 CogniMate 打卡系统测试套件")
    print("=" * 60)
    
    try:
        # 基础CRUD测试
        checkin_id = test_create_checkin()
        test_update_checkin(checkin_id)
        test_today_checkins()
        
        # 解析功能测试
        test_parse_response()
        test_parse_and_update()
        
        # 集成测试
        test_create_from_reminder()
        test_get_pending_checkins()
        
        # 统计测试
        test_checkin_stats()
        test_multiple_checkins()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        raise


if __name__ == "__main__":
    # 等待服务器启动
    import time
    print("⏳ 等待服务器启动...")
    time.sleep(2)
    
    run_all_tests()
