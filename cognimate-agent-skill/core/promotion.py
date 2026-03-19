#!/usr/bin/env python3
"""
CogniMate Agent - Promotion System
Automatically promotes effective learnings to permanent memory
"""

import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

class LearningPromoter:
    """Automatically promotes learnings to permanent memory files"""
    
    def __init__(self, workspace_path: str = None):
        if workspace_path is None:
            workspace_path = os.getenv("OPENCLAW_WORKSPACE", os.getcwd())
        
        self.workspace = Path(workspace_path)
        self.learnings_dir = self.workspace / ".learnings"
        self.user_file = self.workspace / "USER.md"
        self.agents_file = self.workspace / "AGENTS.md"
        
        # Promotion thresholds
        self.thresholds = {
            "min_occurrences": 2,
            "max_age_days": 30,
            "min_priority": "medium"
        }
    
    def _read_learnings_file(self, filename: str) -> List[Dict]:
        """Read learning records file"""
        filepath = self.learnings_dir / filename
        if not filepath.exists():
            return []
        
        content = filepath.read_text(encoding='utf-8')
        entries = []
        
        raw_entries = content.split('---')
        
        for entry in raw_entries:
            if not entry.strip():
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
            "source": "",
            "logged_date": None
        }
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('## ['):
                match = re.search(r'## \[(.+?)\] (.+)', line)
                if match:
                    result["id"] = match.group(1)
                    result["category"] = match.group(2)
            
            elif line.startswith('**Logged**:'):
                date_str = line.split(':', 1)[1].strip()
                result["logged_date"] = self._parse_date(date_str)
            elif line.startswith('**Priority**:'):
                result["priority"] = line.split(':', 1)[1].strip()
            elif line.startswith('**Status**:'):
                result["status"] = line.split(':', 1)[1].strip()
            elif line.startswith('**Area**:'):
                result["area"] = line.split(':', 1)[1].strip()
            
            elif line == '### Summary':
                current_field = 'summary'
            elif line == '### Details':
                current_field = 'details'
            elif line == '### Suggested Action':
                current_field = 'suggested_action'
            
            elif 'current_field' in dir() and line and not line.startswith('#') and not line.startswith('-') and not line.startswith('**'):
                if current_field in ['summary', 'details', 'suggested_action']:
                    if result[current_field]:
                        result[current_field] += ' ' + line
                    else:
                        result[current_field] = line
            
            elif line.startswith('- Tags:'):
                tags_str = line.split(':', 1)[1].strip()
                result["tags"] = [t.strip() for t in tags_str.split(',')]
            elif line.startswith('- Source:'):
                result["source"] = line.split(':', 1)[1].strip()
        
        return result if result["id"] else None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string"""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(date_str[:10], "%Y-%m-%d")
            except:
                return None
    
    def _is_promotable(self, entry: Dict) -> Tuple[bool, str]:
        """Check if entry should be promoted"""
        if entry.get("status") not in ["pending", "resolved"]:
            return False, "Status not pending/resolved"
        
        priority = entry.get("priority", "medium")
        priority_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        min_rank = priority_rank.get(self.thresholds["min_priority"], 2)
        
        if priority_rank.get(priority, 0) < min_rank:
            return False, f"Priority {priority} too low"
        
        logged_date = entry.get("logged_date")
        if logged_date:
            try:
                now = datetime.now(timezone.utc) if logged_date.tzinfo else datetime.now()
                if logged_date.tzinfo is None and now.tzinfo:
                    logged_date = logged_date.replace(tzinfo=now.tzinfo)
                age_days = (now - logged_date).days
                if age_days > self.thresholds["max_age_days"]:
                    return False, f"Too old ({age_days} days)"
            except:
                pass
        
        if priority in ["critical", "high"]:
            return True, "High priority"
        
        if entry.get("source") == "user_feedback":
            return True, "User feedback"
        
        if entry.get("category") == "correction":
            return True, "User correction"
        
        return False, "Does not meet criteria"
    
    def identify_promotable_learnings(self) -> List[Dict]:
        """Identify learnings ready for promotion"""
        promotable = []
        learnings = self._read_learnings_file("LEARNINGS.md")
        
        for entry in learnings:
            should_promote, reason = self._is_promotable(entry)
            if should_promote:
                entry["promote_reason"] = reason
                promotable.append(entry)
        
        return promotable
    
    def promote_to_user_md(self, entry: Dict) -> bool:
        """Promote to USER.md"""
        try:
            if not self.user_file.exists():
                return False
            
            content = self.user_file.read_text(encoding='utf-8')
            summary = entry.get("summary", "")
            
            # Format based on category
            category = entry.get("category", "")
            if category == "preference":
                formatted = f"- **Preference**: {summary}"
            elif category == "correction":
                formatted = f"- **Correction**: {summary}"
            else:
                formatted = f"- {summary}"
            
            # Find section
            area = entry.get("area", "general")
            section_map = {
                "schedule": "## Schedule Preferences",
                "goal": "## Goals",
                "sentiment": "## Communication Style",
                "general": "## Preferences"
            }
            section = section_map.get(area, "## Preferences")
            
            if section in content:
                lines = content.split('\n')
                new_lines = []
                inserted = False
                
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    if not inserted and line.startswith(section):
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() == '' or lines[j].startswith('##'):
                                new_lines.append(f"\n### Auto-added from learnings")
                                new_lines.append(formatted)
                                new_lines.append(f"<!-- LRN: {entry.get('id')} -->")
                                inserted = True
                                break
                
                if inserted:
                    content = '\n'.join(new_lines)
            else:
                content += f"\n\n{section}\n{formatted}\n<!-- LRN: {entry.get('id')} -->"
            
            self.user_file.write_text(content, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"Promotion failed: {e}")
            return False
    
    def update_learning_status(self, entry_id: str, new_status: str = "promoted") -> bool:
        """Update learning record status"""
        try:
            filepath = self.learnings_dir / "LEARNINGS.md"
            if not filepath.exists():
                return False
            
            content = filepath.read_text(encoding='utf-8')
            pattern = rf'(## \[{re.escape(entry_id)}\].*?)\*\*Status\*\*: \w+'
            replacement = rf'\1**Status**: {new_status}'
            
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            if new_content != content:
                filepath.write_text(new_content, encoding='utf-8')
                return True
            
            return False
            
        except Exception as e:
            print(f"Status update failed: {e}")
            return False
    
    def run_promotion(self, dry_run: bool = False) -> Dict:
        """Run promotion process"""
        promotable = self.identify_promotable_learnings()
        
        result = {
            "total_scanned": len(self._read_learnings_file("LEARNINGS.md")),
            "promotable_count": len(promotable),
            "promoted": [],
            "skipped": []
        }
        
        for entry in promotable:
            entry_id = entry.get("id")
            area = entry.get("area")
            reason = entry.get("promote_reason")
            
            print(f"Promoting: [{entry_id}] {entry.get('summary', '')[:50]}...")
            print(f"  Reason: {reason}")
            
            if not dry_run:
                success = self.promote_to_user_md(entry)
                
                if success:
                    self.update_learning_status(entry_id, "promoted")
                    result["promoted"].append({
                        "id": entry_id,
                        "summary": entry.get("summary", "")
                    })
                    print(f"  ✅ Promoted")
                else:
                    result["skipped"].append({"id": entry_id, "reason": "Failed"})
                    print(f"  ❌ Failed")
            else:
                print(f"  [DRY RUN] Would promote to USER.md")
            
            print()
        
        return result


def auto_promote(workspace_path: str = None, dry_run: bool = False) -> Dict:
    """Auto-run promotion"""
    if workspace_path is None:
        workspace_path = os.getenv("OPENCLAW_WORKSPACE", os.getcwd())
    
    promoter = LearningPromoter(workspace_path)
    return promoter.run_promotion(dry_run)


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print("🚀 CogniMate Agent - Auto Promotion")
    print("=" * 60)
    
    result = auto_promote(dry_run=dry_run)
    
    print(f"Scanned: {result['total_scanned']}")
    print(f"Promotable: {result['promotable_count']}")
    print(f"Promoted: {len(result['promoted'])}")
