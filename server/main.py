#!/usr/bin/env python3
"""
CogniMate 本地服务器 - 完整版
整合记忆管理、情感分析、学习记录等功能
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from learning_logger import get_logger
from decision_helper import DecisionHelper
from promotion import LearningPromoter
from goal_tracker import GoalTracker, get_tracker
from checkin_tracker import CheckinTracker, get_tracker as get_checkin_tracker, CheckinStatus
from feishu_messenger import send_message_to_user

app = FastAPI(title="CogniMate Server", version="2.3.0")

# 初始化组件
learning_logger = get_logger()
decision_helper = DecisionHelper("/root/.openclaw/workspace-cognimate")
goal_tracker = get_tracker()
checkin_tracker = get_checkin_tracker()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化学习记录器
learning_logger = get_logger()

# ============ 数据库初始化 ============
def init_db():
    """初始化 SQLite 数据库"""
    conn = sqlite3.connect('/root/.openclaw/workspace-cognimate/cognimate.db')
    cursor = conn.cursor()
    
    # 日程表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            event TEXT NOT NULL,
            location TEXT,
            type TEXT DEFAULT 'regular',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 目标表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_value TEXT,
            current_value TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 状态记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            energy_level TEXT,
            mood TEXT,
            note TEXT
        )
    ''')
    
    # 用户交互记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_input TEXT,
            sentiment TEXT,
            energy_level TEXT,
            response_summary TEXT
        )
    ''')
    
    # 打卡记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            type TEXT NOT NULL,
            title TEXT,
            scheduled_time TIMESTAMP NOT NULL,
            actual_time TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'pending',
            note TEXT,
            reminder_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 提醒表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            type TEXT NOT NULL,
            title TEXT,
            scheduled_time TIMESTAMP NOT NULL,
            message TEXT,
            is_sent BOOLEAN DEFAULT 0,
            checkin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 打卡统计表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            date TEXT NOT NULL,
            total_count INTEGER DEFAULT 0,
            completed_count INTEGER DEFAULT 0,
            missed_count INTEGER DEFAULT 0,
            skipped_count INTEGER DEFAULT 0,
            completion_rate REAL DEFAULT 0.0,
            streak_days INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, date)
        )
    ''')
    
    # 待发送消息队列（用于失败重试）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            last_retry_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            error_msg TEXT
        )
    ''')
    
    # 消息发送日志（用于统计和排查）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            message_type TEXT,
            content_preview TEXT,
            scheduled_time TIMESTAMP,
            actual_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            error_msg TEXT,
            latency_ms INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")
    print("   - 日程表、目标表、状态表")
    print("   - 打卡系统（checkin, stats）")
    print("   - 消息队列（pending_messages）")
    print("   - 消息日志（message_logs）")


# ============ 工具 API ============

@app.post("/tools/query_memory")
async def query_memory(request: Request):
    """查询记忆库"""
    try:
        data = await request.json()
        query = data.get("arguments", {}).get("query", "")
        
        conn = sqlite3.connect('/root/.openclaw/workspace-cognimate/cognimate.db')
        cursor = conn.cursor()
        result = {}
        
        # 解析查询意图
        today = datetime.now().strftime("%Y-%m-%d")
        
        if "日程" in query or "安排" in query:
            # 查询日程
            target_date = today
            if "明天" in query:
                from datetime import timedelta
                target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            cursor.execute(
                "SELECT * FROM schedules WHERE date=? ORDER BY time",
                (target_date,)
            )
            rows = cursor.fetchall()
            result["schedules"] = [
                {"id": r[0], "date": r[1], "time": r[2], "event": r[3], 
                 "location": r[4], "type": r[5]} for r in rows
            ]
        
        elif "目标" in query:
            cursor.execute("SELECT * FROM goals WHERE status='active'")
            rows = cursor.fetchall()
            result["goals"] = [
                {"id": r[0], "name": r[1], "target": r[2], 
                 "current": r[3], "deadline": r[4]} for r in rows
            ]
        
        conn.close()
        
        return {"result": result, "status": "success"}
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/update_memory")
async def update_memory(request: Request):
    """更新记忆库"""
    try:
        data = await request.json()
        operation = data.get("arguments", {}).get("operation")
        item_data = data.get("arguments", {}).get("data", {})
        
        conn = sqlite3.connect('/root/.openclaw/workspace-cognimate/cognimate.db')
        cursor = conn.cursor()
        
        if operation == "create":
            if "schedule" in item_data:
                s = item_data["schedule"]
                cursor.execute('''
                    INSERT INTO schedules (date, time, event, location, type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (s.get("date"), s.get("time"), s.get("event"), 
                      s.get("location", ""), s.get("type", "regular")))
        
        elif operation == "update":
            if "schedule" in item_data:
                s = item_data["schedule"]
                cursor.execute('''
                    UPDATE schedules SET time=?, event=?, location=?
                    WHERE id=?
                ''', (s.get("time"), s.get("event"), 
                      s.get("location"), s.get("id")))
        
        elif operation == "delete":
            if "schedule_id" in item_data:
                cursor.execute(
                    "DELETE FROM schedules WHERE id=?",
                    (item_data["schedule_id"],)
                )
        
        conn.commit()
        conn.close()
        
        return {"result": {"success": True}, "status": "success"}
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/analyze_sentiment_and_state")
async def analyze_sentiment(request: Request):
    """分析情感和状态"""
    try:
        data = await request.json()
        user_input = data.get("arguments", {}).get("user_input", "")
        
        # 简单的关键词分析
        sentiment = "neutral"
        energy = "medium"
        keywords = []
        
        negative_words = ["累", "疲惫", "难受", "不舒服", "烦", "糟", "难过"]
        positive_words = ["开心", "棒", "好", "兴奋", "期待", "不错", "赞"]
        low_energy_words = ["累", "困", "没精神", "不想动", "疲惫"]
        high_energy_words = ["精神", "充满活力", "兴奋", "干劲"]
        
        for word in negative_words:
            if word in user_input:
                sentiment = "negative"
                keywords.append(word)
        
        for word in positive_words:
            if word in user_input:
                sentiment = "positive"
                keywords.append(word)
        
        for word in low_energy_words:
            if word in user_input:
                energy = "low"
        
        for word in high_energy_words:
            if word in user_input:
                energy = "high"
        
        # 记录到数据库
        conn = sqlite3.connect('/root/.openclaw/workspace-cognimate/cognimate.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO interactions (user_input, sentiment, energy_level)
            VALUES (?, ?, ?)
        ''', (user_input, sentiment, energy))
        conn.commit()
        conn.close()
        
        return {
            "result": {
                "sentiment": sentiment,
                "energy_level": energy,
                "keywords": keywords
            },
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/generate_dynamic_adjustment")
async def generate_adjustment(request: Request):
    """生成动态调整方案 - 决策前查询学习记录"""
    try:
        data = await request.json()
        current_plan = data.get("arguments", {}).get("current_plan", {})
        user_status = data.get("arguments", {}).get("user_status", {})
        
        adjusted_tasks = []
        reason = ""
        impact = ""
        contextual_advice = None
        
        # ====== 决策前查询学习记录 ======
        # 构建查询上下文
        context_parts = []
        if "跑步" in str(current_plan):
            context_parts.append("运动计划调整")
        if "会议" in str(current_plan):
            context_parts.append("日程调整")
        if user_status.get("energy_level") == "low":
            context_parts.append("用户低能量状态")
        
        context = " ".join(context_parts)
        
        # 查询相关学习记录
        if context:
            contextual_advice = decision_helper.get_contextual_advice(context)
            
            if contextual_advice["has_learnings"]:
                # 如果有相关学习，融入调整建议
                advice = contextual_advice.get("advice", "")
                if advice:
                    reason = f"【基于历史学习】{advice}\n\n"
        # =================================
        
        # 根据用户状态生成调整
        if user_status.get("energy_level") == "low":
            if "跑步" in str(current_plan):
                # 检查是否有关于运动调整的学习
                if contextual_advice and contextual_advice["has_learnings"]:
                    # 使用学习到的偏好
                    action_items = contextual_advice.get("action_items", [])
                    if action_items:
                        suggested_action = action_items[0]
                        adjusted_tasks.append({
                            "time": current_plan.get("time"),
                            "new_task": suggested_action,
                            "original": "跑步30分钟"
                        })
                        reason += f"根据之前的经验：{suggested_action}"
                    else:
                        adjusted_tasks.append({
                            "time": current_plan.get("time"),
                            "new_task": "散步20分钟",
                            "original": "跑步30分钟"
                        })
                        reason += "用户能量水平较低，建议降低运动强度，改为轻度散步"
                else:
                    adjusted_tasks.append({
                        "time": current_plan.get("time"),
                        "new_task": "散步20分钟",
                        "original": "跑步30分钟"
                    })
                    reason += "用户能量水平较低，建议降低运动强度，改为轻度散步"
                
                impact = "今日卡路里消耗减少约30%，可通过明日增加10分钟运动弥补"
                
            elif "会议" in str(current_plan):
                adjusted_tasks.append({
                    "time": current_plan.get("time"),
                    "new_task": "线上参会或延后",
                    "original": current_plan.get("event")
                })
                reason += "用户状态不佳，建议减少外出"
                impact = "不影响工作进度，保护用户健康"
        
        return {
            "result": {
                "adjusted_tasks": adjusted_tasks,
                "reason": reason,
                "impact_on_goal": impact,
                "has_contextual_learning": contextual_advice["has_learnings"] if contextual_advice else False,
                "referenced_learnings": len(contextual_advice.get("learnings", [])) if contextual_advice else 0
            },
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


# ============ 学习记录 API ============

@app.post("/tools/log_learning")
async def log_learning(request: Request):
    """记录学习/纠正/最佳实践"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        result = learning_logger.log_learning(arguments)
        
        return {
            "result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/log_error")
