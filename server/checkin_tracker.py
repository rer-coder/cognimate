#!/usr/bin/env python3
"""
CogniMate 打卡追踪模块
处理打卡记录的创建、更新、统计和解析
"""

import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import os

DB_PATH = '/root/.openclaw/workspace-cognimate/cognimate.db'


class CheckinStatus(Enum):
    """打卡状态枚举"""
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    SKIPPED = "skipped"


class CheckinType(Enum):
    """打卡类型枚举"""
    WATER = "water"
    EXERCISE = "exercise"
    WORK = "work"
    STUDY = "study"
    SLEEP = "sleep"
    MEDICINE = "medicine"
    CUSTOM = "custom"


@dataclass
class CheckinRecord:
    """打卡记录数据类"""
    id: int
    user_id: str
    type: str
    title: str
    scheduled_time: datetime
    actual_time: Optional[datetime]
    status: str
    note: str
    created_at: datetime
    updated_at: datetime


class CheckinTracker:
    """打卡追踪器"""
    
    # 自然语言状态识别模式
    STATUS_PATTERNS = {
        CheckinStatus.COMPLETED: [
            r'喝[了过]?', r'完成[了]?', r'做[了过]?', r'✅', r'✓', r'☑️', 
            r'[做搞]完[了]?', r'ok', r'好的', r'收到', r'明白', r'好[的呀]?',
            r'已[经]?[喝吃做]', r'弄好[了]?', r'搞定', r'yes', r'嗯', r'对',
            r'[做搞]了', r'正常', r'按时', r'准时'
        ],
        CheckinStatus.MISSED: [
            r'没[喝吃做]', r'忘[了记]', r'❌', r'✗', r'错过[了]?',
            r'来?不及[了]?', r'没[有能]?[喝吃做]?', r'没顾上', r'no',
            r'没有', r'忘了', r'忘记', r'忙', r'没空', r'没[有]?时间',
            r'没做到', r'未完成', r'失败'
        ],
        CheckinStatus.SKIPPED: [
            r'跳过', r'不需要', r'取消', r'不用', r'作罢', r'算了',
            r'改天', r'下次', r'不必', r'免了', r'不[用]?[做搞]',
            r'略过', r'pass', r'跳过', r'不[需要]'
        ]
    }
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_checkin(
        self, 
        checkin_type: str, 
        scheduled_time: datetime,
        user_id: str = "default",
        title: str = "",
        note: str = ""
    ) -> int:
        """
        创建新的打卡记录
        
        Args:
            checkin_type: 打卡类型 (water, exercise, work等)
            scheduled_time: 计划时间
            user_id: 用户ID
            title: 打卡标题
            note: 备注
            
        Returns:
            打卡记录ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO checkins 
            (user_id, type, title, scheduled_time, status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, 
            checkin_type, 
            title or self._get_default_title(checkin_type),
            scheduled_time.isoformat(),
            CheckinStatus.PENDING.value,
            note
        ))
        
        checkin_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return checkin_id
    
    def update_checkin_status(
        self, 
        checkin_id: int, 
        status: str,
        actual_time: Optional[datetime] = None,
        note: str = ""
    ) -> bool:
        """
        更新打卡状态
        
        Args:
            checkin_id: 打卡记录ID
            status: 新状态 (pending, completed, missed, skipped)
            actual_time: 实际完成时间
            note: 备注
            
        Returns:
            是否更新成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 检查记录是否存在
        cursor.execute('SELECT id FROM checkins WHERE id = ?', (checkin_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        # 构建更新语句
        updates = ['status = ?']
        params = [status]
        
        if actual_time:
            updates.append('actual_time = ?')
            params.append(actual_time.isoformat())
        
        if note:
            updates.append('note = ?')
            params.append(note)
        
        params.append(checkin_id)
        
        cursor.execute(f'''
            UPDATE checkins 
            SET {', '.join(updates)}
            WHERE id = ?
        ''', params)
        
        conn.commit()
        conn.close()
        
        # 更新统计
        self._update_daily_stats(
            datetime.now().strftime('%Y-%m-%d')
        )
        
        return True
    
    def parse_user_response(self, user_input: str) -> Dict:
        """
        解析用户回复，识别打卡状态
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            解析结果字典
        """
        user_input = user_input.lower().strip()
        
        for status, patterns in self.STATUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return {
                        "status": status.value,
                        "confidence": "high",
                        "matched_pattern": pattern,
                        "original_text": user_input
                    }
        
        # 如果没有匹配到任何模式，返回pending（需要进一步确认）
        return {
            "status": CheckinStatus.PENDING.value,
            "confidence": "low",
            "matched_pattern": None,
            "original_text": user_input,
            "message": "无法自动识别状态，请明确回复'完成'、'没做'或'跳过'"
        }
    
    def get_today_checkins(
        self, 
        user_id: str = "default"
    ) -> List[Dict]:
        """
        获取今日打卡列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            今日打卡记录列表
        """
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM checkins 
            WHERE user_id = ? 
            AND scheduled_time >= ? 
            AND scheduled_time < ?
            ORDER BY scheduled_time
        ''', (user_id, today, tomorrow))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_checkin_stats(
        self, 
        days: int = 7,
        user_id: str = "default"
    ) -> Dict:
        """
        获取打卡统计信息
        
        Args:
            days: 统计天数（最近N天）
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 总体统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM checkins 
            WHERE user_id = ? 
            AND date(scheduled_time) >= date(?)
            AND date(scheduled_time) <= date(?)
        ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        row = cursor.fetchone()
        stats = {
            "period_days": days,
            "total": row['total'] or 0,
            "completed": row['completed'] or 0,
            "missed": row['missed'] or 0,
            "skipped": row['skipped'] or 0,
            "pending": row['pending'] or 0,
            "completion_rate": round(
                (row['completed'] or 0) / max(row['total'] or 1, 1) * 100, 2
            )
        }
        
        # 按类型统计
        cursor.execute('''
            SELECT 
                type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM checkins 
            WHERE user_id = ? 
            AND date(scheduled_time) >= date(?)
            AND date(scheduled_time) <= date(?)
            GROUP BY type
        ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        stats['by_type'] = {
            row['type']: {
                'total': row['count'],
                'completed': row['completed'],
                'rate': round(row['completed'] / max(row['count'], 1) * 100, 2)
            }
            for row in cursor.fetchall()
        }
        
        # 计算连续打卡天数
        stats['current_streak'] = self._calculate_streak(user_id)
        stats['longest_streak'] = self._calculate_longest_streak(user_id)
        
        conn.close()
        
        return stats
    
    def get_pending_checkins(
        self, 
        user_id: str = "default",
        limit: int = 10
    ) -> List[Dict]:
        """
        获取待处理的打卡记录
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            待处理打卡记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM checkins 
            WHERE user_id = ? 
            AND status = 'pending'
            AND scheduled_time <= datetime('now', '+1 hour')
            ORDER BY scheduled_time DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def create_checkin_from_reminder(
        self, 
        reminder_type: str,
        scheduled_time: datetime,
        message: str,
        user_id: str = "default"
    ) -> int:
        """
        从提醒创建打卡记录
        
        Args:
            reminder_type: 提醒类型
            scheduled_time: 计划时间
            message: 提醒消息
            user_id: 用户ID
            
        Returns:
            打卡记录ID
        """
        title = self._extract_title_from_message(message)
        return self.create_checkin(
            checkin_type=reminder_type,
            scheduled_time=scheduled_time,
            user_id=user_id,
            title=title,
            note=f"自动创建，来源: {message[:50]}..."
        )
    
    def _get_default_title(self, checkin_type: str) -> str:
        """获取默认标题"""
        titles = {
            "water": "喝水打卡",
            "exercise": "运动打卡",
            "work": "工作打卡",
            "study": "学习打卡",
            "sleep": "睡眠打卡",
            "medicine": "吃药打卡",
            "custom": "自定义打卡"
        }
        return titles.get(checkin_type, "打卡")
    
    def _extract_title_from_message(self, message: str) -> str:
        """从消息中提取标题"""
        # 简单的标题提取逻辑
        lines = message.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            # 移除常见的提醒前缀
            prefixes = ['提醒：', '【提醒】', '📢', '⏰', '📅']
            for prefix in prefixes:
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix):].strip()
            return first_line[:50]  # 限制长度
        return "打卡提醒"
    
    def _calculate_streak(self, user_id: str = "default") -> int:
        """计算当前连续打卡天数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        streak = 0
        today = datetime.now().date()
        
        # 从昨天开始往前检查
        for i in range(365):  # 最多检查一年
            check_date = today - timedelta(days=i+1)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM checkins 
                WHERE user_id = ? 
                AND date(scheduled_time) = date(?)
            ''', (user_id, check_date.strftime('%Y-%m-%d')))
            
            row = cursor.fetchone()
            total = row['total'] or 0
            completed = row['completed'] or 0
            
            if total == 0:
                # 这一天没有打卡记录，跳过
                continue
            
            if completed > 0 and completed >= total * 0.5:  # 完成率>=50%
                streak += 1
            else:
                break
        
        conn.close()
        return streak
    
    def _calculate_longest_streak(self, user_id: str = "default") -> int:
        """计算历史最长连续打卡天数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 获取所有有打卡记录的日期
        cursor.execute('''
            SELECT DISTINCT date(scheduled_time) as check_date
            FROM checkins 
            WHERE user_id = ?
            ORDER BY check_date
        ''', (user_id,))
        
        dates = [row['check_date'] for row in cursor.fetchall()]
        
        if not dates:
            conn.close()
            return 0
        
        # 计算每天是否达标（完成率>=50%）
        valid_dates = []
        for date_str in dates:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM checkins 
                WHERE user_id = ? 
                AND date(scheduled_time) = date(?)
            ''', (user_id, date_str))
            
            row = cursor.fetchone()
            total = row['total'] or 0
            completed = row['completed'] or 0
            
            if completed >= total * 0.5:
                valid_dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
        
        conn.close()
        
        # 计算最长连续天数
        if not valid_dates:
            return 0
        
        longest = 1
        current = 1
        
        for i in range(1, len(valid_dates)):
            if (valid_dates[i] - valid_dates[i-1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        
        return longest
    
    def _update_daily_stats(self, date: str):
        """更新每日统计（内部方法）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 计算当天的统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
            FROM checkins 
            WHERE date(scheduled_time) = date(?)
        ''', (date,))
        
        row = cursor.fetchone()
        total = row['total'] or 0
        completed = row['completed'] or 0
        missed = row['missed'] or 0
        skipped = row['skipped'] or 0
        rate = round(completed / max(total, 1) * 100, 2)
        
        # 更新或插入统计记录
        cursor.execute('''
            INSERT INTO checkin_stats 
            (user_id, date, total_count, completed_count, missed_count, skipped_count, completion_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
            total_count = excluded.total_count,
            completed_count = excluded.completed_count,
            missed_count = excluded.missed_count,
            skipped_count = excluded.skipped_count,
            completion_rate = excluded.completion_rate,
            updated_at = CURRENT_TIMESTAMP
        ''', ("default", date, total, completed, missed, skipped, rate))
        
        conn.commit()
        conn.close()
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将数据库行转换为字典"""
        return {
            "id": row['id'],
            "user_id": row['user_id'],
            "type": row['type'],
            "title": row['title'],
            "scheduled_time": row['scheduled_time'],
            "actual_time": row['actual_time'],
            "status": row['status'],
            "note": row['note'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }


# 单例实例
checkin_tracker = CheckinTracker()


def get_tracker() -> CheckinTracker:
    """获取打卡追踪器实例"""
    return checkin_tracker
