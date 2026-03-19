#!/usr/bin/env python3
"""
CogniMate Agent - Goal Tracker
完整的目标追踪系统：进度记录、打卡、统计
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class GoalTracker:
    """目标追踪器 - 管理目标进度和每日打卡"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            workspace = os.getenv("OPENCLAW_WORKSPACE", "/root/.openclaw/workspace-cognimate")
            db_path = f"{workspace}/cognimate.db"
        self.db_path = db_path
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    # ============ 目标管理 ============
    
    def create_goal(self, name: str, target_value: str, deadline: str = None) -> int:
        """创建新目标"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO goals (title, description, target_date, progress, start_date)
            VALUES (?, ?, ?, 0, ?)
        ''', (name, target_value, deadline, datetime.now().strftime("%Y-%m-%d")))
        
        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return goal_id
    
    def update_goal_progress(self, goal_id: int, current_value: str, 
                            progress_percent: int, note: str = "") -> bool:
        """更新目标进度"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 更新目标表
        cursor.execute('''
            UPDATE goals 
            SET current_value = ?, progress = ?, progress_percent = ?
            WHERE id = ?
        ''', (current_value, progress_percent, progress_percent, goal_id))
        
        # 记录进度历史
        cursor.execute('''
            INSERT INTO goal_progress (goal_id, progress_percent, current_value, note)
            VALUES (?, ?, ?, ?)
        ''', (goal_id, progress_percent, current_value, note))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_goal(self, goal_id: int) -> Optional[Dict]:
        """获取目标详情"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM goals WHERE id = ?
        ''', (goal_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "name": row[2],  # title as name
                "target_value": row[3],  # description as target_value
                "current_value": row[9] if len(row) > 9 else "",
                "deadline": row[4],  # target_date as deadline
                "status": "active" if row[5] == 0 else "completed",  # progress
                "progress_percent": row[10] if len(row) > 10 else int(row[5]) if row[5] else 0,
                "start_date": row[11] if len(row) > 11 else row[7]  # created_at or start_date
            }
        return None
    
    def get_all_goals(self, status: str = "active") -> List[Dict]:
        """获取所有目标"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 使用progress判断状态
        if status == "active":
            cursor.execute('''
                SELECT * FROM goals WHERE progress < 100
            ''')
        else:
            cursor.execute('''
                SELECT * FROM goals WHERE progress >= 100
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        goals = []
        for row in rows:
            goals.append({
                "id": row[0],
                "name": row[2],  # title
                "target_value": row[3],  # description
                "current_value": row[9] if len(row) > 9 else "",
                "deadline": row[4],  # target_date
                "status": "active" if row[5] < 100 else "completed",
                "progress_percent": row[10] if len(row) > 10 else int(row[5]) if row[5] else 0,
                "start_date": row[11] if len(row) > 11 else row[7]
            })
        
        return goals
    
    # ============ 打卡记录 ============
    
    def checkin(self, date: str, completed: bool, schedule_id: int = None,
                goal_id: int = None, note: str = "") -> bool:
        """记录每日打卡"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO daily_checkins (date, schedule_id, goal_id, completed, note)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, schedule_id, goal_id, completed, note))
        
        # 如果关联了日程，更新日程完成状态
        if schedule_id:
            cursor.execute('''
                UPDATE schedules 
                SET completed = ?, completed_at = ?
                WHERE id = ?
            ''', (completed, datetime.now().isoformat() if completed else None, schedule_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_checkins_by_date(self, date: str) -> List[Dict]:
        """获取某日所有打卡记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, g.name as goal_name, s.event as schedule_event
            FROM daily_checkins c
            LEFT JOIN goals g ON c.goal_id = g.id
            LEFT JOIN schedules s ON c.schedule_id = s.id
            WHERE c.date = ?
        ''', (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        checkins = []
        for row in rows:
            checkins.append({
                "id": row[0],
                "date": row[1],
                "goal_id": row[2],
                "schedule_id": row[3],
                "completed": row[4],
                "note": row[5],
                "created_at": row[6],
                "goal_name": row[7],
                "schedule_event": row[8]
            })
        
        return checkins
    
    # ============ 统计查询 ============
    
    def get_completion_stats(self, goal_id: int, days: int = 7) -> Dict:
        """获取目标完成统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 查询最近N天的打卡记录
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cursor.execute('''
            SELECT date, completed FROM daily_checkins
            WHERE goal_id = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        ''', (goal_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        rows = cursor.fetchall()
        conn.close()
        
        total = len(rows)
        completed = sum(1 for row in rows if row[1])
        
        return {
            "total_days": total,
            "completed_days": completed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "streak": self._calculate_streak(rows)
        }
    
    def _calculate_streak(self, rows: List[Tuple]) -> int:
        """计算连续完成天数"""
        if not rows:
            return 0
        
        streak = 0
        for row in rows:
            if row[1]:  # completed
                streak += 1
            else:
                break
        
        return streak
    
    def get_goal_progress_history(self, goal_id: int, limit: int = 10) -> List[Dict]:
        """获取目标进度历史"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM goal_progress
            WHERE goal_id = ?
            ORDER BY recorded_at DESC
            LIMIT ?
        ''', (goal_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "progress_percent": row[2],
                "current_value": row[3],
                "note": row[4],
                "recorded_at": row[5]
            })
        
        return history
    
    # ============ 每日复盘生成 ============
    
    def generate_daily_review(self, date: str = None) -> Dict:
        """生成每日复盘报告"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 获取明日日程（根据start_time LIKE匹配日期）
        tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, g.title as goal_name, g.progress as goal_progress
            FROM schedules s
            LEFT JOIN goals g ON s.related_goal_id = g.id
            WHERE s.start_time LIKE ? || '%'
            ORDER BY s.start_time
        ''', (tomorrow,))
        
        rows = cursor.fetchall()
        
        schedules = []
        for row in rows:
            schedules.append({
                "id": row[0],
                "time": row[2],
                "event": row[3],
                "completed": row[7] if len(row) > 7 else False,
                "goal_name": row[10],
                "goal_progress": row[11] if len(row) > 11 else 0
            })
        
        # 2. 获取今日打卡记录
        cursor.execute('''
            SELECT c.*, g.title as goal_name, s.event as schedule_event
            FROM daily_checkins c
            LEFT JOIN goals g ON c.goal_id = g.id
            LEFT JOIN schedules s ON c.schedule_id = s.id
            WHERE c.date = ?
        ''', (date,))
        
        rows = cursor.fetchall()
        today_checkins = []
        for row in rows:
            today_checkins.append({
                "completed": row[4],
                "note": row[5],
                "goal_name": row[7],
                "schedule_event": row[8]
            })
        
        # 3. 获取所有活跃目标
        cursor.execute('''
            SELECT * FROM goals WHERE progress < 100
        ''')
        
        rows = cursor.fetchall()
        goals = []
        for row in rows:
            goals.append({
                "id": row[0],
                "name": row[2],  # title
                "target_value": row[3],  # description
                "current_value": row[9] if len(row) > 9 else "",
                "progress_percent": row[10] if len(row) > 10 else int(row[5]) if row[5] else 0
            })
        
        conn.close()
        
        # 计算今日完成率
        total_today = len(today_checkins)
        completed_today = sum(1 for c in today_checkins if c["completed"])
        
        return {
            "date": date,
            "tomorrow": tomorrow,
            "today_completion_rate": round(completed_today / total_today * 100, 1) if total_today > 0 else 0,
            "today_checkins": today_checkins,
            "tomorrow_schedules": schedules,
            "goals": goals
        }


# 便捷函数
def get_tracker() -> GoalTracker:
    """获取追踪器实例"""
    return GoalTracker()


if __name__ == "__main__":
    # 测试
    tracker = get_tracker()
    
    # 测试生成每日复盘
    review = tracker.generate_daily_review()
    print("每日复盘测试:")
    print(f"今日完成率: {review['today_completion_rate']}%")
    print(f"明日待办数: {len(review['tomorrow_schedules'])}")
    print(f"活跃目标数: {len(review['goals'])}")