async def log_error(request: Request):
    """记录错误"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        result = learning_logger.log_error(arguments)
        
        return {
            "result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/log_feature_request")
async def log_feature_request(request: Request):
    """记录功能请求"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        result = learning_logger.log_feature_request(arguments)
        
        return {
            "result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/query_learnings")
async def query_learnings(request: Request):
    """查询学习记录"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        results = learning_logger.query_learnings(
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
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/get_learning_stats")
async def get_learning_stats(request: Request):
    """获取学习记录统计"""
    try:
        stats = learning_logger.get_stats()
        
        return {
            "result": stats,
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/auto_promote_learnings")
async def auto_promote_learnings(request: Request):
    """
    自动晋升学习记录
    将有效的学习记录晋升到 USER.md / AGENTS.md
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        dry_run = arguments.get("dry_run", False)
        
        promoter = LearningPromoter("/root/.openclaw/workspace-cognimate")
        result = promoter.run_promotion(dry_run=dry_run)
        
        return {
            "result": {
                "message": "试运行完成" if dry_run else "晋升完成",
                "total_scanned": result["total_scanned"],
                "promotable_count": result["promotable_count"],
                "promoted": result["promoted"],
                "skipped": result["skipped"],
                "dry_run": dry_run
            },
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/get_contextual_advice")
async def get_contextual_advice(request: Request):
    """
    获取情境化建议
    在决策前查询相关的学习记录
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        context = arguments.get("context", "")
        area = arguments.get("area", "")
        
        advice = decision_helper.get_contextual_advice(context, area)
        
        return {
            "result": advice,
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


# ============ 目标追踪 API (新增) ============

@app.post("/tools/create_goal")
async def create_goal(request: Request):
    """创建新目标"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        goal_id = goal_tracker.create_goal(
            name=arguments.get("name"),
            target_value=arguments.get("target_value"),
            deadline=arguments.get("deadline")
        )
        
        return {
            "result": {"goal_id": goal_id, "message": "Goal created successfully"},
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/update_goal_progress")
async def update_goal_progress(request: Request):
    """更新目标进度"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        success = goal_tracker.update_goal_progress(
            goal_id=arguments.get("goal_id"),
            current_value=arguments.get("current_value"),
            progress_percent=arguments.get("progress_percent"),
            note=arguments.get("note", "")
        )
        
        return {
            "result": {"success": success},
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/get_goals")
async def get_goals(request: Request):
    """获取所有目标"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        status = arguments.get("status", "active")
        
        goals = goal_tracker.get_all_goals(status=status)
        
        return {
            "result": {"goals": goals, "count": len(goals)},
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/daily_checkin")
async def daily_checkin(request: Request):
    """每日打卡"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        success = goal_tracker.checkin(
            date=arguments.get("date"),
            completed=arguments.get("completed"),
            schedule_id=arguments.get("schedule_id"),
            goal_id=arguments.get("goal_id"),
            note=arguments.get("note", "")
        )
        
        return {
            "result": {"success": success},
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/generate_daily_review")
async def generate_daily_review(request: Request):
    """生成每日复盘报告"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        date = arguments.get("date")
        
        review = goal_tracker.generate_daily_review(date)
        
        return {
            "result": review,
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/get_goal_stats")
async def get_goal_stats(request: Request):
    """获取目标统计"""
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        stats = goal_tracker.get_completion_stats(
            goal_id=arguments.get("goal_id"),
            days=arguments.get("days", 7)
        )
        
        return {
            "result": stats,
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


# ============ 打卡系统 API (新增) ============

@app.post("/checkin")
async def create_checkin_endpoint(request: Request):
    """
    创建打卡记录
    
    请求体:
    {
        "type": "water",
        "title": "喝水打卡",
        "scheduled_time": "2026-03-15T15:00:00",
        "note": "备注信息"
    }
    """
    try:
        data = await request.json()
        
        from datetime import datetime as dt
        scheduled_time = data.get("scheduled_time")
        if isinstance(scheduled_time, str):
            scheduled_time = dt.fromisoformat(scheduled_time)
        else:
            scheduled_time = dt.now()
        
        checkin_id = checkin_tracker.create_checkin(
            checkin_type=data.get("type", "custom"),
            scheduled_time=scheduled_time,
            user_id=data.get("user_id", "default"),
            title=data.get("title", ""),
            note=data.get("note", "")
        )
        
        return {
            "result": {
                "checkin_id": checkin_id,
                "message": "打卡记录创建成功"
            },
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.put("/checkin/{checkin_id}")
async def update_checkin_endpoint(checkin_id: int, request: Request):
    """
    更新打卡状态
    
    请求体:
    {
        "status": "completed",
        "actual_time": "2026-03-15T15:05:00",
        "note": "已喝500ml"
    }
    """
    try:
        data = await request.json()
        
        from datetime import datetime as dt
        actual_time = data.get("actual_time")
        if isinstance(actual_time, str):
            actual_time = dt.fromisoformat(actual_time)
        
        success = checkin_tracker.update_checkin_status(
            checkin_id=checkin_id,
            status=data.get("status", "pending"),
            actual_time=actual_time,
            note=data.get("note", "")
        )
        
        if success:
            return {
                "result": {
                    "message": "打卡状态更新成功",
                    "checkin_id": checkin_id,
                    "status": data.get("status")
                },
                "status": "success"
            }
        else:
            return {
                "result": {"error": f"打卡记录 {checkin_id} 不存在"},
                "status": "error"
            }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.get("/checkin/today")
async def get_today_checkins_endpoint(
    user_id: str = "default"
):
    """获取今日打卡列表"""
    try:
        checkins = checkin_tracker.get_today_checkins(user_id)
        
        return {
            "result": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "checkins": checkins,
                "count": len(checkins)
            },
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.get("/checkin/stats")
async def get_checkin_stats_endpoint(
    days: int = 7,
    user_id: str = "default"
):
    """
    获取打卡统计
    
    参数:
    - days: 统计天数（默认7天）
    - user_id: 用户ID
    """
    try:
        stats = checkin_tracker.get_checkin_stats(
            days=days,
            user_id=user_id
        )
        
        return {
            "result": stats,
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/checkin/parse")
async def parse_checkin_response_endpoint(request: Request):
    """
    解析用户回复，自动识别打卡状态
    
    请求体:
    {
        "user_input": "喝了"
    }
    
    返回:
    {
        "status": "completed",
        "confidence": "high",
        "matched_pattern": "喝了"
    }
    """
    try:
        data = await request.json()
        user_input = data.get("user_input", "")
        
        result = checkin_tracker.parse_user_response(user_input)
        
        # 如果提供了checkin_id，自动更新状态
        checkin_id = data.get("checkin_id")
        if checkin_id and result.get("confidence") == "high":
            checkin_tracker.update_checkin_status(
                checkin_id=checkin_id,
                status=result["status"],
                actual_time=datetime.now()
            )
            result["updated"] = True
            result["checkin_id"] = checkin_id
        
        return {
            "result": result,
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


# ============ 工具函数：打卡集成 ============

@app.post("/tools/create_checkin_from_reminder")
async def create_checkin_from_reminder_endpoint(request: Request):
    """
    从提醒创建打卡记录（供提醒发送时调用）
    
    请求体:
    {
        "reminder_type": "water",
        "scheduled_time": "2026-03-15T15:00:00",
        "message": "该喝水了！"
    }
    """
    try:
        data = await request.json()
        
        from datetime import datetime as dt
        scheduled_time = data.get("scheduled_time")
        if isinstance(scheduled_time, str):
            scheduled_time = dt.fromisoformat(scheduled_time)
        else:
            scheduled_time = dt.now()
        
        checkin_id = checkin_tracker.create_checkin_from_reminder(
            reminder_type=data.get("reminder_type", "custom"),
            scheduled_time=scheduled_time,
            message=data.get("message", ""),
            user_id=data.get("user_id", "default")
        )
        
        return {
            "result": {
                "checkin_id": checkin_id,
                "message": "打卡记录已自动创建",
                "status": "pending"
            },
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/get_pending_checkins")
async def get_pending_checkins_endpoint(request: Request):
    """
    获取待处理的打卡记录
    
    用于主会话识别用户是否正在回复打卡
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        pending = checkin_tracker.get_pending_checkins(
            user_id=arguments.get("user_id", "default"),
            limit=arguments.get("limit", 5)
        )
        
        return {
            "result": {
                "pending_checkins": pending,
                "count": len(pending),
                "has_pending": len(pending) > 0
            },
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.3.0",
        "features": [
            "memory", "sentiment", "adjustment", 
            "learning", "promotion", "contextual_advice",
            "goal_tracking", "daily_checkin", "daily_review",
            "checkin_system", "auto_parse", "checkin_stats"
        ]
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "CogniMate Server is running",
        "version": "2.3.0",
        "docs": "/docs"
    }


# ============ 飞书直接发送 API (方案B - 带重试机制) ============

import asyncio
import time

@app.post("/tools/send_feishu_message")
async def send_feishu_message(request: Request):
    """
    直接发送飞书消息，绕过 OpenClaw 的 message 机制
    用于解决 API 限流导致的消息延迟问题
    带重试机制：失败后等待30秒重试，最多3次
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        user_id = arguments.get("user_id", "ou_e2516ce99ba67e7c21320bbc96270d17")
        message = arguments.get("message", "")
        max_retries = arguments.get("max_retries", 3)
        
        if not message:
            return {"result": {"error": "消息内容不能为空"}, "status": "error"}
        
        # 带重试机制的发送
        last_error = None
        for attempt in range(max_retries):
            try:
                print(f"[SendMessage] 尝试 {attempt + 1}/{max_retries} 发送消息给用户 {user_id}")
                success, result = send_message_to_user(user_id, message)
                
                if success:
                    print(f"[SendMessage] 消息发送成功: {result.get('message_id', 'unknown')}")
                    return {
                        "result": {
                            "message_id": result.get("message_id", "unknown"),
                            "chat_id": result.get("chat_id", user_id),
                            "status": "sent",
                            "attempts": attempt + 1
                        },
                        "status": "success"
                    }
                else:
                    last_error = result
                    print(f"[SendMessage] 发送失败: {result}")
                    
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
                        print(f"[SendMessage] 等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                    
            except Exception as e:
                last_error = str(e)
                print(f"[SendMessage] 发送异常: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(30)
        
        # 所有重试都失败
        return {
            "result": {
                "error": f"发送失败，已重试 {max_retries} 次",
                "last_error": last_error
            },
            "status": "error"
        }
        
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/send_message_with_fallback")
async def send_message_with_fallback(request: Request):
    """
    发送消息（带多重降级方案）
    
    降级方案：
    1. 首选：飞书直接发送 API
    2. 备用：记录到数据库，等待下次发送
    """
    try:
        data = await request.json()
        arguments = data.get("arguments", {})
        
        user_id = arguments.get("user_id", "ou_e2516ce99ba67e7c21320bbc96270d17")
        message = arguments.get("message", "")
        
        # 尝试直接发送
        success, result = send_message_to_user(user_id, message)
        
        if success:
            return {
                "result": {"status": "sent", "message_id": result.get("message_id")},
                "status": "success"
            }
        else:
            # 记录失败到数据库，稍后重试
            conn = sqlite3.connect('/root/.openclaw/workspace-cognimate/cognimate.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pending_messages (user_id, message, created_at, retry_count)
                VALUES (?, ?, datetime('now'), 0)
            ''', (user_id, message))
            conn.commit()
            conn.close()
            
            return {
                "result": {
                    "status": "queued",
                    "message": "发送失败，已加入队列稍后重试"
                },
                "status": "partial"
            }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


# ============ 启动 ============

if __name__ == "__main__":
    import uvicorn
    
    # 初始化数据库
    init_db()
    
    # 启动服务器
    print("🚀 启动 CogniMate Server v2.3.0...")
    print("📍 地址: http://localhost:8000")
    print("📖 API 文档: http://localhost:8000/docs")
    print("✨ 功能列表:")
    print("   - 记忆管理")
    print("   - 情感分析")
    print("   - 学习记录与晋升")
    print("   - 目标追踪")
    print("   - 每日复盘")
    print("   - 打卡系统 ⭐ NEW")
    print("   - 自动状态识别 ⭐ NEW")
    uvicorn.run(app, host="0.0.0.0", port=8000)
