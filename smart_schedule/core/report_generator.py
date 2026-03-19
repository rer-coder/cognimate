"""
CogniMate 智能日程管理系统 - 汇报生成器
生成"变化项 vs 不变项"报告
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ChangeReport:
    """变更报告"""
    summary: str
    total_changes: int
    changes_by_type: Dict[str, int]
    high_impact_changes: List[Dict]
    medium_impact_changes: List[Dict]
    low_impact_changes: List[Dict]
    unchanged_schedules: List[Dict]
    impact_analysis: List[Dict]
    confirmation_prompt: str
    change_ids: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'summary': self.summary,
            'total_changes': self.total_changes,
            'changes_by_type': self.changes_by_type,
            'high_impact_changes': self.high_impact_changes,
            'medium_impact_changes': self.medium_impact_changes,
            'low_impact_changes': self.low_impact_changes,
            'unchanged_schedules': self.unchanged_schedules,
            'impact_analysis': self.impact_analysis,
            'confirmation_prompt': self.confirmation_prompt,
            'change_ids': self.change_ids
        }

class ReportGenerator:
    """汇报生成器 - 生成用户友好的变更报告"""
    
    def __init__(self):
        pass
    
    def generate_report(self, changes: List[Dict], 
                        impact_analysis: List[Dict],
                        all_schedules: List[Dict],
                        changed_schedule_ids: List[int]) -> ChangeReport:
        """
        生成变更报告
        
        Args:
            changes: 变更列表
            impact_analysis: 影响分析列表
            all_schedules: 所有日程
            changed_schedule_ids: 变更的日程ID列表
        
        Returns:
            变更报告
        """
        # 按影响级别分类
        high_impact = [c for c in changes if c.get('impact_level') == 'high']
        medium_impact = [c for c in changes if c.get('impact_level') == 'medium']
        low_impact = [c for c in changes if c.get('impact_level') == 'low']
        
        # 统计变更类型
        changes_by_type = {}
        for change in changes:
            change_type = change.get('change_type', 'unknown')
            changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1
        
        # 获取未变更的日程
        unchanged = [
            s for s in all_schedules 
            if s.get('id') not in changed_schedule_ids and s.get('status') == 'active'
        ]
        
        # 生成摘要
        summary = self._generate_summary(changes, changes_by_type)
        
        # 生成确认提示
        confirmation_prompt = self._generate_confirmation_prompt(changes)
        
        # 提取变更记录ID
        change_ids = [c.get('id') for c in changes if c.get('id')]
        
        return ChangeReport(
            summary=summary,
            total_changes=len(changes),
            changes_by_type=changes_by_type,
            high_impact_changes=high_impact,
            medium_impact_changes=medium_impact,
            low_impact_changes=low_impact,
            unchanged_schedules=unchanged[:5],  # 只显示前5个未变更
            impact_analysis=impact_analysis,
            confirmation_prompt=confirmation_prompt,
            change_ids=change_ids
        )
    
    def _generate_summary(self, changes: List[Dict], 
                          changes_by_type: Dict) -> str:
        """生成报告摘要"""
        total = len(changes)
        
        if total == 0:
            return "未发现任何变更。"
        
        parts = [f"检测到 **{total}** 项变更："]
        
        type_names = {
            'create': '新增',
            'update': '修改',
            'delete': '删除',
            'cancel': '取消',
            'postpone': '推迟',
            'reschedule': '改期'
        }
        
        for change_type, count in changes_by_type.items():
            name = type_names.get(change_type, change_type)
            parts.append(f"  - {name}: {count} 项")
        
        # 添加高影响提醒
        high_impact_count = len([c for c in changes if c.get('impact_level') == 'high'])
        if high_impact_count > 0:
            parts.append(f"\n⚠️ 其中有 **{high_impact_count}** 项高影响变更，请特别注意。")
        
        return "\n".join(parts)
    
    def _generate_confirmation_prompt(self, changes: List[Dict]) -> str:
        """生成确认提示"""
        if not changes:
            return ""
        
        lines = ["\n📋 **变更清单** (请回复同意/不同意):\n"]
        
        for i, change in enumerate(changes, 1):
            change_type = change.get('change_type', '')
            description = change.get('description', '')
            impact = change.get('impact_level', 'low')
            
            impact_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(impact, '⚪')
            
            lines.append(f"{impact_emoji} **{i}.** {description}")
        
        lines.append("\n💡 **您可以这样回复：**")
        lines.append('  - "全部同意" - 应用所有变更')
        lines.append('  - "全部不同意" - 拒绝所有变更')
        lines.append('  - "除了第2项，其他都同意" - 部分同意')
        lines.append('  - "第1、3项不同意" - 指定不同意的项')
        
        return "\n".join(lines)
    
    def generate_location_report(self, old_location: str, new_location: str,
                                  impacts: List[Dict],
                                  affected_schedules: List[Dict]) -> str:
        """
        生成位置变更报告
        
        Args:
            old_location: 原位置
            new_location: 新位置
            impacts: 影响分析
            affected_schedules: 受影响的日程
        
        Returns:
            报告文本
        """
        lines = [
            f"📍 **位置变更检测**",
            f"从 『{old_location or "未知"}』 变为 『{new_location}』\n",
            f"该变更可能影响以下 **{len(affected_schedules)}** 个日程：\n"
        ]
        
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠', 
            'medium': '🟡',
            'low': '🟢'
        }
        
        for i, impact in enumerate(impacts, 1):
            severity = impact.get('severity', 'low')
            emoji = severity_emoji.get(severity, '⚪')
            title = impact.get('affected_schedule_title', '未命名')
            description = impact.get('impact_description', '')
            suggestion = impact.get('suggested_action', '')
            
            lines.append(f"{emoji} **{i}. {title}**")
            lines.append(f"   影响: {description}")
            lines.append(f"   建议: {suggestion}\n")
        
        if not impacts:
            lines.append("✅ 该位置变更不会对现有日程产生影响。")
        else:
            lines.append("\n💡 请确认是否应用以上调整建议？")
        
        return "\n".join(lines)
    
    def format_schedule_for_display(self, schedule: Dict) -> str:
        """格式化日程供显示"""
        title = schedule.get('title', '未命名')
        start_time = schedule.get('start_time', '')
        location = schedule.get('location', '')
        
        time_str = self._format_time(start_time)
        location_str = f" 📍{location}" if location else ""
        
        return f"{time_str} {title}{location_str}"
    
    def _format_time(self, time_value) -> str:
        """格式化时间"""
        if isinstance(time_value, datetime):
            return time_value.strftime('%m月%d日 %H:%M')
        if isinstance(time_value, str):
            try:
                dt = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                return dt.strftime('%m月%d日 %H:%M')
            except:
                return time_value
        return str(time_value)
