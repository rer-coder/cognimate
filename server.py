from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
import json
import os
from datetime import datetime

app = FastAPI(title="CogniMate Backend", version="1.0.0")

# 启用CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "cognimate.db")
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "memory")

# 确保memory目录存在
os.makedirs(MEMORY_DIR, exist_ok=True)

# 数据库初始化
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT,
        timezone TEXT DEFAULT 'Asia/Shanghai',
        language TEXT DEFAULT 'zh-CN',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建日程表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        event TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        location TEXT,
        repeat_rule TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建目标表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        title TEXT NOT NULL,
        description TEXT,
        target_date TEXT,
        progress REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建每日任务表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        goal_id INTEGER,
        task TEXT NOT NULL,
        date TEXT,
        completed BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (goal_id) REFERENCES goals (id)
    )''')
    
    # 创建偏好表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        key TEXT NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 插入默认用户（如果不存在）
    cursor.execute("SELECT id FROM users WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (id, name, timezone, language) VALUES (1, '用户', 'Asia/Shanghai', 'zh-CN')"
        )
    
    # ===== 打卡系统表 (新增) =====
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
    )''')
    
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
    )''')
    
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
    )''')
    
    conn.commit()
    conn.close()

init_db()

# Pydantic模型
class QueryRequest(BaseModel):
    query: str

class UpdateMemoryRequest(BaseModel):
    operation: str  # create, update, delete
    data: Dict[str, Any]

class SentimentRequest(BaseModel):
    user_input: str

class AdjustmentRequest(BaseModel):
    current_plan: Dict[str, Any]
    user_status: Dict[str, Any]

class OutingRequest(BaseModel):
    event: Dict[str, Any]

class ChatRequest(BaseModel):
    message: Dict[str, Any]

class GoalSettingRequest(BaseModel):
    user_input: str
    current_profile: Optional[Dict[str, Any]] = None

class PersonalizedPlanRequest(BaseModel):
    user_profile: Dict[str, Any]
    goal_type: str

# 打卡系统模型 (新增)
class CreateCheckinRequest(BaseModel):
    type: str
    title: str = ""
    scheduled_time: str
    note: str = ""
    user_id: str = "default"

class UpdateCheckinRequest(BaseModel):
    status: str  # pending, completed, missed, skipped
    actual_time: Optional[str] = None
    note: str = ""

class ParseCheckinRequest(BaseModel):
    user_input: str
    checkin_id: Optional[int] = None

class CreateCheckinFromReminderRequest(BaseModel):
    reminder_type: str
    scheduled_time: str
    message: str
    user_id: str = "default"

class GetPendingCheckinsRequest(BaseModel):
    user_id: str = "default"
    limit: int = 10

