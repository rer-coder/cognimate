#!/usr/bin/env python3
"""
CogniMate 工具服务器 - 学习记录模块
提供学习记录相关的 API 端点
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from learning_logger import get_logger

router = APIRouter(prefix="/tools")

# 获取学习记录器实例
logger = get_logger()


@router.post("/log_learning")
async def log_learning(request: Request):
    """
    记录学习/纠正/最佳实践
    
    请求体示例:
    {
        "function_name": "log_learning",
        "arguments": {
            "category": "correction",  # correction, knowledge_gap, best_practice
            "summary": "简短描述",
            "details": "详细内容",
            "suggested_action": "建议操作",
            "priority": "medium",  # low, medium, high, critical
            "area": "general",  # frontend, backend, config, workflow
            "source": "user_feedback",
            "tags": ["tag1", "tag2"],
            "related_files": "path/to/file"
        }
    }
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        result = logger.log_learning(arguments)
        
        return {
            "result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {
            "result": {"error": str(e)},
            "status": "error"
        }


@router.post("/log_error")
async def log_error(request: Request):
    """
    记录错误
    
    请求体示例:
    {
        "function_name": "log_error",
        "arguments": {
            "summary": "错误描述",
            "details": "错误详情和上下文",
            "suggested_action": "修复建议",
            "priority": "high",
            "area": "backend",
            "source": "tool_execution",
            "tags": ["error", "api"]
        }
    }
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        result = logger.log_error(arguments)
        
        return {
            "result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {
            "result": {"error": str(e)},
            "status": "error"
        }


@router.post("/log_feature_request")
async def log_feature_request(request: Request):
    """
    记录功能请求
    
    请求体示例:
    {
        "function_name": "log_feature_request",
        "arguments": {
            "summary": "想要的功能",
            "details": "功能描述和使用场景",
            "suggested_action": "实现思路",
            "priority": "medium",
            "area": "frontend",
            "source": "user_request",
            "tags": ["feature", "enhancement"]
        }
    }
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        result = logger.log_feature_request(arguments)
        
        return {
            "result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {
            "result": {"error": str(e)},
            "status": "error"
        }


@router.post("/query_learnings")
async def query_learnings(request: Request):
    """
    查询学习记录
    
    请求体示例:
    {
        "function_name": "query_learnings",
        "arguments": {
            "query": "搜索关键词",
            "area": "config",
            "status": "pending",
            "limit": 5
        }
    }
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        results = logger.query_learnings(
            query=arguments.get("query", ""),
            area=arguments.get("area", ""),
            status=arguments.get("status", ""),
            limit=arguments.get("limit", 10)
        )
        
        return {
            "result": {
                "learnings": results,
                "count": len(results)
            },
            "status": "success"
        }
    except Exception as e:
        return {
            "result": {"error": str(e)},
            "status": "error"
        }


@router.post("/get_learning_stats")
async def get_learning_stats(request: Request):
    """
    获取学习记录统计
    
    请求体示例:
    {
        "function_name": "get_learning_stats",
        "arguments": {}
    }
    """
    try:
        stats = logger.get_stats()
        
        return {
            "result": stats,
            "status": "success"
        }
    except Exception as e:
        return {
            "result": {"error": str(e)},
            "status": "error"
        }


# 便捷函数 - 供 CogniMate 直接调用
def quick_log_learning(category: str, summary: str, details: str = "", 
                       suggested_action: str = "", tags: list = None):
    """快速记录学习"""
    if tags is None:
        tags = []
    
    return logger.log_learning({
        "category": category,
        "summary": summary,
        "details": details,
        "suggested_action": suggested_action,
        "tags": tags,
        "source": "cognimate_auto"
    })


def quick_log_error(summary: str, details: str = "", suggested_action: str = ""):
    """快速记录错误"""
    return logger.log_error({
        "summary": summary,
        "details": details,
        "suggested_action": suggested_action,
        "priority": "high",
        "tags": ["error"],
        "source": "cognimate_auto"
    })


def quick_log_feature(summary: str, details: str = ""):
    """快速记录功能请求"""
    return logger.log_feature_request({
        "summary": summary,
        "details": details,
        "tags": ["feature_request"],
        "source": "user_request"
    })
