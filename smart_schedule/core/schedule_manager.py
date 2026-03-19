"""
CogniMate 智能日程管理系统 - 日程管理器
整合所有核心组件，提供统一接口
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from database.db import Database
from core.change_detector import ChangeDetectionEngine, ScheduleChange, ChangeType
from core.impact_analyzer import ImpactAnalyzer, ImpactAnalysis
from core.report_generator import ReportGenerator, ChangeReport
from core.confirmation_parser import PartialConfirmationParser, ConfirmationType

class ScheduleManager:
    """
    日程管理器 - 核心控制器
    
    实现核心需求：
    1. 数据库为唯一真相源
    2. 变更检测与汇报机制
    3. 部分同意机制
    4. 位置感知
    """
    
    def __init__(self, db_path: str = "smart_schedule.db"):
        self.db = Database(db_path)
        self.change_detector = ChangeDetectionEngine(self.db)
        self.impact_analyzer = ImpactAnalyzer(self.db)
        self.report_generator = ReportGenerator()
        self.confirmation_parser = PartialConfirmationParser()
        
        # 临时存储待确认的变更
        self._pending_changes: Dict[str, Any] = {}
    
    # ==================== 核心流程方法 ====================
    
    def analyze_impact(self, user_input: str) -> Dict:
        """
        分析用户输入的影响
        
        流程: 用户输入 → 检测变化 → 生成变更清单 → 汇报用户
        """
        # 1. 获取当前日程
        current_schedules = self.db.get_schedules_by_date_range(
            datetime.now() - timedelta(days=1),
            datetime.now() + timedelta(days=7)
        )
        
        # 2. 检测用户输入中的变化意图
        detected_changes = self.change_detector.detect_user_input_changes(
            user_input, current_schedules
        )
        
        # 3. 分析影响
        impact_results = []
        for change in detected_changes:
            impacts = self.impact_analyzer.analyze_impact(change, current_schedules)
            impact_results.extend([i.to_dict() for i in impacts])
        
        return {
            'detected_intents': detected_changes,
            'impact_analysis': impact_results,
            'affected_schedules_count': len(set(
                i.get('affected_schedule_id') for i in impact_results
            ))
        }
    
    def propose_changes(self, old_schedules: List[Dict], 
                        new_schedules: List[Dict]) -> Dict:
        """
        生成变更建议
        
        流程: 对比新旧状态 → 识别变化 → 分析影响 → 生成报告
        """
        # 1. 检测变更
        changes = self.change_detector.detect_changes(old_schedules, new_schedules)
        
        if not changes:
            return {
                'has_changes': False,
                'message': '未发现任何变更'
            }
        
        # 2. 分析影响
        all_schedules = self.db.get_schedules_by_date_range(
            datetime.now() - timedelta(days=30),
            datetime.now() + timedelta(days=30)
        )
        
        impact_results = []
        for change in changes:
            impacts = self.impact_analyzer.analyze_impact(change.to_dict(), all_schedules)
            impact_results.extend([i.to_dict() for i in impacts])
        
        # 3. 生成报告
        changed_ids = [c.schedule_id for c in changes if c.schedule_id]
        report = self.report_generator.generate_report(
            changes=[c.to_dict() for c in changes],
            impact_analysis=impact_results,
            all_schedules=all_schedules,
            changed_schedule_ids=changed_ids
        )
        
        # 4. 保存待确认变更
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._pending_changes[batch_id] = {
            'changes': [c.to_dict() for c in changes],
            'new_schedules': new_schedules,
            'created_at': datetime.now()
        }
        
        result = report.to_dict()
        result['batch_id'] = batch_id
        result['has_changes'] = True
        
        return result
    
    def confirm_changes(self, batch_id: str, user_confirmation: str) -> Dict:
        """
        执行确认的变更
        
        流程: 解析用户回复 → 执行同意的变更 → 同步Cron
        """
        if batch_id not in self._pending_changes:
            return {
                'success': False,
                'error': '未找到待确认的变更批次，可能已过期'
            }
        
        pending = self._pending_changes[batch_id]
        changes = pending['changes']
        
        # 1. 解析用户确认
        confirm_type, approved_indices = self.confirmation_parser.parse_confirmation(
            user_confirmation, len(changes)
        )
        
        if confirm_type == ConfirmationType.UNCLEAR:
            return {
                'success': False,
                'error': '无法识别您的确认指令',
                'hint': '请使用以下格式之一："全部同意"、"全部不同意"、"除了第2项，其他同意"、"第1、3项不同意"'
            }
        
        # 2. 确定要执行的变更
        approved_changes = []
        rejected_changes = []
        
        for i, change in enumerate(changes, 1):
            if i in approved_indices:
                approved_changes.append(change)
            else:
                rejected_changes.append(change)
        
        # 3. 执行同意的变更
        executed = []
        failed = []
        
        for change in approved_changes:
            try:
                result = self._execute_change(change)
                if result:
                    executed.append(change)
                else:
                    failed.append(change)
            except Exception as e:
                failed.append({**change, 'error': str(e)})
        
        # 4. 同步到Cron
        sync_results = []
        if executed:
            sync_results = self.sync_to_cron(executed)
        
        # 5. 清理待确认列表
        del self._pending_changes[batch_id]
        
        return {
            'success': len(failed) == 0,
            'confirmation_type': confirm_type.value,
            'approved_count': len(approved_changes),
            'rejected_count': len(rejected_changes),
            'executed_count': len(executed),
            'failed_count': len(failed),
            'executed_changes': executed,
            'rejected_changes': rejected_changes,
            'failed_changes': failed,
            'cron_sync_results': sync_results
        }
    
    def _execute_change(self, change: Dict) -> bool:
        """执行单个变更"""
        change_type = change.get('change_type')
        schedule_id = change.get('schedule_id')
        
        # 创建变更记录
        change_record_id = self.db.create_change_record({
            'change_type': change_type,
            'schedule_id': schedule_id,
            'field_name': change.get('field_name'),
            'old_value': json.dumps(change.get('old_value')) if change.get('old_value') else None,
            'new_value': json.dumps(change.get('new_value')) if change.get('new_value') else None,
            'status': 'confirmed'
        })
        
        # 根据变更类型执行不同操作
        if change_type == 'create':
            new_schedule = change.get('new_value', {})
            if isinstance(new_schedule, dict) and 'id' in new_schedule:
                # 已经在数据库中，只需更新状态
                pass
        elif change_type == 'update' or change_type == 'reschedule' or change_type == 'postpone':
            if schedule_id and change.get('field_name'):
                self.db.update_schedule(schedule_id, {
                    change['field_name']: change['new_value']
                })
        elif change_type == 'delete' or change_type == 'cancel':
            if schedule_id:
                self.db.delete_schedule(schedule_id, soft=True)
        
        # 标记变更已应用
        self.db.mark_change_applied(change_record_id)
        
        return True
    
    # ==================== 查询方法 ====================
    
    def get_today_schedules(self) -> List[Dict]:
        """获取今日日程（从数据库）"""
        return self.db.get_today_schedules()
    
    def get_schedules_by_range(self, start: datetime, end: datetime) -> List[Dict]:
        """获取日期范围日程"""
        return self.db.get_schedules_by_date_range(start, end)
    
    # ==================== 位置感知 ====================
    
    def update_location(self, new_location: str) -> Dict:
        """
        更新用户位置，分析对日程的影响
        
        流程: 检测位置变化 → 分析影响 → 汇报建议
        """
        # 1. 获取旧位置
        old_location = self.db.get_current_location()
        
        # 2. 如果位置没变，直接返回
        if old_location == new_location:
            return {
                'location_changed': False,
                'message': f'位置未变化，当前位置: {new_location}'
            }
        
        # 3. 更新位置
        self.db.set_user_context('location', 'current', new_location, valid_hours=48)
        
        # 4. 获取相关日程
        future_schedules = self.db.get_schedules_by_date_range(
            datetime.now(),
            datetime.now() + timedelta(days=14)
        )
        
        # 5. 分析影响
        impacts = self.impact_analyzer.analyze_location_impact(
            new_location, future_schedules
        )
        
        # 6. 生成报告
        affected_schedules = [
            s for s in future_schedules 
            if any(i.get('affected_schedule_id') == s['id'] for i in [im.to_dict() for im in impacts])
        ]
        
        report = self.report_generator.generate_location_report(
            old_location, new_location, 
            [i.to_dict() for i in impacts],
            affected_schedules
        )
        
        return {
            'location_changed': True,
            'old_location': old_location,
            'new_location': new_location,
            'affected_count': len(affected_schedules),
            'report': report,
            'impacts': [i.to_dict() for i in impacts]
        }
    
    # ==================== Cron同步 ====================
    
    def sync_to_cron(self, changes: List[Dict] = None) -> List[Dict]:
        """
        数据库同步到Cron
        
        核心原则: 所有变更必须先更新数据库，再同步Cron
        """
        sync_results = []
        
        # 获取需要同步的日程
        if changes:
            schedule_ids = [c.get('schedule_id') for c in changes if c.get('schedule_id')]
            schedules = []
            for sid in schedule_ids:
                s = self.db.get_schedule(sid)
                if s:
                    schedules.append(s)
        else:
            # 同步所有活跃日程
            schedules = self.db.get_schedules_by_date_range(
                datetime.now(),
                datetime.now() + timedelta(days=30)
            )
        
        # 模拟同步到Cron（实际应调用cron服务）
        for schedule in schedules:
            try:
                # 生成cron表达式
                cron_expr = self._generate_cron_expression(schedule)
                
                # 记录同步日志
                self.db.log_cron_sync({
                    'sync_type': 'schedule',
                    'schedule_id': schedule['id'],
                    'cron_expression': cron_expr,
                    'sync_status': 'success'
                })
                
                sync_results.append({
                    'schedule_id': schedule['id'],
                    'title': schedule.get('title'),
                    'status': 'success',
                    'cron_expression': cron_expr
                })
            except Exception as e:
                self.db.log_cron_sync({
                    'sync_type': 'schedule',
                    'schedule_id': schedule['id'],
                    'sync_status': 'failed',
                    'error_message': str(e)
                })
                
                sync_results.append({
                    'schedule_id': schedule['id'],
                    'title': schedule.get('title'),
                    'status': 'failed',
                    'error': str(e)
                })
        
        return sync_results
    
    def _generate_cron_expression(self, schedule: Dict) -> str:
        """生成cron表达式（简化版）"""
        start_time = schedule.get('start_time', '')
        recurrence = schedule.get('recurrence_rule', '')
        
        # 解析时间
        if isinstance(start_time, str):
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except:
                dt = datetime.now()
        else:
            dt = start_time or datetime.now()
        
        minute = dt.minute
        hour = dt.hour
        
        # 根据重复规则生成
        if 'daily' in recurrence:
            return f"{minute} {hour} * * *"
        elif 'weekly' in recurrence:
            weekday = dt.weekday()
            return f"{minute} {hour} * * {weekday}"
        else:
            day = dt.day
            month = dt.month
            return f"{minute} {hour} {day} {month} *"
    
    # ==================== 辅助方法 ====================
    
    def get_pending_confirmations(self) -> Dict:
        """获取待确认的变更"""
        return self._pending_changes
    
    def get_schedule_history(self, schedule_id: int) -> List[Dict]:
        """获取日程变更历史"""
        # 从 schedule_changes 表查询
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM schedule_changes WHERE schedule_id = ? ORDER BY created_at DESC",
                (schedule_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
