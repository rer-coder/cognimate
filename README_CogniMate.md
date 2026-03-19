# CogniMate 智能伴秘系统

## 系统概述

CogniMate是一个运行于用户本地设备、以飞书为交互入口的个人AI协作者。系统的核心智能由一个本地的OpenClaw实例驱动，通过精心设计的提示词、函数调用和外部工具集成，实现日程管理、目标动态规划、状态适应、情感支持及情境感知等复杂功能。

## 架构设计

### 核心架构
采用"一体化大脑"架构，单个OpenClaw实例扮演"中央调度与协调员"，通过调用一系列本地函数来模拟不同专业Agent的工作。

```
用户输入 (飞书文本) 
       → 
[本地服务器 API] 
       → 
[OpenClaw 实例 (大脑)] 
       → 
[函数调用/工具使用] 
       → 
[组织回复] 
       → 
[返回给用户]
```

### 核心文件
- **SOUL.md**：定义CogniMate的角色、价值观和核心能力
- **TOOLS.md**：定义可用工具和调用格式
- **AGENTS.md**：定义工作流程和行为模式
- **USER.md**：用户档案模板
- **memory/**：存储日常交互记录

## 部署步骤

### 1. OpenClaw配置

#### 安装OpenClaw
```bash
# 安装OpenClaw
npm install -g openclaw@latest

# 运行引导向导
openclaw onboard --install-daemon
```

#### 配置OpenClaw
1. 确保OpenClaw API的本地端点可访问（如 http://localhost:8080/v1/chat/completions）
2. 确认其支持函数调用功能
3. 将本目录中的SOUL.md、TOOLS.md、AGENTS.md复制到OpenClaw工作目录

### 2. 本地服务器实现

#### 安装依赖
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
env\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn sqlite3 python-dotenv
```

#### 实现服务器代码
创建 `server.py` 文件：

```python
from fastapi import FastAPI, HTTPException
import sqlite3
import json
import os

app = FastAPI()

# 数据库初始化
def init_db():
    conn = sqlite3.connect('cognimate.db')
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        contact TEXT,
        timezone TEXT,
        language TEXT
    )''')
    
    # 创建日程表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        event TEXT,
        start_time TEXT,
        end_time TEXT,
        location TEXT,
        repeat_rule TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建目标表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        title TEXT,
        description TEXT,
        target_date TEXT,
        progress REAL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # 创建每日任务表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_tasks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        goal_id INTEGER,
        task TEXT,
        date TEXT,
        completed BOOLEAN,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (goal_id) REFERENCES goals (id)
    )''')
    
    # 创建偏好表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS preferences (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        key TEXT,
        value TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

# 工具函数实现
@app.post("/tools/query_memory")
async def query_memory(query: str):
    # 实现查询逻辑
    conn = sqlite3.connect('cognimate.db')
    cursor = conn.cursor()
    
    # 示例：查询日程
    if "日程" in query:
        cursor.execute("SELECT * FROM schedules")
        schedules = cursor.fetchall()
        result = [{
            "id": s[0],
            "event": s[2],
            "start_time": s[3],
            "end_time": s[4],
            "location": s[5]
        } for s in schedules]
    
    # 示例：查询目标
    elif "目标" in query:
        cursor.execute("SELECT * FROM goals")
        goals = cursor.fetchall()
        result = [{
            "id": g[0],
            "title": g[2],
            "description": g[3],
            "target_date": g[4],
            "progress": g[5]
        } for g in goals]
    else:
        result = {"message": "未找到相关信息"}
    
    conn.close()
    return {"result": result, "status": "success"}

@app.post("/tools/update_memory")
async def update_memory(operation: str, data: dict):
    # 实现更新逻辑
    conn = sqlite3.connect('cognimate.db')
    cursor = conn.cursor()
    
    if operation == "create":
        # 示例：创建日程
        if "event" in data:
            cursor.execute(
                "INSERT INTO schedules (user_id, event, start_time, end_time, location) VALUES (?, ?, ?, ?, ?)",
                (1, data["event"], data.get("start_time"), data.get("end_time"), data.get("location"))
            )
    
    elif operation == "update":
        # 示例：更新目标进度
        if "goal_id" in data and "progress" in data:
            cursor.execute(
                "UPDATE goals SET progress = ? WHERE id = ?",
                (data["progress"], data["goal_id"])
            )
    
    elif operation == "delete":
        # 示例：删除日程
        if "schedule_id" in data:
            cursor.execute(
                "DELETE FROM schedules WHERE id = ?",
                (data["schedule_id"],)
            )
    
    conn.commit()
    conn.close()
    return {"result": {"message": "操作成功"}, "status": "success"}

@app.post("/tools/analyze_sentiment_and_state")
async def analyze_sentiment_and_state(user_input: str):
    # 实现情感分析逻辑
    sentiment = "neutral"
    energy_level = "medium"
    keywords = []
    
    # 简单的情感分析
    negative_words = ["累", "疲惫", "不想", "难过", "痛苦", "挫折"]
    positive_words = ["开心", "高兴", "完成", "成功", "棒", "好"]
    
    for word in negative_words:
        if word in user_input:
            sentiment = "negative"
            energy_level = "low"
            keywords.append(word)
            break
    
    for word in positive_words:
        if word in user_input:
            sentiment = "positive"
            energy_level = "high"
            keywords.append(word)
            break
    
    return {
        "result": {
            "sentiment": sentiment,
            "energy_level": energy_level,
            "keywords": keywords
        },
        "status": "success"
    }

@app.post("/tools/generate_dynamic_adjustment")
async def generate_dynamic_adjustment(current_plan: dict, user_status: dict):
    # 实现动态调整逻辑
    adjusted_tasks = []
    reason = ""
    impact_on_goal = ""
    
    if user_status.get("energy_level") == "low":
        # 降低强度
        if "跑步" in current_plan.get("event", ""):
            adjusted_tasks.append({
                "time": current_plan.get("start_time"),
                "new_task": "散步40分钟"
            })
            reason = "用户反馈身体不适，建议降低强度防止受伤"
            impact_on_goal = "总体卡路里消耗预计减少5%，可通过明日增加10分钟运动弥补"
    
    return {
        "result": {
            "adjusted_tasks": adjusted_tasks,
            "reason": reason,
            "impact_on_goal": impact_on_goal
        },
        "status": "success"
    }

@app.post("/tools/check_context_for_outing")
async def check_context_for_outing(event: dict):
    # 实现情境检查逻辑
    # 这里可以集成天气API
    return {
        "result": {
            "weather": "晴天",
            "suggestions": "建议穿轻便衣物，带防晒用品"
        },
        "status": "success"
    }

@app.post("/chat")
async def chat(message: dict):
    # 处理飞书消息
    # 这里需要实现与OpenClaw API的通信
    return {"response": "CogniMate正在处理您的消息..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. 飞书机器人配置

1. **创建飞书机器人**：
   - 登录飞书开发者平台
   - 创建企业内部应用
   - 开启机器人能力

2. **配置回调地址**：
   - 将回调地址设置为本地服务器的公网URL（可使用ngrok或frp进行内网穿透）
   - 示例：`https://your-public-url.com/chat`

3. **配置权限**：
   - 开启消息接收权限
   - 开启消息发送权限

## 运行系统

### 1. 启动OpenClaw
```bash
# 启动OpenClaw Gateway
openclaw gateway --port 18789 --verbose
```

### 2. 启动本地服务器
```bash
# 激活虚拟环境
# Windows
env\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 启动服务器
python server.py
```

### 3. 启动飞书机器人
- 在飞书开发者平台启用机器人
- 添加机器人到聊天群或个人聊天

## 使用示例

### 示例1：查询日程
**用户**："我今天有什么安排？"
**CogniMate**："你今天有以下安排：
- 9:00-10:00 团队晨会
- 14:00-15:30 客户会议
- 18:00-19:30 健身
需要我为你准备什么吗？"

### 示例2：调整计划
**用户**："我今天感觉很累，不想跑步了"
**CogniMate**："听到你不舒服我很担心。根据你的状态，我建议将今天的跑步调整为散步40分钟，运动量我会帮你平摊到后面两天，这样不影响月度目标。照顾好自己的身体更重要，你觉得呢？"

### 示例3：设定目标
**用户**："我想设定一个减重目标"
**CogniMate**："好的，我来帮你设定减重目标。请问你当前的体重是多少？目标体重是多少？希望在多长时间内达成这个目标？"

## 系统维护

### 1. 记忆管理
- 定期备份 `cognimate.db` 数据库
- 定期整理 `memory/` 目录下的文件
- 每月更新 `MEMORY.md` 文件

### 2. 性能优化
- 确保工具函数响应时间 < 500ms
- 对频繁查询的数据进行缓存
- 定期清理无用数据

### 3. 安全管理
- 确保本地服务器的安全性
- 定期更新OpenClaw和依赖库
- 监控系统运行状态

## 扩展功能

### 1. 语音交互
- 集成语音识别和合成功能
- 支持语音指令和语音回复

### 2. 多平台支持
- 扩展到其他聊天平台（如微信、Telegram等）
- 支持多设备同步

### 3. 智能推荐
- 基于用户历史行为推荐活动
- 基于天气和日程推荐出行方案

## 故障排查

### 常见问题
1. **OpenClaw连接失败**：检查OpenClaw API端点是否正确
2. **工具调用超时**：检查工具函数响应时间
3. **飞书消息无响应**：检查回调地址配置和网络连接
4. **数据库操作失败**：检查数据库连接和权限

### 日志查看
- OpenClaw日志：`~/.openclaw/logs/`
- 本地服务器日志：控制台输出
- 飞书机器人日志：飞书开发者平台

## 总结

CogniMate智能伴秘系统通过OpenClaw的强大能力，为用户提供个性化的日程管理、目标规划和情感支持服务。系统采用本地部署方式，确保数据隐私和安全性，同时通过精心设计的工具和工作流程，实现高效、智能的用户体验。

通过持续的优化和扩展，CogniMate将成为用户生活和工作中的得力助手，帮助用户更加高效、健康地管理时间和达成目标。
