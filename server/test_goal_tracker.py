#!/usr/bin/env python3
"""
测试目标追踪功能
"""

import sys
sys.path.append('/root/.openclaw/workspace-cognimate/server')

from goal_tracker import GoalTracker, get_tracker

def test_goal_tracker():
    print("🧪 测试目标追踪功能...\n")
    
    tracker = get_tracker()
    
    # 1. 测试创建目标
    print("1. 创建测试目标...")
    goal_id = tracker.create_goal(
        name="测试目标：学会游泳",
        target_value="4周内学会基础游泳",
        deadline="2026-04-14"
    )
    print(f"   ✅ 目标创建成功，ID: {goal_id}")
    
    # 2. 测试更新进度
    print("\n2. 更新目标进度...")
    tracker.update_goal_progress(
        goal_id=goal_id,
        current_value="已完成第1次游泳，30分钟",
        progress_percent=25,
        note="第一天感觉不错"
    )
    print("   ✅ 进度更新成功")
    
    # 3. 测试获取目标
    print("\n3. 获取目标详情...")
    goal = tracker.get_goal(goal_id)
    print(f"   目标名称: {goal['name']}")
    print(f"   当前进度: {goal['progress_percent']}%")
    print(f"   当前状态: {goal['current_value']}")
    
    # 4. 测试打卡
    print("\n4. 记录今日打卡...")
    tracker.checkin(
        date="2026-03-14",
        completed=True,
        goal_id=goal_id,
        note="游泳30分钟，第1天"
    )
    print("   ✅ 打卡记录成功")
    
    # 5. 测试生成每日复盘
    print("\n5. 生成每日复盘...")
    review = tracker.generate_daily_review("2026-03-14")
    print(f"   日期: {review['date']}")
    print(f"   明日日期: {review['tomorrow']}")
    print(f"   今日完成率: {review['today_completion_rate']}%")
    print(f"   活跃目标数: {len(review['goals'])}")
    
    # 6. 测试统计
    print("\n6. 获取目标统计...")
    stats = tracker.get_completion_stats(goal_id, days=7)
    print(f"   总天数: {stats['total_days']}")
    print(f"   完成天数: {stats['completed_days']}")
    print(f"   完成率: {stats['completion_rate']}%")
    print(f"   连续打卡: {stats['streak']}天")
    
    print("\n✅ 所有测试通过！")

if __name__ == "__main__":
    test_goal_tracker()
