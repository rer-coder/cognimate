# CogniMate 打卡系统集成模块
# 在主会话中处理用户消息时调用

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

BASE_URL = "http://localhost:8000"

def get_pending_checkins(user_id: str = "default", limit: int = 3) -> Dict[str, Any]:
    """获取待处理的打卡记录"""
    try:
        response = requests.post(
            f"{BASE_URL}/tools/get_pending_checkins",
            json={"arguments": {"user_id": user_id, "limit": limit}},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("result", {})
        return {"has_pending": False, "pending_checkins": []}
    except Exception as e:
        print(f"[Checkin] 获取待处理打卡失败: {e}")
        return {"has_pending": False, "pending_checkins": []}

def parse_checkin_response(user_input: str, checkin_id: Optional[int] = None) -> Dict[str, Any]:
    """解析用户打卡回复"""
    try:
        payload = {"user_input": user_input}
        if checkin_id:
            payload["checkin_id"] = checkin_id
            
        response = requests.post(
            f"{BASE_URL}/checkin/parse",
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("result", {})
        return {"status": "pending", "confidence": "low"}
    except Exception as e:
        print(f"[Checkin] 解析回复失败: {e}")
        return {"status": "pending", "confidence": "low"}

def is_checkin_reply(user_input: str, pending_checkins: list) -> bool:
    """
    判断用户输入是否为打卡回复
    
    判断依据：
    1. 有待处理的打卡
    2. 消息较短（<20字）
    3. 包含打卡关键词
    """
    if not pending_checkins:
        return False
    
    # 消息长度检查
    if len(user_input) > 30:
        return False
    
    # 打卡关键词
    checkin_keywords = [
        # 完成
        "喝了", "喝了", "完成", "做了", "搞定", "ok", "好", "收到", "明白",
        "✅", "✓", "☑️", "已", "刚刚", "正在", "马上",
        # 未完成
        "没喝", "忘了", "忘记", "错过", "来不及", "没做", "没有",
        "❌", "✗", "没空", "忙", "忘记了", "没完成",
        # 跳过
        "跳过", "不需要", "取消", "不用", "算了", "pass", "略过"
    ]
    
    user_lower = user_input.lower()
    for keyword in checkin_keywords:
        if keyword in user_lower:
            return True
    
    # 如果消息很短（<10字），也认为是打卡回复
    if len(user_input) < 10:
        return True
    
    return False

def handle_checkin_reply(user_input: str, user_id: str = "default") -> Optional[str]:
    """
    处理用户打卡回复
    
    返回：
    - 打卡确认消息（如果是打卡回复）
    - None（如果不是打卡回复，需要正常处理）
    """
    # 1. 获取待处理打卡
    pending = get_pending_checkins(user_id)
    
    if not pending.get("has_pending"):
        return None
    
    # 2. 判断是否为打卡回复
    if not is_checkin_reply(user_input, pending["pending_checkins"]):
        return None
    
    # 3. 获取最新的待处理打卡
    latest_checkin = pending["pending_checkins"][0]
    checkin_id = latest_checkin["id"]
    checkin_title = latest_checkin.get("title", "打卡")
    
    # 4. 解析用户回复
    result = parse_checkin_response(user_input, checkin_id)
    
    # 5. 根据解析结果生成回复
    status = result.get("status", "pending")
    confidence = result.get("confidence", "low")
    
    status_map = {
        "completed": ("✅", "已完成"),
        "missed": ("❌", "未完成"),
        "skipped": ("⏭️", "已跳过"),
        "pending": ("⏳", "待确认")
    }
    
    emoji, status_text = status_map.get(status, ("❓", "状态不明"))
    
    if confidence == "high":
        # 高置信度，确认已记录
        responses = {
            "completed": [
                f"{emoji} 已记录！{checkin_title}完成！继续保持 💪",
                f"{emoji} 收到！{checkin_title}打卡成功！你真棒 👍",
                f"{emoji} 已确认！{checkin_title}完成记录 ✓"
            ],
            "missed": [
                f"{emoji} 收到，已记录{checkin_title}未完成。没关系，下次记得哦 😊",
                f"{emoji} 已记录。下次记得按时完成呀 💪",
                f"{emoji} 收到，偶尔一次没关系，明天继续加油！"
            ],
            "skipped": [
                f"{emoji} 已跳过本次{checkin_title}。需要调整提醒时间吗？",
                f"{emoji} 收到，已跳过。下次需要记得告诉我哦 😊"
            ],
            "pending": [
                f"不太确定你的意思呢 😅 请告诉我'完成'、'没做'或'跳过'好吗？"
            ]
        }
        import random
        return random.choice(responses.get(status, responses["pending"]))
    else:
        # 低置信度，请求确认
        return (
            f"收到你的回复，但不太确定状态呢 🤔\n"
            f"请明确告诉我：\n"
            f"• ✅ 完成 / 喝了 / 做了\n"
            f"• ❌ 没完成 / 忘了 / 没做\n"
            f"• ⏭️ 跳过 / 不需要"
        )

def get_today_checkin_summary(user_id: str = "default") -> str:
    """获取今日打卡汇总"""
    try:
        response = requests.get(
            f"{BASE_URL}/checkin/today",
            params={"user_id": user_id},
            timeout=5
        )
        if response.status_code != 200:
            return "暂时无法获取打卡数据"
        
        data = response.json().get("result", {})
        checkins = data.get("checkins", [])
        
        if not checkins:
            return "今日暂无打卡记录"
        
        # 统计
        total = len(checkins)
        completed = sum(1 for c in checkins if c["status"] == "completed")
        pending = sum(1 for c in checkins if c["status"] == "pending")
        missed = sum(1 for c in checkins if c["status"] == "missed")
        
        # 按类型分组
        by_type = {}
        for c in checkins:
            t = c.get("type", "other")
            if t not in by_type:
                by_type[t] = {"total": 0, "completed": 0}
            by_type[t]["total"] += 1
            if c["status"] == "completed":
                by_type[t]["completed"] += 1
        
        type_names = {
            "water": "💧 喝水",
            "exercise": "🏃 运动",
            "work": "💼 工作",
            "study": "📚 学习",
            "sleep": "😴 睡眠",
            "medicine": "💊 用药"
        }
        
        lines = [f"📊 今日打卡 ({completed}/{total} 完成)"]
        lines.append("")
        
        for t, stats in by_type.items():
            name = type_names.get(t, t)
            rate = stats["completed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            bar = "█" * int(rate / 10) + "░" * (10 - int(rate / 10))
            lines.append(f"{name}: {bar} {stats['completed']}/{stats['total']}")
        
        if pending > 0:
            lines.append(f"")
            lines.append(f"⏳ 待完成: {pending} 项")
        
        return "\n".join(lines)
        
    except Exception as e:
        print(f"[Checkin] 获取汇总失败: {e}")
        return "暂时无法获取打卡数据"

# 测试代码
if __name__ == "__main__":
    # 测试打卡回复处理
    test_cases = [
        "喝了",
        "完成",
        "忘了",
        "没喝",
        "跳过",
        "今天天气不错",  # 应该返回 None
    ]
    
    print("=== 测试打卡回复识别 ===")
    for msg in test_cases:
        result = handle_checkin_reply(msg)
        print(f"'{msg}' -> {result if result else '(非打卡回复)'}")