# 工具函数实现
@app.post("/tools/query_memory")
async def query_memory(request: QueryRequest):
    """查询记忆库（日程、目标、档案）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = request.query
    result = {}
    
    # 查询日程
    if any(keyword in query for keyword in ["日程", "安排", "计划", "今天", "明天", "下午", "上午"]):
        cursor.execute("SELECT * FROM schedules ORDER BY start_time")
        schedules = cursor.fetchall()
        result["schedules"] = [
            {
                "id": s[0],
                "event": s[2],
                "start_time": s[3],
                "end_time": s[4],
                "location": s[5]
            }
            for s in schedules
        ]
    
    # 查询目标
    if any(keyword in query for keyword in ["目标", "goal", "减重", "计划"]):
        cursor.execute("SELECT * FROM goals")
        goals = cursor.fetchall()
        result["goals"] = [
            {
                "id": g[0],
                "title": g[2],
                "description": g[3],
                "target_date": g[4],
                "progress": g[5]
            }
            for g in goals
        ]
    
    # 查询用户档案
    if any(keyword in query for keyword in ["档案", "信息", "偏好", "用户"]):
        cursor.execute("SELECT * FROM users WHERE id = 1")
        user = cursor.fetchone()
        if user:
            result["user"] = {
                "id": user[0],
                "name": user[1],
                "timezone": user[3],
                "language": user[4]
            }
    
    if not result:
        result = {"message": "未找到相关信息"}
    
    conn.close()
    return {"result": result, "status": "success"}

@app.post("/tools/update_memory")
async def update_memory(request: UpdateMemoryRequest):
    """创建、更新或删除记忆库中的条目"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    operation = request.operation
    data = request.data
    
    try:
        if operation == "create":
            # 创建日程
            if "event" in data:
                cursor.execute(
                    """INSERT INTO schedules (user_id, event, start_time, end_time, location) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (1, data["event"], data.get("start_time"), data.get("end_time"), data.get("location"))
                )
            
            # 创建目标
            elif "title" in data and ("description" in data or "target_date" in data):
                cursor.execute(
                    """INSERT INTO goals (user_id, title, description, target_date, progress) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (1, data["title"], data.get("description"), data.get("target_date"), data.get("progress", 0))
                )
            
            # 创建任务
            elif "task" in data:
                cursor.execute(
                    """INSERT INTO daily_tasks (user_id, goal_id, task, date, completed) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (1, data.get("goal_id"), data["task"], data.get("date"), data.get("completed", False))
                )
        
        elif operation == "update":
            # 更新目标进度
            if "goal_id" in data and "progress" in data:
                cursor.execute(
                    "UPDATE goals SET progress = ? WHERE id = ?",
                    (data["progress"], data["goal_id"])
                )
            
            # 更新任务状态
            elif "task_id" in data and "completed" in data:
                cursor.execute(
                    "UPDATE daily_tasks SET completed = ? WHERE id = ?",
                    (data["completed"], data["task_id"])
                )
            
            # 更新日程
            elif "schedule_id" in data:
                updates = []
                params = []
                if "event" in data:
                    updates.append("event = ?")
                    params.append(data["event"])
                if "start_time" in data:
                    updates.append("start_time = ?")
                    params.append(data["start_time"])
                if "end_time" in data:
                    updates.append("end_time = ?")
                    params.append(data["end_time"])
                if "location" in data:
                    updates.append("location = ?")
                    params.append(data["location"])
                
                if updates:
                    params.append(data["schedule_id"])
                    cursor.execute(
                        f"UPDATE schedules SET {', '.join(updates)} WHERE id = ?",
                        params
                    )
        
        elif operation == "delete":
            # 删除日程
            if "schedule_id" in data:
                cursor.execute("DELETE FROM schedules WHERE id = ?", (data["schedule_id"],))
            
            # 删除目标
            elif "goal_id" in data:
                cursor.execute("DELETE FROM goals WHERE id = ?", (data["goal_id"],))
            
            # 删除任务
            elif "task_id" in data:
                cursor.execute("DELETE FROM daily_tasks WHERE id = ?", (data["task_id"],))
        
        conn.commit()
        conn.close()
        return {"result": {"message": "操作成功"}, "status": "success"}
    
    except Exception as e:
        conn.close()
        return {"result": {"message": f"操作失败: {str(e)}"}, "status": "error"}

@app.post("/tools/analyze_sentiment_and_state")
async def analyze_sentiment_and_state(request: SentimentRequest):
    """分析用户输入的情感和隐含状态 - 增强版：支持否定词和程度词"""
    user_input = request.user_input
    
    sentiment = "neutral"
    energy_level = "medium"
    keywords = []
    intensity_score = 0.5  # 默认中等强度 0.0-1.0
    
    # 情感词库
    negative_words = ["累", "疲惫", "不想", "难过", "痛苦", "挫折", "难受", "不舒服", 
                      "焦虑", "压力大", "烦", "郁闷", "失望", "沮丧", "担心", "害怕"]
    positive_words = ["开心", "高兴", "完成", "成功", "棒", "好", "不错", "赞", 
                      "轻松", "愉快", "满意", "喜欢", "兴奋", "惊喜", "舒服"]
    
    # 否定词 - 用于反转情感
    negation_words = ["不", "没", "别", "无", "非", "未", "不要", "不是", "不会", "没有"]
    
    # 程度词 - 用于调整强度
    intensity_words = {
        "有点": 0.4,      # 轻度
        "稍微": 0.4,
        "比较": 0.6,      # 中度
        "挺": 0.6,
        "很": 0.8,        # 较强
        "非常": 0.9,      # 强
        "太": 0.9,
        "特别": 0.9,
        "十分": 0.9,
        "极其": 1.0,      # 极强
        "超级": 1.0,
        "真的": 0.8,
        "确实": 0.7
    }
    
    # 检查程度词
    for word, score in intensity_words.items():
        if word in user_input:
            intensity_score = score
            keywords.append(f"[程度]{word}")
            break
    
    # 检查情感词（考虑否定词）
    negation_detected = False
    negation_position = -1
    
    # 先检测否定词位置
    for neg_word in negation_words:
        pos = user_input.find(neg_word)
        if pos != -1 and (negation_position == -1 or pos < negation_position):
            negation_position = pos
            negation_detected = True
    
    # 检测消极词
    for word in negative_words:
        if word in user_input:
            word_pos = user_input.find(word)
            # 检查是否在否定词范围内（否定词在前3个字内）
            is_negated = negation_detected and negation_position < word_pos and (word_pos - negation_position) <= 3
            
            if is_negated:
                # 否定消极 = 积极
                sentiment = "positive"
                # 根据程度词调整能量
                if intensity_score >= 0.8:
                    energy_level = "high"
                else:
                    energy_level = "medium"
                keywords.append(f"[否定消极]{word}")
            else:
                # 纯消极
                sentiment = "negative"
                energy_level = "low" if intensity_score >= 0.6 else "medium"
                keywords.append(f"[消极]{word}")
    
    # 检测积极词（如果没匹配到消极词或消极词被否定）
    if sentiment == "neutral":
        for word in positive_words:
            if word in user_input:
                word_pos = user_input.find(word)
                # 检查是否被否定
                is_negated = negation_detected and negation_position < word_pos and (word_pos - negation_position) <= 3
                
                if is_negated:
                    # 否定积极 = 消极
                    sentiment = "negative"
                    energy_level = "low"
                    keywords.append(f"[否定积极]{word}")
                else:
                    # 纯积极
                    sentiment = "positive"
                    energy_level = "high" if intensity_score >= 0.6 else "medium"
                    keywords.append(f"[积极]{word}")
    
    # 如果没有匹配到关键词，根据标点符号和长度做简单判断
    if not keywords or sentiment == "neutral":
        if "!" in user_input or "！" in user_input:
            energy_level = "high"
        elif "。" in user_input and len(user_input) > 20:
            energy_level = "medium"
    
    return {
        "result": {
            "sentiment": sentiment,
            "energy_level": energy_level,
            "keywords": keywords,
            "intensity_score": round(intensity_score, 2),
            "negation_detected": negation_detected
        },
        "status": "success"
    }

@app.post("/tools/generate_dynamic_adjustment")
async def generate_dynamic_adjustment(request: AdjustmentRequest):
    """根据用户当前状态生成动态调整方案"""
    current_plan = request.current_plan
    user_status = request.user_status
    
    adjusted_tasks = []
    reason = ""
    impact_on_goal = ""
    
    energy_level = user_status.get("energy_level", "medium")
    
    if energy_level == "low":
        # 降低强度
        event = current_plan.get("event", "")
        if "跑步" in event or "运动" in event or "健身" in event:
            adjusted_tasks.append({
                "time": current_plan.get("start_time"),
                "new_task": "散步30-40分钟"
            })
            reason = "用户反馈身体不适或能量较低，建议降低运动强度，避免过度疲劳"
            impact_on_goal = "今日运动量减少约30%，但持续性更重要。可在明日状态好时适当增加运动量补偿"
        
        elif "会议" in event or "工作" in event:
            adjusted_tasks.append({
                "time": current_plan.get("start_time"),
                "new_task": "简短会议或推迟到明天"
            })
            reason = "用户当前状态不佳，建议减少高强度工作"
            impact_on_goal = "今日工作进度可能略有延迟，但充分休息能保证后续效率"
    
    elif energy_level == "high":
        # 可以考虑增加挑战性
        reason = "用户状态良好，可以按计划执行或适当增加挑战性任务"
        impact_on_goal = "当前状态有利于目标推进，建议把握机会"
    
    return {
        "result": {
            "adjusted_tasks": adjusted_tasks,
            "reason": reason,
            "impact_on_goal": impact_on_goal
        },
        "status": "success"
    }

@app.post("/tools/check_context_for_outing")
async def check_context_for_outing(request: OutingRequest):
    """为外出日程查询情境信息（天气、交通）"""
    event = request.event
    location = event.get("location", "")
    start_time = event.get("start_time", "")
    
    # 这里可以集成天气API，现在返回模拟数据
    return {
        "result": {
            "weather": "晴天，温度适宜",
            "suggestions": "建议穿轻便衣物，提前15分钟出发避开高峰",
            "location": location,
            "start_time": start_time
        },
        "status": "success"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """处理飞书消息 - 由OpenClaw处理，这里仅做转发/记录"""
    message = request.message
    
    # 记录到每日记忆文件
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = os.path.join(MEMORY_DIR, f"{today}.md")
    
    with open(memory_file, "a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().strftime('%H:%M:%S')}\n")
        f.write(f"**用户**: {message.get('text', '')}\n")
    
    return {
        "result": {
            "message": "消息已接收，请通过OpenClaw处理",
            "timestamp": datetime.now().isoformat()
        },
        "status": "success"
    }

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CogniMate Backend"}

# 获取所有日程
@app.get("/schedules")
async def get_schedules():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules ORDER BY start_time")
    schedules = cursor.fetchall()
    conn.close()
    
    return {
        "schedules": [
            {
                "id": s[0],
                "event": s[2],
                "start_time": s[3],
                "end_time": s[4],
                "location": s[5]
            }
            for s in schedules
        ]
    }

# 获取所有目标
@app.get("/goals")
async def get_goals():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals")
    goals = cursor.fetchall()
    conn.close()
    
    return {
        "goals": [
            {
                "id": g[0],
                "title": g[2],
                "description": g[3],
                "target_date": g[4],
                "progress": g[5]
            }
            for g in goals
        ]
    }

# 目标设定访谈 - 分析用户输入，判断是否需要提问，返回问题列表
@app.post("/tools/goal_setting_interview")
async def goal_setting_interview(request: GoalSettingRequest):
    """目标设定访谈：分析用户目标意向，返回需要收集的信息和问题"""
    user_input = request.user_input
    current_profile = request.current_profile or {}
    
    # 检测目标类型
    goal_type = None
    if any(word in user_input for word in ["减重", "减肥", "瘦", "体重", "健身", "运动"]):
        goal_type = "weight_loss"
    elif any(word in user_input for word in ["学习", "读书", "备考", "考试", "技能"]):
        goal_type = "learning"
    elif any(word in user_input for word in ["早起", "早睡", "喝水", "习惯"]):
        goal_type = "habit"
    else:
        goal_type = "general"
    
    # 根据目标类型和已有信息，确定需要提问的内容
    questions = []
    missing_info = []
    
    if goal_type == "weight_loss":
        # 减重目标需要的信息
        required_fields = ["height", "current_weight", "target_weight", "timeframe", "focus_areas", "exercise_time", "fitness_level"]
        
        for field in required_fields:
            if field not in current_profile:
                missing_info.append(field)
        
        # 根据缺失信息生成问题
        question_map = {
            "height": "你的身高是多少？",
            "current_weight": "你目前的体重是多少？",
            "target_weight": "目标体重是多少？（建议设定合理的目标，比如每月减2-4斤）",
            "timeframe": "希望在多长时间内达成？（1个月/3个月/半年）",
            "focus_areas": "最想改善哪个部位？（肚子/腿/臀部/手臂/全身）",
            "exercise_time": "每天能抽出多少时间运动？",
            "fitness_level": "平时有运动习惯吗？（新手/偶尔运动/经常运动）"
        }
        
        for field in missing_info:
            if field in question_map:
                questions.append({
                    "field": field,
                    "question": question_map[field]
                })
    
    elif goal_type == "learning":
        questions = [
            {"field": "subject", "question": "你想学习什么内容？"},
            {"field": "current_level", "question": "目前的基础如何？（零基础/有基础/进阶）"},
            {"field": "study_time", "question": "每天能投入多少时间学习？"},
            {"field": "deadline", "question": "有考试或完成的截止日期吗？"}
        ]
    
    elif goal_type == "habit":
        questions = [
            {"field": "habit_name", "question": "具体想养成什么习惯？"},
            {"field": "trigger", "question": "打算在什么时间/场景执行？"},
            {"field": "difficulty", "question": "觉得这个习惯容易坚持吗？（容易/中等/困难）"}
        ]
    
    # 判断是否有足够信息生成方案
    has_enough_info = len(missing_info) <= 2  # 如果只剩2个以下信息缺失，认为足够
    
    return {
        "result": {
            "goal_type": goal_type,
            "detected_intent": True,
            "questions": questions,
            "missing_fields": missing_info,
            "current_profile": current_profile,
            "has_enough_info": has_enough_info,
            "message": f"检测到你想设定{goal_type}目标，请回答以下问题，我来为你定制方案" if questions else "信息已收集完整，可以生成个性化方案了！"
        },
        "status": "success"
    }

# 生成个性化方案
@app.post("/tools/create_personalized_plan")
async def create_personalized_plan(request: PersonalizedPlanRequest):
    """根据用户资料生成完全个性化的方案"""
    profile = request.user_profile
    goal_type = request.goal_type
    
    plan = {
        "goal_summary": "",
        "plan_documents": [],
        "schedule_items": [],
        "recommendations": []
    }
    
    if goal_type == "weight_loss":
        height = profile.get("height", 170)
        current_weight = profile.get("current_weight", 70)
        target_weight = profile.get("target_weight", 65)
        timeframe = profile.get("timeframe", "3个月")
        focus_areas = profile.get("focus_areas", ["全身"])
        exercise_time = profile.get("exercise_time", "30分钟")
        fitness_level = profile.get("fitness_level", "新手")
        
        weight_diff = current_weight - target_weight
        
        plan["goal_summary"] = f"{timeframe}内从{current_weight}斤减至{target_weight}斤（共{weight_diff}斤），重点改善{', '.join(focus_areas)}"
        
        plan["plan_documents"] = [
            f"fitness_plan_{profile.get('name', 'user')}.md - 个性化运动计划",
            f"diet_plan_{profile.get('name', 'user')}.md - 个性化饮食建议",
            f"goals/weight_loss_{profile.get('name', 'user')}.md - 目标追踪文档"
        ]
        
        # 生成每日日程
        plan["schedule_items"] = [
            {
                "event": f"{exercise_time}减重运动（重点：{', '.join(focus_areas)}）",
                "time": "19:00",
                "location": "家里/健身房",
                "repeat": "daily"
            },
            {
                "event": "记录体重和饮食",
                "time": "21:00",
                "location": "手机/笔记本",
                "repeat": "daily"
            }
        ]
        
        plan["recommendations"] = [
            f"根据你的{fitness_level}水平，建议从低强度开始，逐步增加",
            f"重点关注{', '.join(focus_areas)}的训练",
            "每周安排1-2天休息日，让身体恢复",
            "配合饮食控制，效果更佳"
        ]
    
    return {
        "result": plan,
        "status": "success"
    }


# ============ 打卡系统 API (新增) ============

import re
from datetime import datetime, timedelta

def parse_user_response(user_input: str) -> Dict[str, Any]:
    """解析用户回复，识别打卡状态"""
    user_input = user_input.lower().strip()
    
    # 状态识别模式
    status_patterns = {
        "completed": [
            r'喝[了过]?', r'完成[了]?', r'做[了过]?', r'✅', r'✓', r'☑️', 
            r'[做搞]完[了]?', r'ok', r'好的', r'收到', r'明白', r'好[的呀]?',
            r'已[经]?[喝吃做]', r'弄好[了]?', r'搞定', r'yes', r'嗯', r'对',
            r'[做搞]了', r'正常', r'按时', r'准时', r'刚刚完成'
        ],
        "missed": [
            r'没[喝吃做]', r'忘[了记]', r'❌', r'✗', r'错过[了]?',
            r'来?不及[了]?', r'没[有能]?[喝吃做]?', r'没顾上', r'no',
            r'没有', r'忘了', r'忘记', r'忙', r'没空', r'没[有]?时间',
            r'没做到', r'未完成', r'失败'
        ],
        "skipped": [
            r'跳过', r'不需要', r'取消', r'不用', r'作罢', r'算了',
            r'改天', r'下次', r'不必', r'免了', r'不[用]?[做搞]',
            r'略过', r'pass', r'不[需要]'
        ]
    }
    
    for status, patterns in status_patterns.items():
        for pattern in patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return {
                    "status": status,
                    "confidence": "high",
                    "matched_pattern": pattern,
                    "original_text": user_input
                }
    
    return {
        "status": "pending",
        "confidence": "low",
        "matched_pattern": None,
        "original_text": user_input,
        "message": "无法自动识别状态，请明确回复'完成'、'没做'或'跳过'"
    }


def calculate_streak(user_id: str = "default") -> int:
    """计算当前连续打卡天数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    streak = 0
    today = datetime.now().date()
    
    for i in range(365):
        check_date = today - timedelta(days=i+1)
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM checkins 
            WHERE user_id = ? AND date(scheduled_time) = date(?)
        ''', (user_id, check_date.strftime('%Y-%m-%d')))
        
        row = cursor.fetchone()
        total = row[0] or 0
        completed = row[1] or 0
        
        if total == 0:
            continue
        
        if completed > 0 and completed >= total * 0.5:
            streak += 1
        else:
            break
    
    conn.close()
    return streak


def calculate_longest_streak(user_id: str = "default") -> int:
    """计算历史最长连续打卡天数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT date(scheduled_time) as check_date
        FROM checkins 
        WHERE user_id = ?
        ORDER BY check_date
    ''', (user_id,))
    
    dates = [row[0] for row in cursor.fetchall()]
    
    if not dates:
        conn.close()
        return 0
    
    valid_dates = []
    for date_str in dates:
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM checkins 
            WHERE user_id = ? AND date(scheduled_time) = date(?)
        ''', (user_id, date_str))
        
        row = cursor.fetchone()
        total = row[0] or 0
        completed = row[1] or 0
        
        if completed >= total * 0.5:
            valid_dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
    
    conn.close()
    
    if not valid_dates:
        return 0
    
    longest = 1
    current = 1
    
    for i in range(1, len(valid_dates)):
        if (valid_dates[i] - valid_dates[i-1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    
    return longest


@app.post("/checkin")
async def create_checkin(request: CreateCheckinRequest):
    """创建打卡记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 解析时间
        scheduled_time = datetime.fromisoformat(request.scheduled_time.replace('Z', '+00:00'))
        
        # 生成默认标题
        titles = {
            "water": "喝水打卡",
            "exercise": "运动打卡",
            "work": "工作打卡",
            "study": "学习打卡",
            "sleep": "睡眠打卡",
            "medicine": "吃药打卡",
            "custom": "自定义打卡"
        }
        title = request.title or titles.get(request.type, "打卡")
        
        cursor.execute('''
            INSERT INTO checkins (user_id, type, title, scheduled_time, status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (request.user_id, request.type, title, scheduled_time.isoformat(), 
              "pending", request.note))
        
        checkin_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "result": {"checkin_id": checkin_id, "message": "打卡记录创建成功"},
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.put("/checkin/{checkin_id}")
async def update_checkin(checkin_id: int, request: UpdateCheckinRequest):
    """更新打卡状态"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查记录是否存在
        cursor.execute('SELECT id FROM checkins WHERE id = ?', (checkin_id,))
        if not cursor.fetchone():
            conn.close()
            return {"result": {"error": f"打卡记录 {checkin_id} 不存在"}, "status": "error"}
        
        # 构建更新
        updates = ['status = ?']
        params = [request.status]
        
        if request.actual_time:
            actual_time = datetime.fromisoformat(request.actual_time.replace('Z', '+00:00'))
            updates.append('actual_time = ?')
            params.append(actual_time.isoformat())
        
        if request.note:
            updates.append('note = ?')
            params.append(request.note)
        
        params.append(checkin_id)
        
        cursor.execute(f'''
            UPDATE checkins SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', params)
        
        conn.commit()
        conn.close()
        
        return {
            "result": {"message": "打卡状态更新成功", "checkin_id": checkin_id, "status": request.status},
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.get("/checkin/today")
async def get_today_checkins(user_id: str = "default"):
    """获取今日打卡列表"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT * FROM checkins 
            WHERE user_id = ? AND scheduled_time >= ? AND scheduled_time < ?
            ORDER BY scheduled_time
        ''', (user_id, today, tomorrow))
        
        rows = cursor.fetchall()
        conn.close()
        
        checkins = [
            {
                "id": r[0],
                "user_id": r[1],
                "type": r[2],
                "title": r[3],
                "scheduled_time": r[4],
                "actual_time": r[5],
                "status": r[6],
                "note": r[7],
                "created_at": r[9],
                "updated_at": r[10]
            }
            for r in rows
        ]
        
        return {
            "result": {"date": today, "checkins": checkins, "count": len(checkins)},
            "status": "success"
        }
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.get("/checkin/stats")
async def get_checkin_stats(days: int = 7, user_id: str = "default"):
    """获取打卡统计"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        
        # 总体统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM checkins 
            WHERE user_id = ? AND date(scheduled_time) >= date(?) AND date(scheduled_time) <= date(?)
        ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        row = cursor.fetchone()
        total = row[0] or 0
        completed = row[1] or 0
        missed = row[2] or 0
        skipped = row[3] or 0
        pending_count = row[4] or 0
        
        # 按类型统计
        cursor.execute('''
            SELECT 
                type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM checkins 
            WHERE user_id = ? AND date(scheduled_time) >= date(?) AND date(scheduled_time) <= date(?)
            GROUP BY type
        ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        by_type = {
            row[0]: {
                'total': row[1],
                'completed': row[2] or 0,
                'rate': round((row[2] or 0) / max(row[1], 1) * 100, 2)
            }
            for row in cursor.fetchall()
        }
        
        conn.close()
        
        stats = {
            "period_days": days,
            "total": total,
            "completed": completed,
            "missed": missed,
            "skipped": skipped,
            "pending": pending_count,
            "completion_rate": round(completed / max(total, 1) * 100, 2),
            "by_type": by_type,
            "current_streak": calculate_streak(user_id),
            "longest_streak": calculate_longest_streak(user_id)
        }
        
        return {"result": stats, "status": "success"}
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/checkin/parse")
async def parse_checkin_response(request: ParseCheckinRequest):
    """解析用户回复，自动识别打卡状态"""
    try:
        result = parse_user_response(request.user_input)
        
        # 如果提供了checkin_id且置信度高，自动更新
        if request.checkin_id and result.get("confidence") == "high":
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE checkins 
                SET status = ?, actual_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (result["status"], datetime.now().isoformat(), request.checkin_id))
            
            conn.commit()
            conn.close()
            
            result["updated"] = True
            result["checkin_id"] = request.checkin_id
        
        return {"result": result, "status": "success"}
    except Exception as e:
        return {"result": {"error": str(e)}, "status": "error"}


