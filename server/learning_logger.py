#!/usr/bin/env python3
"""
CogniMate 学习记录模块
实现 Self-Improving-Agent 的基础记录功能
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class LearningLogger:
    """学习记录器 - 记录用户纠正、错误、最佳实践等"""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.learnings_dir = self.workspace / ".learnings"
        
        # 确保目录存在
        self.learnings_dir.mkdir(exist_ok=True)
        
        # 文件路径
        self.learnings_file = self.learnings_dir / "LEARNINGS.md"
        self.errors_file = self.learnings_dir / "ERRORS.md"
        self.features_file = self.learnings_dir / "FEATURE_REQUESTS.md"
    
    def _generate_id(self, prefix: str) -> str:
        """生成记录ID: TYPE-YYYYMMDD-XXX"""
        date_str = datetime.now().strftime("%Y%m%d")
        # 简单使用随机3字符
        import random
        import string
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        return f"{prefix}-{date_str}-{suffix}"
    
    def _format_entry(self, entry_type: str, data: Dict) -> str:
        """格式化记录条目"""
        timestamp = datetime.now().isoformat()
        
        # 根据类型确定前缀
        prefix_map = {
            "learning": "LRN",
            "correction": "LRN",
            "knowledge_gap": "LRN",
            "best_practice": "LRN",
            "error": "ERR",
            "feature_request": "FEAT"
        }
        prefix = prefix_map.get(entry_type, "LRN")
        entry_id = data.get("id", self._generate_id(prefix))
        
        # 构建条目
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
        """记录学习/纠正/知识缺口/最佳实践"""
        try:
            entry = self._format_entry("learning", data)
            
            # 追加到文件
            with open(self.learnings_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return {
                "success": True,
                "id": data.get("id"),
                "file": str(self.learnings_file),
                "message": "学习记录已保存"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def log_error(self, data: Dict) -> Dict:
        """记录错误"""
        try:
            entry = self._format_entry("error", data)
            
            with open(self.errors_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return {
                "success": True,
                "id": data.get("id"),
                "file": str(self.errors_file),
                "message": "错误记录已保存"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def log_feature_request(self, data: Dict) -> Dict:
        """记录功能请求"""
        try:
            entry = self._format_entry("feature_request", data)
            
            with open(self.features_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return {
                "success": True,
                "id": data.get("id"),
                "file": str(self.features_file),
                "message": "功能请求已记录"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def query_learnings(self, query: str = "", area: str = "", 
                       status: str = "", limit: int = 10) -> List[Dict]:
        """查询学习记录"""
        results = []
        
        # 读取所有学习记录
        files = [self.learnings_file, self.errors_file, self.features_file]
        
        for file_path in files:
            if not file_path.exists():
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单解析 - 按条目分割
            entries = content.split('---')
            
            for entry in entries:
                if not entry.strip():
                    continue
                    
                # 过滤逻辑
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
        """获取统计信息"""
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


# 便捷函数 - 供其他模块调用
def get_logger(workspace_path: str = None) -> LearningLogger:
    """获取学习记录器实例"""
    if workspace_path is None:
        # 默认使用 CogniMate 工作区
        workspace_path = "/root/.openclaw/workspace-cognimate"
    return LearningLogger(workspace_path)


if __name__ == "__main__":
    # 测试
    logger = get_logger()
    
    # 测试记录学习
    result = logger.log_learning({
        "category": "correction",
        "summary": "测试学习记录",
        "details": "这是一个测试条目",
        "suggested_action": "观察效果",
        "source": "test",
        "tags": ["test"]
    })
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n统计:", logger.get_stats())
