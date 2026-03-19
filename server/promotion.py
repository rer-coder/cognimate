#!/usr/bin/env python3
"""
CogniMate 学习记录自动晋升机制
将有效的学习记录晋升到长期记忆（USER.md / AGENTS.md）
"""

import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class LearningPromoter:
    """学习记录晋升器"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.learnings_dir = self.workspace / ".learnings"
        self.user_file = self.workspace / "USER.md"
        self.agents_file = self.workspace / "AGENTS.md"
        
        # 晋升阈值配置
        self.thresholds = {
            "min_occurrences": 2,  # 最少出现次数
            "max_age_days": 30,    # 最大年龄（天）
            "min_priority": "medium"  # 最低优先级
        }
    
    def _read_learnings_file(self, filename: str) -> List[Dict]:
        """读取学习记录文件"""
        filepath = self.learnings_dir / filename
        if not filepath.exists():
            return []
        
        content = filepath.read_text(encoding='utf-8')
        entries = []
        
        # 按条目分割
        raw_entries = content.split('---')
        
        for entry in raw_entries:
            if not entry.strip():
                continue
            
            parsed = self._parse_entry(entry)
            if parsed:
                entries.append(parsed)
        
        return entries
    
    def _parse_entry(self, entry: str) -> Optional[Dict]:
        """解析单条学习记录"""
        lines = entry.strip().split('\n')
        
        result = {
            "id": "",
            "category": "",
            "summary": "",
            "details": "",
            "suggested_action": "",
            "priority": "medium",
            "status": "pending",
            "area": "general",
            "tags": [],
            "source": "",
            "logged_date": None
        }
        
        for line in lines:
            line = line.strip()
            
            # 解析 ID
            if line.startswith('## ['):
                match = re.search(r'## \[(.+?)\] (.+)', line)
                if match:
                    result["id"] = match.group(1)
                    result["category"] = match.group(2)
            
            # 解析字段
            elif line.startswith('**Logged**:'):
                date_str = line.split(':', 1)[1].strip()
                result["logged_date"] = self._parse_date(date_str)
            elif line.startswith('**Priority**:'):
                result["priority"] = line.split(':', 1)[1].strip()
            elif line.startswith('**Status**:'):
                result["status"] = line.split(':', 1)[1].strip()
            elif line.startswith('**Area**:'):
                result["area"] = line.split(':', 1)[1].strip()
            
            # 解析区块内容
            elif line == '### Summary':
                current_field = 'summary'
            elif line == '### Details':
                current_field = 'details'
            elif line == '### Suggested Action':
                current_field = 'suggested_action'
            
            # 收集内容
            elif 'current_field' in dir() and line and not line.startswith('#') and not line.startswith('-') and not line.startswith('**'):
                if current_field in ['summary', 'details', 'suggested_action']:
                    if result[current_field]:
                        result[current_field] += ' ' + line
                    else:
                        result[current_field] = line
            
            # 解析标签
            elif line.startswith('- Tags:'):
                tags_str = line.split(':', 1)[1].strip()
                result["tags"] = [t.strip() for t in tags_str.split(',')]
            elif line.startswith('- Source:'):
                result["source"] = line.split(':', 1)[1].strip()
        
        return result if result["id"] else None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        try:
            # 尝试 ISO 格式
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # 尝试其他格式
                return datetime.strptime(date_str[:10], "%Y-%m-%d")
            except:
                return None
    
    def _is_promotable(self, entry: Dict) -> Tuple[bool, str]:
        """
        判断学习记录是否应该晋升
        
        Returns:
            (是否应该晋升, 原因)
        """
        # 检查状态
        if entry.get("status") not in ["pending", "resolved"]:
            return False, "状态不是 pending 或 resolved"
        
        # 检查优先级
        priority = entry.get("priority", "medium")
        priority_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        min_priority_rank = priority_rank.get(self.thresholds["min_priority"], 2)
        
        if priority_rank.get(priority, 0) < min_priority_rank:
            return False, f"优先级 {priority} 低于阈值 {self.thresholds['min_priority']}"
        
        # 检查年龄
        logged_date = entry.get("logged_date")
        if logged_date:
            try:
                # 处理时区问题
                now = datetime.now()
                if logged_date.tzinfo is not None and now.tzinfo is None:
                    now = now.replace(tzinfo=logged_date.tzinfo)
                elif logged_date.tzinfo is None and now.tzinfo is not None:
                    logged_date = logged_date.replace(tzinfo=now.tzinfo)
                
                age_days = (now - logged_date).days
                if age_days > self.thresholds["max_age_days"]:
                    return False, f"记录太旧（{age_days}天）"
            except Exception:
                # 如果日期计算失败，忽略年龄检查
                pass
        
        # 高优先级自动晋升
        if priority in ["critical", "high"]:
            return True, "高优先级"
        
        # 检查是否来自用户反馈（用户纠正通常很重要）
        if entry.get("source") == "user_feedback":
            return True, "用户反馈"
        
        # 检查类别
        category = entry.get("category", "")
        if category == "correction":
            return True, "用户纠正"
        
        return False, "未达到晋升条件"
    
    def identify_promotable_learnings(self) -> List[Dict]:
        """识别可晋升的学习记录"""
        promotable = []
        
        # 读取所有学习记录
        learnings = self._read_learnings_file("LEARNINGS.md")
        
        for entry in learnings:
            should_promote, reason = self._is_promotable(entry)
            if should_promote:
                entry["promote_reason"] = reason
                promotable.append(entry)
        
        return promotable
    
    def _format_for_user_md(self, entry: Dict) -> str:
        """格式化为 USER.md 条目"""
        category = entry.get("category", "")
        summary = entry.get("summary", "")
        
        if category == "correction":
            return f"- **{summary}**"
        elif category == "best_practice":
            return f"- {summary}"
        else:
            return f"- {summary}"
    
    def _format_for_agents_md(self, entry: Dict) -> str:
        """格式化为 AGENTS.md 条目"""
        summary = entry.get("summary", "")
        action = entry.get("suggested_action", "")
        
        if action:
            return f"- {summary} → {action}"
        return f"- {summary}"
    
    def promote_to_user_md(self, entry: Dict) -> bool:
        """晋升到 USER.md"""
        try:
            if not self.user_file.exists():
                return False
            
            content = self.user_file.read_text(encoding='utf-8')
            
            # 确定插入位置
            area = entry.get("area", "general")
            formatted = self._format_for_user_md(entry)
            
            # 根据 area 选择插入位置
            if area == "schedule":
                section = "## 日程管理"
            elif area == "goal":
                section = "## 目标管理"
            elif area == "sentiment":
                section = "## 沟通风格"
            else:
                section = "## 个人偏好"
            
            # 查找插入位置
            if section in content:
                # 在对应 section 后插入
                lines = content.split('\n')
                new_lines = []
                inserted = False
                
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    
                    if not inserted and line.startswith(section):
                        # 找到 section 的下一个空行或下一个 section
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() == '' or lines[j].startswith('##'):
                                new_lines.append(f"\n### 学习记录（自动添加）")
                                new_lines.append(f"{formatted}")
                                new_lines.append(f"<!-- LRN-ID: {entry.get('id')} -->")
                                inserted = True
                                break
                
                if inserted:
                    content = '\n'.join(new_lines)
            else:
                # 添加到文件末尾
                content += f"\n\n### 学习记录（自动添加）\n{formatted}\n<!-- LRN-ID: {entry.get('id')} -->"
            
            self.user_file.write_text(content, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"晋升到 USER.md 失败: {e}")
            return False
    
    def promote_to_agents_md(self, entry: Dict) -> bool:
        """晋升到 AGENTS.md"""
        try:
            if not self.agents_file.exists():
                return False
            
            content = self.agents_file.read_text(encoding='utf-8')
            formatted = self._format_for_agents_md(entry)
            
            # 添加到工作流改进 section
            section = "## 工作流程"
            
            if section in content:
                lines = content.split('\n')
                new_lines = []
                inserted = False
                
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    
                    if not inserted and line.startswith(section):
                        new_lines.append(f"\n### 学习改进（自动添加）")
                        new_lines.append(f"{formatted}")
                        new_lines.append(f"<!-- LRN-ID: {entry.get('id')} -->")
                        inserted = True
                
                if inserted:
                    content = '\n'.join(new_lines)
            else:
                content += f"\n\n### 学习改进（自动添加）\n{formatted}\n<!-- LRN-ID: {entry.get('id')} -->"
            
            self.agents_file.write_text(content, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"晋升到 AGENTS.md 失败: {e}")
            return False
    
    def update_learning_status(self, entry_id: str, new_status: str = "promoted") -> bool:
        """更新学习记录的状态"""
        try:
            filepath = self.learnings_dir / "LEARNINGS.md"
            if not filepath.exists():
                return False
            
            content = filepath.read_text(encoding='utf-8')
            
            # 查找并替换状态
            pattern = rf'(## \[{re.escape(entry_id)}\].*?)\*\*Status\*\*: \w+'
            replacement = rf'\1**Status**: {new_status}'
            
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            if new_content != content:
                filepath.write_text(new_content, encoding='utf-8')
                return True
            
            return False
            
        except Exception as e:
            print(f"更新状态失败: {e}")
            return False
    
    def run_promotion(self, dry_run: bool = False) -> Dict:
        """
        运行晋升流程
        
        Args:
            dry_run: 如果为 True，只显示会晋升哪些记录，不实际执行
        
        Returns:
            {
                "total_scanned": int,
                "promotable_count": int,
                "promoted": List[Dict],
                "skipped": List[Dict]
            }
        """
        promotable = self.identify_promotable_learnings()
        
        result = {
            "total_scanned": len(self._read_learnings_file("LEARNINGS.md")),
            "promotable_count": len(promotable),
            "promoted": [],
            "skipped": []
        }
        
        if dry_run:
            print("=== 试运行模式（不会实际修改文件）===\n")
        
        for entry in promotable:
            entry_id = entry.get("id")
            area = entry.get("area")
            reason = entry.get("promote_reason")
            
            print(f"准备晋升: [{entry_id}] {entry.get('summary', '')[:50]}...")
            print(f"  原因: {reason}")
            print(f"  领域: {area}")
            
            if not dry_run:
                # 决定晋升到哪个文件
                success = False
                target_file = ""
                
                if area in ["schedule", "goal", "sentiment"]:
                    success = self.promote_to_user_md(entry)
                    target_file = "USER.md"
                else:
                    success = self.promote_to_agents_md(entry)
                    target_file = "AGENTS.md"
                
                if success:
                    # 更新学习记录状态
                    self.update_learning_status(entry_id, "promoted")
                    
                    result["promoted"].append({
                        "id": entry_id,
                        "target": target_file,
                        "summary": entry.get("summary", "")
                    })
                    print(f"  ✅ 已晋升到 {target_file}")
                else:
                    result["skipped"].append({
                        "id": entry_id,
                        "reason": "晋升失败"
                    })
                    print(f"  ❌ 晋升失败")
            else:
                print(f"  [试运行] 会晋升到 {'USER.md' if area in ['schedule', 'goal', 'sentiment'] else 'AGENTS.md'}")
            
            print()
        
        return result


# ============ 便捷函数 ============

def auto_promote(workspace_path: str = None, dry_run: bool = False) -> Dict:
    """
    自动运行晋升流程
    
    使用示例:
    
    # 试运行（查看会晋升哪些）
    result = auto_promote(dry_run=True)
    
    # 实际执行
    result = auto_promote(dry_run=False)
    """
    if workspace_path is None:
        workspace_path = "/root/.openclaw/workspace-cognimate"
    
    promoter = LearningPromoter(workspace_path)
    return promoter.run_promotion(dry_run)


if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print("🚀 CogniMate 学习记录自动晋升")
    print("=" * 60)
    print()
    
    result = auto_promote(dry_run=dry_run)
    
    print("=" * 60)
    print(f"📊 扫描记录: {result['total_scanned']}")
    print(f"✅ 可晋升: {result['promotable_count']}")
    print(f"📝 已晋升: {len(result['promoted'])}")
    print(f"⏭️  跳过: {len(result['skipped'])}")
    print("=" * 60)
