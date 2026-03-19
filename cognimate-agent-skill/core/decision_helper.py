#!/usr/bin/env python3
"""
CogniMate Agent - Decision Helper
Provides contextual advice based on past learnings before making decisions
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class DecisionHelper:
    """
    Decision helper - queries relevant learnings before making decisions
    """
    
    def __init__(self, workspace_path: str = None):
        if workspace_path is None:
            workspace_path = os.getenv("OPENCLAW_WORKSPACE", os.getcwd())
        
        self.workspace = Path(workspace_path)
        self.learnings_file = self.workspace / ".learnings" / "LEARNINGS.md"
    
    def _read_learnings(self) -> List[Dict]:
        """Read learning records"""
        if not self.learnings_file.exists():
            return []
        
        content = self.learnings_file.read_text(encoding='utf-8')
        entries = []
        
        # Split by entries
        raw_entries = content.split('---')
        
        for entry in raw_entries:
            if not entry.strip() or '## [' not in entry:
                continue
            
            parsed = self._parse_entry(entry)
            if parsed:
                entries.append(parsed)
        
        return entries
    
    def _parse_entry(self, entry: str) -> Optional[Dict]:
        """Parse single learning entry"""
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
            
            # Parse ID and category
            if line.startswith('## ['):
                match = re.search(r'## \[(.+?)\] (.+)', line)
                if match:
                    result["id"] = match.group(1)
                    result["category"] = match.group(2)
            
            # Parse fields
            elif line.startswith('**Logged**:'):
                result["logged"] = line.split(':', 1)[1].strip()
            elif line.startswith('**Priority**:'):
                result["priority"] = line.split(':', 1)[1].strip()
            elif line.startswith('**Status**:'):
                result["status"] = line.split(':', 1)[1].strip()
            elif line.startswith('**Area**:'):
                result["area"] = line.split(':', 1)[1].strip()
            
            # Parse sections
            elif line == '### Summary':
                current_field = 'summary'
            elif line == '### Details':
                current_field = 'details'
            elif line == '### Suggested Action':
                current_field = 'suggested_action'
            elif line == '### Metadata':
                current_field = 'metadata'
            
            # Collect content
            elif current_field and line and not line.startswith('#') and not line.startswith('-'):
                if current_field in ['summary', 'details', 'suggested_action']:
                    if result[current_field]:
                        result[current_field] += '\n' + line
                    else:
                        result[current_field] = line
            
            # Parse tags
            elif line.startswith('- Tags:'):
                tags_str = line.split(':', 1)[1].strip()
                result["tags"] = [t.strip() for t in tags_str.split(',')]
        
        return result if result["id"] else None
    
    def query_relevant_learnings(self, context: str, area: str = "") -> List[Dict]:
        """
        Query learnings relevant to current decision
        
        Args:
            context: Decision context (e.g., "reminder time", "workout plan")
            area: Domain filter
        
        Returns:
            List of relevant learning records
        """
        all_learnings = self._read_learnings()
        relevant = []
        
        # Extract keywords
        keywords = self._extract_keywords(context)
        
        for entry in all_learnings:
            # Only consider pending or resolved records
            if entry.get("status") not in ["pending", "resolved"]:
                continue
            
            # Area matching
            if area and entry.get("area") != area:
                continue
            
            # Keyword matching
            content = f"{entry.get('summary', '')} {entry.get('details', '')} {' '.join(entry.get('tags', []))}"
            score = self._calculate_relevance(content, keywords)
            
            if score > 0:
                entry["relevance_score"] = score
                relevant.append(entry)
        
        # Sort by relevance and priority
        relevant.sort(key=lambda x: (
            x.get("relevance_score", 0),
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.get("priority"), 0)
        ), reverse=True)
        
        return relevant[:3]  # Return top 3
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords"""
        keywords = []
        
        # Domain keyword mapping
        keyword_map = {
            "reminder": ["reminder", "time", "alarm", "notification", "提醒", "时间"],
            "workout": ["workout", "running", "exercise", "fitness", "运动", "跑步", "健身"],
            "schedule": ["schedule", "plan", "meeting", "日程", "安排", "会议"],
            "goal": ["goal", "target", "weight", "目标", "减重", "减肥"],
            "emotion": ["emotion", "mood", "feel", "情感", "心情", "状态"]
        }
        
        for domain, words in keyword_map.items():
            if any(word in text.lower() for word in words):
                keywords.extend(words)
        
        # Add original words
        keywords.extend(text.split())
        
        return list(set(keywords))
    
    def _calculate_relevance(self, content: str, keywords: List[str]) -> int:
        """Calculate relevance score"""
        score = 0
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                score += 1
        
        return score
    
    def get_contextual_advice(self, context: str, area: str = "") -> Dict:
        """
        Get contextual advice based on past learnings
        
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
        
        # Generate advice
        advice_parts = []
        action_items = []
        
        for entry in learnings:
            category = entry.get("category", "")
            
            if category == "correction":
                advice_parts.append(f"Based on previous correction: {entry.get('summary', '')}")
                action_items.append(entry.get('suggested_action', ''))
            
            elif category == "best_practice":
                advice_parts.append(f"Best practice: {entry.get('summary', '')}")
            
            elif category == "knowledge_gap":
                advice_parts.append(f"Note: {entry.get('summary', '')}")
            
            elif category == "preference":
                advice_parts.append(f"User preference: {entry.get('summary', '')}")
                action_items.append(entry.get('suggested_action', ''))
        
        return {
            "has_learnings": True,
            "learnings": learnings,
            "advice": "\n".join(advice_parts),
            "action_items": [a for a in action_items if a]
        }


# Convenience function for use in decisions
def before_decision(context: str, area: str = "") -> Dict:
    """
    Call before decision - query relevant learnings
    
    Usage:
        # Before generating reminder
        context = "User asking about reminder time"
        learnings = before_decision(context, area="schedule")
        
        if learnings["has_learnings"]:
            # Apply learned preferences
            pass
    """
    workspace = os.getenv("OPENCLAW_WORKSPACE", os.getcwd())
    helper = DecisionHelper(workspace)
    return helper.get_contextual_advice(context, area)


if __name__ == "__main__":
    # Test
    helper = DecisionHelper()
    
    print("Test 1: Query reminder-related learnings")
    result = helper.get_contextual_advice("reminder time", area="schedule")
    print(f"Found learnings: {result['has_learnings']}")
    if result['has_learnings']:
        print(f"Advice: {result['advice'][:100]}...")
    
    print("\nTest 2: Query workout-related learnings")
    result = helper.get_contextual_advice("workout plan", area="goal")
    print(f"Found learnings: {result['has_learnings']}")
