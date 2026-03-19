"""
CogniMate 智能日程管理系统 - 影响分析器
分析变化影响的日程项
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ImpactType(Enum):
    DIRECT = "direct"          # 直接影响
    INDIRECT = "indirect"      # 间接影响
    CASCADING = "cascading"    # 级联影响
    CONFLICT = "conflict"      # 冲突影响

@dataclass
class ImpactAnalysis:
    impact_type: ImpactType
    affected_schedule_id: int
    affected_schedule_title: str
    impact_description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    suggested_action: str
    related_change_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'impact_type': self.impact_type.value,
            'affected_schedule_id': self.affected_schedule_id,
            'affected_schedule_title': self.affected_schedule_title,
            'impact_description': self.impact_description,
            'severity': self.severity,
            'suggested_action': self.suggested_action,
            'related_change_id': self.related_change_id
        }

class ImpactAnalyzer:
    """影响分析器 - 分析变更对其他日程的影响"""
    
    def __init__(self, db):
        self.db = db
    
    def analyze_impact(self, change: Dict, 
                       all_schedules: List[Dict]) -> List[ImpactAnalysis]:
        """
        分析变更的影响
        
        Args:
            change: 变更信息
            all_schedules: 所有相关日程
        
        Returns:
            影响分析列表
        """
        impacts = []
        
        change_type = change.get('change_type')
        schedule_id = change.get('schedule_id')
        new_value = change.get('new_value')
        old_value = change.get('old_value')
        field_name = change.get('field_name')
        
        # 获取变更的日程
        changed_schedule = None
        for s in all_schedules:
            if s.get('id') == schedule_id:
                changed_schedule = s
                break
        
        if not changed_schedule:
            return impacts
        
        # 1. 分析时间变更的影响
        if field_name == 'start_time' or field_name == 'end_time' or change_type in ('postpone', 'reschedule'):
            time_impacts = self._analyze_time_impact(
                changed_schedule, new_value, all_schedules
            )
            impacts.extend(time_impacts)
        
        # 2. 分析取消/删除的影响
        if change_type in ('delete', 'cancel'):
            cancel_impacts = self._analyze_cancel_impact(changed_schedule, all_schedules)
            impacts.extend(cancel_impacts)
        
        # 3. 分析新增日程的影响
        if change_type == 'create':
            create_impacts = self._analyze_create_impact(changed_schedule, all_schedules)
            impacts.extend(create_impacts)
        
        # 4. 分析地点变更的影响
        if field_name == 'location':
            location_impacts = self._analyze_location_impact(
                changed_schedule, old_value, new_value, all_schedules
            )
            impacts.extend(location_impacts)
        
        return impacts
    
    def _analyze_time_impact(self, changed_schedule: Dict, 
                             new_time, all_schedules: List[Dict]) -> List[ImpactAnalysis]:
        """分析时间变更的影响"""
        impacts = []
        
        new_start = self._parse_time(new_time) if isinstance(new_time, str) else new_time
        if not new_start:
            # 尝试从 schedule 数据中获取
            new_start = self._parse_time(changed_schedule.get('start_time'))
        
        if not new_start:
            return impacts
        
        new_end = self._parse_time(changed_schedule.get('end_time'))
        if not new_end:
            new_end = new_start + timedelta(hours=1)
        
        # 检查冲突的日程
        for schedule in all_schedules:
            if schedule['id'] == changed_schedule['id']:
                continue
            
            other_start = self._parse_time(schedule.get('start_time'))
            other_end = self._parse_time(schedule.get('end_time'))
            
            if not other_start:
                continue
            if not other_end:
                other_end = other_start + timedelta(hours=1)
            
            # 检查时间冲突
            if (new_start < other_end and new_end > other_start):
                impacts.append(ImpactAnalysis(
                    impact_type=ImpactType.CONFLICT,
                    affected_schedule_id=schedule['id'],
                    affected_schedule_title=schedule.get('title', '未命名'),
                    impact_description=f"与日程『{changed_schedule.get('title', '未命名')}』时间冲突",
                    severity='high',
                    suggested_action=f"建议调整『{schedule.get('title', '未命名')}』的时间"
                ))
        
        # 检查目标关联影响
        goal_impacts = self._check_goal_impact(changed_schedule, all_schedules)
        impacts.extend(goal_impacts)
        
        return impacts
    
    def _analyze_cancel_impact(self, cancelled_schedule: Dict, 
                               all_schedules: List[Dict]) -> List[ImpactAnalysis]:
        """分析取消的影响"""
        impacts = []
        
        # 检查是否有关联目标
        category = cancelled_schedule.get('category', '')
        if category in ['fitness', 'learning', 'work']:
            impacts.append(ImpactAnalysis(
                impact_type=ImpactType.CASCADING,
                affected_schedule_id=cancelled_schedule['id'],
                affected_schedule_title=cancelled_schedule.get('title', '未命名'),
                impact_description=f"取消『{cancelled_schedule.get('title', '未命名')}』可能影响相关目标的进度",
                severity='medium',
                suggested_action="考虑在本周其他时间安排替代活动"
            ))
        
        return impacts
    
    def _analyze_create_impact(self, new_schedule: Dict, 
                               all_schedules: List[Dict]) -> List[ImpactAnalysis]:
        """分析新增日程的影响"""
        impacts = []
        
        new_start = self._parse_time(new_schedule.get('start_time'))
        new_end = self._parse_time(new_schedule.get('end_time'))
        
        if not new_start:
            return impacts
        if not new_end:
            new_end = new_start + timedelta(hours=1)
        
        # 检查冲突
        for schedule in all_schedules:
            if schedule['id'] == new_schedule.get('id'):
                continue
            
            other_start = self._parse_time(schedule.get('start_time'))
            other_end = self._parse_time(schedule.get('end_time'))
            
            if not other_start:
                continue
            if not other_end:
                other_end = other_start + timedelta(hours=1)
            
            if (new_start < other_end and new_end > other_start):
                impacts.append(ImpactAnalysis(
                    impact_type=ImpactType.CONFLICT,
                    affected_schedule_id=schedule['id'],
                    affected_schedule_title=schedule.get('title', '未命名'),
                    impact_description=f"新增日程与『{schedule.get('title', '未命名')}』时间冲突",
                    severity='high',
                    suggested_action=f"请确认是否调整其中一个日程的时间"
                ))
        
        # 检查是否有助于目标
        category = new_schedule.get('category', '')
        if category in ['fitness', 'learning', 'work']:
            impacts.append(ImpactAnalysis(
                impact_type=ImpactType.INDIRECT,
                affected_schedule_id=new_schedule.get('id'),
                affected_schedule_title=new_schedule.get('title', '未命名'),
                impact_description=f"新增日程有助于推进相关目标",
                severity='low',
                suggested_action="确保该日程与现有目标一致"
            ))
        
        return impacts
    
    def _analyze_location_impact(self, changed_schedule: Dict,
                                  old_location: str, new_location: str,
                                  all_schedules: List[Dict]) -> List[ImpactAnalysis]:
        """分析地点变更的影响"""
        impacts = []
        
        # 检查同地点的其他日程
        if new_location:
            same_location_schedules = [
                s for s in all_schedules 
                if s.get('location') == new_location and s['id'] != changed_schedule['id']
            ]
            
            if len(same_location_schedules) > 0:
                impacts.append(ImpactAnalysis(
                    impact_type=ImpactType.INDIRECT,
                    affected_schedule_id=changed_schedule['id'],
                    affected_schedule_title=changed_schedule.get('title', '未命名'),
                    impact_description=f"地点变更为『{new_location}』，该地点还有 {len(same_location_schedules)} 个日程",
                    severity='low',
                    suggested_action="可以优化行程安排，减少往返时间"
                ))
        
        return impacts
    
    def _check_goal_impact(self, changed_schedule: Dict, 
                           all_schedules: List[Dict]) -> List[ImpactAnalysis]:
        """检查对目标的影响"""
        impacts = []
        # 这里可以查询目标表，检查影响
        # 简化实现，实际应查询 goals 表
        return impacts
    
    def _parse_time(self, time_value) -> Optional[datetime]:
        """解析时间"""
        if isinstance(time_value, datetime):
            return time_value
        if isinstance(time_value, str):
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d'
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(time_value, fmt)
                except:
                    continue
        return None
    
    def analyze_location_impact(self, location: str, 
                                all_schedules: List[Dict]) -> List[ImpactAnalysis]:
        """
        分析位置变化对所有日程的影响
        
        Args:
            location: 新位置 (company, hometown, business_trip等)
            all_schedules: 所有日程
        
        Returns:
            影响分析列表
        """
        impacts = []
        
        # 获取位置规则
        location_rules = self.db.get_location_rules(location)
        
        if not location_rules:
            return impacts
        
        rule = location_rules[0]
        affected_categories = rule.get('affected_categories', [])
        adjustments = rule.get('schedule_adjustments', {})
        
        for schedule in all_schedules:
            category = schedule.get('category', '')
            
            if category in affected_categories:
                # 根据规则生成影响分析
                if adjustments.get('cancel'):
                    impacts.append(ImpactAnalysis(
                        impact_type=ImpactType.DIRECT,
                        affected_schedule_id=schedule['id'],
                        affected_schedule_title=schedule.get('title', '未命名'),
                        impact_description=f"由于位置变为『{location}』，该日程建议取消",
                        severity='high',
                        suggested_action='取消该日程或调整为其他活动'
                    ))
                elif adjustments.get('postpone_to'):
                    impacts.append(ImpactAnalysis(
                        impact_type=ImpactType.DIRECT,
                        affected_schedule_id=schedule['id'],
                        affected_schedule_title=schedule.get('title', '未命名'),
                        impact_description=f"由于位置变为『{location}』，该日程建议推迟",
                        severity='medium',
                        suggested_action=f"推迟到 {adjustments.get('postpone_to')}"
                    ))
                elif adjustments.get('reminder_offset'):
                    impacts.append(ImpactAnalysis(
                        impact_type=ImpactType.INDIRECT,
                        affected_schedule_id=schedule['id'],
                        affected_schedule_title=schedule.get('title', '未命名'),
                        impact_description=f"由于位置变为『{location}』，提醒时间需要调整",
                        severity='low',
                        suggested_action=f"提前 {adjustments.get('reminder_offset')} 分钟提醒"
                    ))
        
        return impacts
