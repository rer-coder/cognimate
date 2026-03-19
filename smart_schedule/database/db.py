"""
CogniMate 智能日程管理系统 - 数据库操作模块
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str = "smart_schedule.db"):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # ==================== 日程操作 ====================
    
    def create_schedule(self, schedule_data: Dict) -> int:
        """创建新日程"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            placeholders = []
            
            for key, value in schedule_data.items():
                if value is not None:
                    fields.append(key)
                    values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
                    placeholders.append('?')
            
            sql = f"INSERT INTO schedules ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def get_schedule(self, schedule_id: int) -> Optional[Dict]:
        """获取单个日程"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM schedules WHERE id = ? AND deleted_at IS NULL", (schedule_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_schedules_by_date_range(self, start: datetime, end: datetime, 
                                    category: str = None) -> List[Dict]:
        """获取日期范围内的日程"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = """
                SELECT * FROM schedules 
                WHERE deleted_at IS NULL 
                AND status = 'active'
                AND (
                    (start_time >= ? AND start_time < ?) OR
                    (end_time > ? AND end_time <= ?) OR
                    (start_time <= ? AND end_time >= ?)
                )
            """
            params = [start, end, start, end, start, end]
            
            if category:
                sql += " AND category = ?"
                params.append(category)
            
            sql += " ORDER BY start_time"
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_today_schedules(self) -> List[Dict]:
        """获取今日日程"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.get_schedules_by_date_range(today, tomorrow)
    
    def update_schedule(self, schedule_id: int, updates: Dict) -> bool:
        """更新日程"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            set_clause = []
            values = []
            
            for key, value in updates.items():
                if key != 'id':
                    set_clause.append(f"{key} = ?")
                    values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            
            set_clause.append("updated_at = ?")
            values.append(datetime.now())
            values.append(schedule_id)
            
            sql = f"UPDATE schedules SET {', '.join(set_clause)} WHERE id = ?"
            cursor.execute(sql, values)
            return cursor.rowcount > 0
    
    def delete_schedule(self, schedule_id: int, soft: bool = True) -> bool:
        """删除日程（支持软删除）"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if soft:
                cursor.execute(
                    "UPDATE schedules SET deleted_at = ?, status = 'deleted' WHERE id = ?",
                    (datetime.now(), schedule_id)
                )
            else:
                cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
            return cursor.rowcount > 0
    
    # ==================== 目标操作 ====================
    
    def create_goal(self, goal_data: Dict) -> int:
        """创建目标"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            placeholders = []
            
            for key, value in goal_data.items():
                if value is not None:
                    fields.append(key)
                    values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
                    placeholders.append('?')
            
            sql = f"INSERT INTO goals ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def get_active_goals(self) -> List[Dict]:
        """获取活跃目标"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM goals WHERE status = 'active' ORDER BY priority DESC, end_date"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 用户上下文操作 ====================
    
    def set_user_context(self, context_type: str, context_key: str, 
                         context_value: Any, valid_hours: int = 24):
        """设置用户上下文"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            valid_until = now + timedelta(hours=valid_hours)
            
            # 先使旧记录失效
            cursor.execute("""
                UPDATE user_context 
                SET valid_until = ? 
                WHERE context_type = ? AND context_key = ? AND valid_until > ?
            """, (now, context_type, context_key, now))
            
            # 插入新记录
            cursor.execute("""
                INSERT INTO user_context (context_type, context_key, context_value, valid_from, valid_until)
                VALUES (?, ?, ?, ?, ?)
            """, (context_type, context_key, json.dumps(context_value), now, valid_until))
            
            return cursor.lastrowid
    
    def get_user_context(self, context_type: str = None, 
                         context_key: str = None) -> List[Dict]:
        """获取用户上下文"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            
            sql = "SELECT * FROM user_context WHERE valid_from <= ? AND valid_until > ?"
            params = [now, now]
            
            if context_type:
                sql += " AND context_type = ?"
                params.append(context_type)
            if context_key:
                sql += " AND context_key = ?"
                params.append(context_key)
            
            sql += " ORDER BY created_at DESC"
            
            cursor.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                try:
                    data['context_value'] = json.loads(data['context_value'])
                except:
                    pass
                results.append(data)
            return results
    
    def get_current_location(self) -> Optional[str]:
        """获取当前位置"""
        contexts = self.get_user_context('location')
        if contexts:
            return contexts[0].get('context_value')
        return None
    
    # ==================== 变更历史操作 ====================
    
    def create_change_record(self, change_data: Dict) -> int:
        """创建变更记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            placeholders = []
            
            for key, value in change_data.items():
                if value is not None:
                    fields.append(key)
                    values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
                    placeholders.append('?')
            
            sql = f"INSERT INTO schedule_changes ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def get_pending_changes(self) -> List[Dict]:
        """获取待确认的变更"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM schedule_changes WHERE status = 'pending' ORDER BY created_at"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def confirm_change(self, change_id: int, user_confirmation: str) -> bool:
        """确认变更"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE schedule_changes 
                SET status = 'confirmed', user_confirmation = ?, confirmed_at = ?
                WHERE id = ?
            """, (user_confirmation, datetime.now(), change_id))
            return cursor.rowcount > 0
    
    def reject_change(self, change_id: int, reason: str) -> bool:
        """拒绝变更"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE schedule_changes 
                SET status = 'rejected', user_confirmation = ?
                WHERE id = ?
            """, (reason, change_id))
            return cursor.rowcount > 0
    
    def mark_change_applied(self, change_id: int) -> bool:
        """标记变更已应用"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE schedule_changes 
                SET status = 'applied', applied_at = ?
                WHERE id = ?
            """, (datetime.now(), change_id))
            return cursor.rowcount > 0
    
    # ==================== 位置规则操作 ====================
    
    def get_location_rules(self, location_key: str = None) -> List[Dict]:
        """获取位置规则"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if location_key:
                cursor.execute(
                    "SELECT * FROM location_rules WHERE location_key = ? AND active = 1",
                    (location_key,)
                )
            else:
                cursor.execute("SELECT * FROM location_rules WHERE active = 1")
            
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                try:
                    data['schedule_adjustments'] = json.loads(data['schedule_adjustments'])
                    data['affected_categories'] = data['affected_categories'].split(',') if data['affected_categories'] else []
                except:
                    pass
                results.append(data)
            return results
    
    # ==================== Cron同步日志 ====================
    
    def log_cron_sync(self, sync_data: Dict):
        """记录Cron同步日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cron_sync_log (sync_type, schedule_id, cron_expression, sync_status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                sync_data.get('sync_type'),
                sync_data.get('schedule_id'),
                sync_data.get('cron_expression'),
                sync_data.get('sync_status'),
                sync_data.get('error_message')
            ))
