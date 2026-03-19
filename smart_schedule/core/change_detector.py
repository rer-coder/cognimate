"""
CogniMate 智能日程管理系统 - 变更检测引擎
对比新旧状态，识别变化
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

class ChangeType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CANCEL = "cancel"
    POSTPONE = "postpone"
    RESCHEDULE = "reschedule"

@dataclass
class ScheduleChange:
    change_type: ChangeType
    schedule_id: Optional[int]
    field_name: Optional[str]
    old_value: Any
    new_value: Any
    description: str
    impact_level: str  # 'low', 'medium', 'high'
    affected_schedules: List[int] = None
    
    def to_dict(self) -> Dict:
        return {
            'change_type': self.change_type.value,
            'schedule_id': self.schedule_id,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'description': self.description,
            'impact_level': self.impact_level,
            'affected_schedules': self.affected_schedules or []
        }

class ChangeDetectionEngine:
    """变更检测引擎 - 识别日程变化"""
    
    # 关键字段变更的影响级别
    IMPACT_FIELDS = {
        'start_time': 'high',
        'end_time': 'high',
        'location': 'medium',
        'status': 'high',
        'title': 'low',
        'description': 'low',
        'category': 'medium',
        'priority': 'low'
    }
    
    def __init__(self, db):
        self.db = db
    
    def detect_changes(self, old_schedules: List[Dict], 
                       new_schedules: List[Dict]) -> List[ScheduleChange]:
        """
        检测日程变化
        
        Args:
            old_schedules: 变更前的日程列表
            new_schedules: 变更后的日程列表
        
        Returns:
            变更列表
        """
        changes = []
        
        # 创建ID到日程的映射
        old_map = {s['id']: s for s in old_schedules if 'id' in s}
        new_map = {s['id']: s for s in new_schedules if 'id' in s}
        
        # 1. 检测删除的日程
        for schedule_id, old_schedule in old_map.items():
            if schedule_id not in new_map:
                changes.append(ScheduleChange(
                    change_type=ChangeType.DELETE,
                    schedule_id=schedule_id,
                    field_name=None,
                    old_value=old_schedule,
                    new_value=None,
                    description=f"删除日程: {old_schedule.get('title', '未命名')}",
                    impact_level='high',
                    affected_schedules=[schedule_id]
                ))
        
        # 2. 检测新增的日程
        for schedule_id, new_schedule in new_map.items():
            if schedule_id not in old_map:
                changes.append(ScheduleChange(
                    change_type=ChangeType.CREATE,
                    schedule_id=schedule_id,
                    field_name=None,
                    old_value=None,
                    new_value=new_schedule,
                    description=f"新增日程: {new_schedule.get('title', '未命名')}",
                    impact_level='medium',
                    affected_schedules=[schedule_id]
                ))
        
        # 3. 检测修改的日程
        for schedule_id in set(old_map.keys()) & set(new_map.keys()):
            old_schedule = old_map[schedule_id]
            new_schedule = new_map[schedule_id]
            
            field_changes = self._detect_field_changes(schedule_id, old_schedule, new_schedule)
            changes.extend(field_changes)
        
        return changes
    
    def _detect_field_changes(self, schedule_id: int, 
                              old_schedule: Dict, 
                              new_schedule: Dict) -> List[ScheduleChange]:
        """检测字段级别的变化"""
        changes = []
        
        # 检查所有可能的字段
        all_fields = set(old_schedule.keys()) | set(new_schedule.keys())
        
        for field in all_fields:
            # 跳过非业务字段
            if field in ('created_at', 'updated_at', 'id'):
                continue
            
            old_value = old_schedule.get(field)
            new_value = new_schedule.get(field)
            
            # 处理JSON字段
            if isinstance(old_value, str) and old_value.startswith('{'):
                try:
                    old_value = json.loads(old_value)
                except:
                    pass
            if isinstance(new_value, str) and new_value.startswith('{'):
                try:
                    new_value = json.loads(new_value)
                except:
                    pass
            
            # 检测变化
            if old_value != new_value:
                impact = self.IMPACT_FIELDS.get(field, 'low')
                
                # 特殊处理时间变更
                change_type = ChangeType.UPDATE
                if field == 'start_time' and old_value and new_value:
                    old_dt = self._parse_datetime(old_value)
                    new_dt = self._parse_datetime(new_value)
                    if old_dt and new_dt:
                        diff = new_dt - old_dt
                        if diff.total_seconds() > 86400:  # > 1天
                            change_type = ChangeType.POSTPONE
                        elif abs(diff.total_seconds()) > 3600:  # > 1小时
                            change_type = ChangeType.RESCHEDULE
                
                # 特殊处理状态变更
                if field == 'status':
                    if new_value == 'cancelled':
                        change_type = ChangeType.CANCEL
                    elif old_value == 'cancelled' and new_value == 'active':
                        change_type = ChangeType.CREATE
                
                changes.append(ScheduleChange(
                    change_type=change_type,
                    schedule_id=schedule_id,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value,
                    description=self._generate_change_description(
                        schedule_id, old_schedule.get('title', '未命名'),
                        field, old_value, new_value
                    ),
                    impact_level=impact,
                    affected_schedules=[schedule_id]
                ))
        
        return changes
    
    def _parse_datetime(self, value) -> Optional[datetime]:
        """解析日期时间"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except:
                    continue
        return None
    
    def _generate_change_description(self, schedule_id: int, title: str,
                                     field: str, old_value: Any, new_value: Any) -> str:
        """生成变更描述"""
        field_names = {
            'title': '标题',
            'start_time': '开始时间',
            'end_time': '结束时间',
            'location': '地点',
            'description': '描述',
            'category': '类别',
            'priority': '优先级',
            'status': '状态'
        }
        
        field_name = field_names.get(field, field)
        
        if field == 'start_time':
            old_str = self._format_datetime(old_value) or '未设置'
            new_str = self._format_datetime(new_value) or '未设置'
            return f"【{title}】{field_name}: {old_str} → {new_str}"
        elif field == 'end_time':
            old_str = self._format_datetime(old_value) or '未设置'
            new_str = self._format_datetime(new_value) or '未设置'
            return f"【{title}】{field_name}: {old_str} → {new_str}"
        elif field == 'status':
            status_map = {'active': '活跃', 'cancelled': '已取消', 'completed': '已完成'}
            old_str = status_map.get(str(old_value), str(old_value))
            new_str = status_map.get(str(new_value), str(new_value))
            return f"【{title}】{field_name}: {old_str} → {new_str}"
        else:
            old_str = str(old_value) if old_value is not None else '未设置'
            new_str = str(new_value) if new_value is not None else '未设置'
            return f"【{title}】{field_name}: {old_str} → {new_str}"
    
    def _format_datetime(self, value) -> Optional[str]:
        """格式化日期时间"""
        dt = self._parse_datetime(value)
        if dt:
            return dt.strftime('%m月%d日 %H:%M')
        return None
    
    def detect_user_input_changes(self, user_input: str, 
                                   current_schedules: List[Dict]) -> List[Dict]:
        """
        从用户输入中解析可能的变化意图
        
        这是一个简化版本，实际可以使用NLP解析
        """
        changes = []
        
        # 简单的关键词匹配
        keywords = {
            '取消': 'cancel',
            '删掉': 'delete',
            '删除': 'delete',
            '改到': 'reschedule',
            '推迟': 'postpone',
            '提前': 'reschedule',
            '延后': 'postpone'
        }
        
        detected_intent = None
        for keyword, intent in keywords.items():
            if keyword in user_input:
                detected_intent = intent
                break
        
        if detected_intent:
            # 尝试匹配相关日程
            for schedule in current_schedules:
                title = schedule.get('title', '')
                if title in user_input or any(word in user_input for word in title.split()):
                    changes.append({
                        'intent': detected_intent,
                        'schedule_id': schedule['id'],
                        'schedule_title': title,
                        'confidence': 'medium'
                    })
        
        return changes
