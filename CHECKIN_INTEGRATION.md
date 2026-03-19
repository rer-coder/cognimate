# CogniMate 打卡系统集成指南

## 概述

打卡系统已集成到 CogniMate Server v2.3.0，支持自动识别用户回复并更新打卡状态。

## API 端点

### 1. 创建打卡记录
```http
POST /checkin
Content-Type: application/json

{
    "type": "water",           // 打卡类型: water, exercise, work, study, sleep, medicine, custom
    "title": "下午喝水提醒",    // 打卡标题（可选）
    "scheduled_time": "2026-03-15T15:00:00",  // 计划时间
    "note": "备注信息",         // 备注（可选）
    "user_id": "default"        // 用户ID（可选，默认default）
}
```

### 2. 更新打卡状态
```http
PUT /checkin/{checkin_id}
Content-Type: application/json

{
    "status": "completed",      // 状态: pending, completed, missed, skipped
    "actual_time": "2026-03-15T15:05:00",  // 实际完成时间（可选）
    "note": "已喝500ml"          // 备注（可选）
}
```

### 3. 获取今日打卡列表
```http
GET /checkin/today?user_id=default
```

### 4. 获取打卡统计
```http
GET /checkin/stats?days=7&user_id=default
```

### 5. 解析用户回复
```http
POST /checkin/parse
Content-Type: application/json

{
    "user_input": "喝了",        // 用户回复内容
    "checkin_id": 123           // 可选，如提供则自动更新该打卡
}
```

### 6. 从提醒创建打卡（工具函数）
```http
POST /tools/create_checkin_from_reminder
Content-Type: application/json

{
    "reminder_type": "water",
    "scheduled_time": "2026-03-15T15:00:00",
    "message": "该喝水了！",
    "user_id": "default"
}
```

### 7. 获取待处理打卡（工具函数）
```http
POST /tools/get_pending_checkins
Content-Type: application/json

{
    "arguments": {
        "user_id": "default",
        "limit": 5
    }
}
```

## 主会话集成逻辑

### 识别用户是否在回复打卡

当用户发送消息时，主会话应：

1. **查询待处理打卡**
   ```python
   response = requests.post("http://localhost:8000/tools/get_pending_checkins", json={
       "arguments": {"user_id": "default", "limit": 3}
   })
   pending = response.json()["result"]
   ```

2. **判断是否为打卡回复**
   - 如果有待处理打卡，且消息内容与最近提醒相关
   - 或消息内容简短（<10字）且包含常见打卡关键词

3. **自动解析并更新**
   ```python
   if pending["has_pending"]:
       # 获取最新的待处理打卡
       latest_checkin = pending["pending_checkins"][0]
       
       # 解析用户回复
       parse_response = requests.post("http://localhost:8000/checkin/parse", json={
           "user_input": user_message,
           "checkin_id": latest_checkin["id"]
       })
       
       result = parse_response.json()["result"]
       
       if result["confidence"] == "high":
           # 解析成功，自动更新
           if result.get("updated"):
               return f"已记录：{latest_checkin['title']} ✓"
       else:
           # 置信度低，需要确认
           return "收到！请问你是完成了打卡、没完成，还是需要跳过呢？"
   ```

### 完整集成示例

```python
async def handle_user_message(user_input: str):
    """处理用户消息的主函数"""
    
    # 1. 检查是否有待处理的打卡
    pending_response = requests.post(
        "http://localhost:8000/tools/get_pending_checkins",
        json={"arguments": {"user_id": "default", "limit": 3}}
    )
    pending = pending_response.json()["result"]
    
    # 2. 判断是否可能是打卡回复
    is_checkin_reply = False
    if pending["has_pending"]:
        # 检查消息是否在提醒发送后短时间内
        latest = pending["pending_checkins"][0]
        created_time = datetime.fromisoformat(latest["created_at"])
        time_diff = (datetime.now() - created_time).total_seconds()
        
        # 如果在1小时内，且消息较短，认为是打卡回复
        if time_diff < 3600 and len(user_input) < 20:
            is_checkin_reply = True
    
    # 3. 处理打卡回复
    if is_checkin_reply:
        parse_response = requests.post(
            "http://localhost:8000/checkin/parse",
            json={
                "user_input": user_input,
                "checkin_id": pending["pending_checkins"][0]["id"]
            }
        )
        result = parse_response.json()["result"]
        
        if result["confidence"] == "high":
            status_map = {
                "completed": "✅ 已完成",
                "missed": "❌ 未完成",
                "skipped": "⏭️ 已跳过"
            }
            return f"收到！已记录{pending['pending_checkins'][0]['title']} - {status_map.get(result['status'], result['status'])}"
        else:
            # 无法识别，请求明确回复
            return "不太确定你的意思呢😊 请告诉我'完成'、'没做'或'跳过'好吗？"
    
    # 4. 普通消息处理（原有逻辑）
    # ... 其他处理逻辑
```

## 自动识别规则

系统支持以下关键词自动识别：

### 完成状态 (completed)
- 关键词：`喝了`、`完成`、`做了`、`✅`、`✓`、`☑️`、`搞定`、`ok`、`好的`、`收到`、`已完成`

### 未完成状态 (missed)
- 关键词：`没喝`、`忘了`、`❌`、`错过`、`来不及`、`没做`、`没有`、`忙`、`没空`

### 跳过状态 (skipped)
- 关键词：`跳过`、`不需要`、`取消`、`不用`、`作罢`、`算了`、`改天`、`pass`

## 提醒发送时自动创建打卡

修改提醒发送逻辑：

```python
def send_reminder(reminder_type: str, message: str, scheduled_time: datetime):
    """发送提醒并创建打卡记录"""
    
    # 1. 先创建打卡记录
    checkin_response = requests.post(
        "http://localhost:8000/tools/create_checkin_from_reminder",
        json={
            "reminder_type": reminder_type,
            "scheduled_time": scheduled_time.isoformat(),
            "message": message,
            "user_id": "default"
        }
    )
    checkin_id = checkin_response.json()["result"]["checkin_id"]
    
    # 2. 发送提醒消息
    send_message_to_user(message)
    
    return checkin_id
```

## 数据库结构

### checkins 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | TEXT | 用户ID |
| type | TEXT | 打卡类型 |
| title | TEXT | 打卡标题 |
| scheduled_time | TIMESTAMP | 计划时间 |
| actual_time | TIMESTAMP | 实际完成时间 |
| status | TEXT | 状态 (pending/completed/missed/skipped) |
| note | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### checkin_stats 表
| 字段 | 类型 | 说明 |
|------|------|------|
| date | TEXT | 日期 |
| total_count | INTEGER | 总打卡数 |
| completed_count | INTEGER | 完成数 |
| completion_rate | REAL | 完成率 |
| streak_days | INTEGER | 连续打卡天数 |

## 测试

运行测试用例：
```bash
cd /root/.openclaw/workspace-cognimate/server
python test_checkin.py
```

## 版本信息

- 版本: v2.3.0
- 新增功能: 打卡系统、自动状态识别、打卡统计
- 更新时间: 2026-03-15
