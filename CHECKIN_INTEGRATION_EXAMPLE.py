#!/usr/bin/env python3
"""
CogniMate 主会话打卡集成示例
在主会话中识别用户回复打卡并自动更新状态
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def is_checkin_reply(user_input: str, pending_checkins: list) -> bool:
    """
    判断用户消息是否为打卡回复
    
    判断逻辑:
    1. 有待处理打卡
    2. 消息在提醒发送后1小时内
    3. 消息较短 (<20字)
    """
    if not pending_checkins:
        return False
    
    # 检查最近一条待处理打卡的时间
    latest = pending_checkins[0]
    created_time = datetime.fromisoformat(latest["scheduled_time"].replace('Z', '+00:00'))
    time_diff = (datetime.now() - created_time).total_seconds()
    
    # 如果在1小时内且消息较短，认为是打卡回复
    if time_diff < 3600 and len(user_input) < 20:
        return True
    
    # 检查是否包含明显的打卡关键词
    checkin_keywords = ["喝", "完成", "做", "✅", "❌", "忘了", "跳过", "没做"]
    for keyword in checkin_keywords:
        if keyword in user_input:
            return True
    
    return False


def handle_user_message(user_input: str, user_id: str = "default") -> str:
    """
    处理用户消息的主函数（主会话集成点）
    
    Args:
        user_input: 用户输入消息
        user_id: 用户ID
        
    Returns:
        回复消息
    """
    
    # ===== 步骤1: 查询待处理打卡 =====
    response = requests.post(f"{BASE_URL}/tools/get_pending_checkins", json={
        "user_id": user_id,
        "limit": 5
    })
    
    pending_result = response.json()["result"]
    pending_checkins = pending_result.get("pending_checkins", [])
    
    # ===== 步骤2: 判断是否为打卡回复 =====
    if is_checkin_reply(user_input, pending_checkins):
        # 获取最新的待处理打卡
        latest_checkin = pending_checkins[0]
        
        # ===== 步骤3: 解析用户回复并自动更新 =====
        parse_response = requests.post(f"{BASE_URL}/checkin/parse", json={
            "user_input": user_input,
            "checkin_id": latest_checkin["id"]
        })
        
        parse_result = parse_response.json()["result"]
        
        if parse_result["confidence"] == "high":
            status = parse_result["status"]
            status_map = {
                "completed": "✅ 已完成",
                "missed": "❌ 未完成",
                "skipped": "⏭️ 已跳过",
                "pending": "⏳ 待处理"
            }
            
            return f"收到！已记录{latest_checkin['title']} - {status_map.get(status, status)}"
        else:
            # 无法自动识别，请求明确回复
            return "收到你的回复😊 不过我不太确定你的意思。请告诉我'完成'、'没做'或'跳过'好吗？"
    
    # ===== 步骤4: 普通消息处理（原有逻辑）=====
    # 这里调用原有的情感分析、日程查询等功能
    # ...
    
    return None  # 返回None表示不是打卡回复，需要走原有处理流程


def send_reminder_and_create_checkin(
    reminder_type: str, 
    message: str, 
    scheduled_time: datetime,
    user_id: str = "default"
) -> int:
    """
    发送提醒并自动创建打卡记录（提醒发送时调用）
    
    Args:
        reminder_type: 提醒类型 (water/exercise/work等)
        message: 提醒消息内容
        scheduled_time: 计划时间
        user_id: 用户ID
        
    Returns:
        打卡记录ID
    """
    # 先创建打卡记录
    response = requests.post(f"{BASE_URL}/tools/create_checkin_from_reminder", json={
        "reminder_type": reminder_type,
        "scheduled_time": scheduled_time.isoformat(),
        "message": message,
        "user_id": user_id
    })
    
    checkin_id = response.json()["result"]["checkin_id"]
    
    # 发送提醒消息给用户（实际实现需要调用飞书API）
    # send_feishu_message(user_id, message)
    
    return checkin_id


def get_daily_checkin_report(user_id: str = "default") -> str:
    """
    生成每日打卡报告
    
    Returns:
        格式化报告文本
    """
    # 获取今日打卡列表
    today_response = requests.get(f"{BASE_URL}/checkin/today?user_id={user_id}")
    today_data = today_response.json()["result"]
    
    # 获取统计
    stats_response = requests.get(f"{BASE_URL}/checkin/stats?days=7&user_id={user_id}")
    stats = stats_response.json()["result"]
    
    # 生成报告
    report = f"📊 **今日打卡报告** ({today_data['date']})\n\n"
    
    # 今日打卡列表
    completed = [c for c in today_data["checkins"] if c["status"] == "completed"]
    pending = [c for c in today_data["checkins"] if c["status"] == "pending"]
    missed = [c for c in today_data["checkins"] if c["status"] == "missed"]
    
    report += f"✅ 已完成: {len(completed)}/{len(today_data['checkins'])}\n"
    for c in completed:
        report += f"   ✓ {c['title']}\n"
    
    if pending:
        report += f"\n⏳ 待完成: {len(pending)}\n"
        for c in pending:
            report += f"   ○ {c['title']}\n"
    
    if missed:
        report += f"\n❌ 未完成: {len(missed)}\n"
        for c in missed:
            report += f"   ✗ {c['title']}\n"
    
    # 连续打卡
    report += f"\n🔥 连续打卡: {stats['current_streak']} 天"
    
    return report


# ============ 使用示例 ============

if __name__ == "__main__":
    print("=" * 60)
    print("CogniMate 打卡系统集成示例")
    print("=" * 60)
    
    # 示例1: 发送提醒并创建打卡
    print("\n📢 示例1: 发送喝水提醒")
    checkin_id = send_reminder_and_create_checkin(
        reminder_type="water",
        message="⏰ 该喝水了！记得保持充足水分哦~",
        scheduled_time=datetime.now()
    )
    print(f"已创建打卡记录 ID: {checkin_id}")
    
    # 示例2: 处理用户回复
    test_cases = [
        "喝了",           # completed
        "刚刚完成",       # completed
        "忘了",           # missed
        "今天太忙",       # missed (需要确认)
        "跳过吧",         # skipped
        "天气真好",       # 不是打卡回复
    ]
    
    print("\n💬 示例2: 处理用户回复")
    for user_input in test_cases:
        result = handle_user_message(user_input)
        if result:
            print(f"  用户: '{user_input}' -> CogniMate: {result}")
        else:
            print(f"  用户: '{user_input}' -> [非打卡回复，走正常流程]")
    
    # 示例3: 生成每日报告
    print("\n📊 示例3: 生成每日打卡报告")
    report = get_daily_checkin_report()
    print(report)
