#!/usr/bin/env python3
"""
CogniMate 决策辅助模块
在决策前自动查询学习记录，提供个性化建议
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class DecisionHelper:
    """决策辅助器 - 在决策前查询相关学习记录"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.learnings_file = self.workspace / ".learnings" / "LEARNINGS.md"
        self.user_file = self.workspace / "USER.md"
    
    def _read_learnings(self) -> List[Dict]:
        """读取学习记录文件"""
        if not self.learnings_file.exists():
            return []
        
        content = self.learnings_file.read_text(encoding='utf-8')
        entries = []
        
        # 按条目分割
        raw_entries = content.split('---')
        
        for entry in raw_entries:
            if not entry.strip() or '## [' not in entry:
                continue
            
            # 解析条目
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
            "source": ""
        }
        
        current_field = None
        
        for line in lines:
            line = line.strip()
            
            # 解析 ID 和 category
            if line.startswith('## ['):
                match = re.search(r'## \[(.+?)\] (.+)', line)
                if match:
                    result["id"] = match.group(1)
                    result["category"] = match.group(2)
            
            # 解析字段
            elif line.startswith('**Logged**:'):
                result["logged"] = line.split(':', 1)[1].strip()
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
            elif line == '### Metadata':
                current_field = 'metadata'
            
            # 收集内容
            elif current_field and line and not line.startswith('#') and not line.startswith('-'):
                if current_field in ['summary', 'details', 'suggested_action']:
                    if result[current_field]:
                        result[current_field] += '\n' + line
                    else:
                        result[current_field] = line
            
            # 解析标签
            elif line.startswith('- Tags:'):
                tags_str = line.split(':', 1)[1].strip()
                result["tags"] = [t.strip() for t in tags_str.split(',')]
        
        return result if result["id"] else None
    
    def query_relevant_learnings(self, context: str, area: str = "") -> List[Dict]:
        """
        查询与当前决策相关的学习记录
        
        Args:
            context: 决策上下文（如"提醒时间"、"运动计划"）
            area: 领域过滤
        
        Returns:
            相关的学习记录列表
        """
        all_learnings = self._read_learnings()
        relevant = []
        
        # 提取关键词
        keywords = self._extract_keywords(context)
        
        for entry in all_learnings:
            # 只考虑 pending 或 resolved 的记录
            if entry.get("status") not in ["pending", "resolved"]:
                continue
            
            # 领域匹配
            if area and entry.get("area") != area:
                continue
            
            # 关键词匹配
            content = f"{entry.get('summary', '')} {entry.get('details', '')} {' '.join(entry.get('tags', []))}"
            score = self._calculate_relevance(content, keywords)
            
            if score > 0:
                entry["relevance_score"] = score
                relevant.append(entry)
        
        # 按相关性和优先级排序
        relevant.sort(key=lambda x: (
            x.get("relevance_score", 0),
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.get("priority"), 0)
        ), reverse=True)
        
        return relevant[:3]  # 返回最相关的3条
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        keywords = []
        
        # 领域关键词映射
        keyword_map = {
            "提醒": ["提醒", "时间", "闹钟", "通知"],
            "运动": ["运动", "跑步", "健身", "锻炼", "减重"],
            "日程": ["日程", "安排", "计划", "会议"],
            "目标": ["目标", "减重", "减肥", "计划"],
            "情感": ["情感", "心情", "状态", "鼓励"]
        }
        
        for domain, words in keyword_map.items():
            if any(word in text for word in words):
                keywords.extend(words)
        
        # 添加原文中的词
        keywords.extend(text.split())
        
        return list(set(keywords))
    
    def _calculate_relevance(self, content: str, keywords: List[str]) -> int:
        """计算相关性得分"""
        score = 0
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                score += 1
        
        return score
    
    def get_contextual_advice(self, context: str, area: str = "") -> Dict:
        """
        获取情境化建议
        
        Returns:
            {
                "has_learnings": bool,
                "learnings": List[Dict],
                "advice": str,
                "action_items": List[str]
            }
        """
        learnings = self.query_relevant_learnings(context, area)
        
        if not learnings:
            return {
                "has_learnings": False,
                "learnings": [],
                "advice": "",
                "action_items": []
            }
        
        # 生成建议
        advice_parts = []
        action_items = []
        
        for entry in learnings:
            category = entry.get("category", "")
            
            if category == "correction":
                advice_parts.append(f"根据之前的纠正：{entry.get('summary', '')}")
                action_items.append(entry.get('suggested_action', ''))
            
            elif category == "best_practice":
                advice_parts.append(f"最佳实践：{entry.get('summary', '')}")
            
            elif category == "knowledge_gap":
                advice_parts.append(f"注意：{entry.get('summary', '')}")
        
        return {
            "has_learnings": True,
            "learnings": learnings,
            "advice": "\n".join(advice_parts),
            "action_items": [a for a in action_items if a]
        }


# ============ 集成到决策流程 ============

def before_decision(context: str, area: str = "") -> Dict:
    """
    决策前调用 - 查询相关学习记录
    
    使用示例:
    
    # 生成提醒前
    context = "用户询问明天提醒时间"
    learnings = before_decision(context, area="schedule")
    
    if learnings["has_learnings"]:
        # 应用学习到的偏好
        pass
    """
    helper = DecisionHelper("/root/.openclaw/workspace-cognimate")
    return helper.get_contextual_advice(context, area)


if __name__ == "__main__":
    # 测试
    helper = DecisionHelper("/root/.openclaw/workspace-cognimate")
    
    print("测试1: 查询提醒相关的学习")
    result = helper.get_contextual_advice("提醒时间", area="schedule")
    print(f"找到学习: {result['has_learnings']}")
    if result['has_learnings']:
        print(f"建议: {result['advice'][:100]}...")
    
    print("\n测试2: 查询运动相关的学习")
    result = helper.get_contextual_advice("运动计划", area="goal")
    print(f"找到学习: {result['has_learnings']}")