@app.post("/tools/create_checkin_from_reminder")
async def create_checkin_from_reminder(request: CreateCheckinFromReminderRequest):
    """从提醒创建打卡记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        scheduled_time = datetime.fromisoformat(request.scheduled_time.replace('Z', '+00:00'))
        
        # 提取标题
        titles = {
            "water": "喝水打卡",
            "exercise": "运动打卡",
            "work": "工作打卡",
            "study": "学习打卡",
            "sleep": "睡眠打卡",
            "medicine": "吃药打卡",
            "custom": "自定义打卡"
        }
        title = titles.get(request.reminder_type, "打卡")
        
        cursor.execute('''
            INSERT INTO checkins (user_id, type, title, scheduled_time, status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (request.user_id, request.reminder_type, title, scheduled_time.isoformat(), 
              "pending", f"来源: {request.message[:50]}..."))
        
        checkin_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
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
async def get_pending_checkins(request: GetPendingCheckinsRequest):
    """获取待处理的打卡记录（用于识别用户是否在回复打卡）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM checkins 
            WHERE user_id = ? AND status = 'pending'
            AND scheduled_time <= datetime('now', '+1 hour')
            ORDER BY scheduled_time DESC
            LIMIT ?
        ''', (request.user_id, request.limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        pending = [
            {
                "id": r[0],
                "user_id": r[1],
                "type": r[2],
                "title": r[3],
                "scheduled_time": r[4],
                "status": r[6],
                "note": r[7]
            }
            for r in rows
        ]
        
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

if __name__ == "__main__":
    import uvicorn
    print("🧠 CogniMate Backend 启动中...")
    print(f"📁 数据库: {DB_PATH}")
    print(f"📁 记忆目录: {MEMORY_DIR}")
    print("✅ 打卡系统已加载")
    uvicorn.run(app, host="0.0.0.0", port=8000)
