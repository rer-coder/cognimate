#!/usr/bin/env python3
"""
CogniMate Agent - Learning Logger
Universal learning record system for personal AI companions
"""

import json
import os
import re
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class LearningLogger:
    """
    Universal learning logger for AI companions
    Records corrections, errors, best practices, and feature requests
    """
    
    def __init__(self, workspace_path: str = None):
        """
        Initialize the learning logger
        
        Args:
            workspace_path: Path to workspace. If None, uses OPENCLAW_WORKSPACE env var
        """
        if workspace_path is None:
            workspace_path = os.getenv("OPENCLAW_WORKSPACE", os.getcwd())
        
        self.workspace = Path(workspace_path)
        self.learnings_dir = self.workspace / ".learnings"
        
        # Ensure directory exists
        self.learnings_dir.mkdir(exist_ok=True)
        
        # File paths
        self.learnings_file = self.learnings_dir / "LEARNINGS.md"
        self.errors_file = self.learnings_dir / "ERRORS.md"
        self.features_file = self.learnings_dir / "FEATURE_REQUESTS.md"
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize learning files with headers if they don't exist"""
        headers = {
            self.learnings_file: "# Learnings Log\n\n<!-- Corrections, knowledge gaps, best practices -->\n\n",
            self.errors_file: "# Errors Log\n\n<!-- Command failures, exceptions -->\n\n",
            self.features_file: "# Feature Requests Log\n\n<!-- User-requested capabilities -->\n\n"
        }
        
        for filepath, header in headers.items():
            if not filepath.exists():
                filepath.write_text(header, encoding='utf-8')
    
    def _generate_id(self, prefix: str) -> str:
        """Generate record ID: TYPE-YYYYMMDD-XXX"""
        date_str = datetime.now().strftime("%Y%m%d")
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        return f"{prefix}-{date_str}-{suffix}"
    
    def _format_entry(self, entry_type: str, data: Dict) -> str:
        """Format learning entry"""
        timestamp = datetime.now().isoformat()
        
        # Determine prefix based on type
        prefix_map = {
            "learning": "LRN",
            "correction": "LRN",
            "knowledge_gap": "LRN",
            "best_practice": "LRN",
            "preference": "LRN",
            "error": "ERR",
            "feature_request": "FEAT"
        }
        prefix = prefix_map.get(entry_type, "LRN")
        entry_id = data.get("id", self._generate_id(prefix))
        
        # Build entry
        entry = f"""## [{entry_id}] {data.get('category', entry_type)}

**Logged**: {timestamp}
**Priority**: {data.get('priority', 'medium')}
**Status**: {data.get('status', 'pending')}
**Area**: {data.get('area', 'general')}

### Summary
{data.get('summary', '')}

### Details
{data.get('details', '')}

### Suggested Action
{data.get('suggested_action', '')}

### Metadata
- Source: {data.get('source', 'unknown')}
- Related Files: {data.get('related_files', 'N/A')}
- Tags: {', '.join(data.get('tags', []))}

---

"""
        return entry
    
    def log_learning(self, data: Dict) -> Dict:
        """
        Log learning/correction/best practice
        
        Args:
            data: Dictionary with keys:
                - category: Type of learning (correction, best_practice, etc.)
                - summary: Brief description
                - details: Full context
                - suggested_action: Recommended fix
                - priority: low/medium/high/critical
                - area: frontend/backend/config/workflow/etc.
                - source: user_feedback/error/etc.
                - tags: List of tags
                - related_files: Related file paths
        
        Returns:
            Dict with success status and entry info
        """
        try:
            entry = self._format_entry("learning", data)
            
            # Append to file
            with open(self.learnings_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return {
                "success": True,
                "id": data.get("id"),
                "file": str(self.learnings_file),
                "message": "Learning recorded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def log_error(self, data: Dict) -> Dict:
        """Log error"""
        try:
            entry = self._format_entry("error", data)
            
            with open(self.errors_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return {
                "success": True,
                "id": data.get("id"),
                "file": str(self.errors_file),
                "message": "Error recorded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def log_feature_request(self, data: Dict) -> Dict:
        """Log feature request"""
        try:
            entry = self._format_entry("feature_request", data)
            
            with open(self.features_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return {
                "success": True,
                "id": data.get("id"),
                "file": str(self.features_file),
                "message": "Feature request recorded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def query_learnings(self, query: str = "", area: str = "", 
                       status: str = "", limit: int = 10) -> List[Dict]:
        """Query learning records"""
        results = []
        
        # Read all learning files
        files = [self.learnings_file, self.errors_file, self.features_file]
        
        for file_path in files:
            if not file_path.exists():
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple parsing - split by entries
            entries = content.split('---')
            
            for entry in entries:
                if not entry.strip():
                    continue
                    
                # Filter logic
                if query and query.lower() not in entry.lower():
                    continue
                if area and f"**Area**: {area}" not in entry:
                    continue
                if status and f"**Status**: {status}" not in entry:
                    continue
                
                results.append({
                    "content": entry.strip(),
                    "source": file_path.name
                })
        
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """Get statistics"""
        stats = {
            "learnings": 0,
            "errors": 0,
            "features": 0,
            "total": 0
        }
        
        if self.learnings_file.exists():
            content = self.learnings_file.read_text()
            stats["learnings"] = content.count("## [")
        
        if self.errors_file.exists():
            content = self.errors_file.read_text()
            stats["errors"] = content.count("## [")
        
        if self.features_file.exists():
            content = self.features_file.read_text()
            stats["features"] = content.count("## [")
        
        stats["total"] = stats["learnings"] + stats["errors"] + stats["features"]
        
        return stats


# Quick functions for direct use
def get_logger(workspace_path: str = None) -> LearningLogger:
    """Get learning logger instance"""
    return LearningLogger(workspace_path)


def quick_log(category: str, summary: str, details: str = "", 
              suggested_action: str = "", tags: list = None):
    """Quick log learning"""
    if tags is None:
        tags = []
    
    logger = get_logger()
    return logger.log_learning({
        "category": category,
        "summary": summary,
        "details": details,
        "suggested_action": suggested_action,
        "tags": tags,
        "source": "auto"
    })


if __name__ == "__main__":
    # Test
    logger = get_logger()
    
    result = logger.log_learning({
        "category": "best_practice",
        "summary": "Test learning record",
        "details": "This is a test entry",
        "suggested_action": "Observe the effect",
        "source": "test",
        "tags": ["test"]
    })
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\nStats:", logger.get_stats())
