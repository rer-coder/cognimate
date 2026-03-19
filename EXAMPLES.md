# CogniMate 工具使用示例

## 与OpenClaw的沟通示例

### 1. 初始设置
**您**："CogniMate，我需要你作为我的个人智能协作者，帮助我管理日程和目标。我已经在本地部署了服务器，提供了5个工具函数：query_memory、update_memory、analyze_sentiment_and_state、generate_dynamic_adjustment和check_context_for_outing。这些工具都可以通过 http://localhost:8000/tools/ 端点访问。请根据TOOLS.md中的定义使用这些工具。"

**OpenClaw**："好的，我已经了解了。我会作为你的个人智能协作者，使用本地服务器提供的工具来帮助你管理日程和目标。请告诉我你需要什么帮助。"

### 2. 查询日程示例
**您**："我今天下午有什么安排？"

**OpenClaw**：
```json
{
  "function_name": "query_memory",
  "arguments": {
    "query": "查询我今天下午的日程"
  }
}
```

**服务器响应**：
```json
{
  "result": {
    "schedules": [
      {"time": "15:30", "event": "团队周会", "location": "飞书会议"},
      {"time": "19:00", "event": "跑步", "location": "公园"}
    ]
  },
  "status": "success"
}
```

**OpenClaw**："你今天下午有以下安排：
- 15:30 团队周会（飞书会议）
- 19:00 跑步（公园）
需要我为你准备什么吗？"

### 3. 处理用户疲劳情况
**您**："我今天感觉很累，不想跑步了。"

**OpenClaw**：
1. 分析情感状态：
```json
{
  "function_name": "analyze_sentiment_and_state",
  "arguments": {
    "user_input": "我今天感觉很累，不想跑步了"
  }
}
```

**服务器响应**：
```json
{
  "result": {
    "sentiment": "negative",
    "energy_level": "low",
    "keywords": ["累", "不想跑步"]
  },
  "status": "success"
}
```

**OpenClaw**：
2. 查询今日计划：
```json
{
  "function_name": "query_memory",
  "arguments": {
    "query": "查询我今天的日程"
  }
}
```

**服务器响应**：
```json
{
  "result": {
    "schedules": [
      {"time": "19:00", "event": "跑步", "location": "公园"}
    ]
  },
  "status": "success"
}
```

**OpenClaw**：
3. 生成调整方案：
```json
{
  "function_name": "generate_dynamic_adjustment",
  "arguments": {
    "current_plan": {"time": "19:00", "event": "跑步", "location": "公园"},
    "user_status": {"sentiment": "negative", "energy_level": "low", "keywords": ["累", "不想跑步"]}
  }
}
```

**服务器响应**：
```json
{
  "result": {
    "adjusted_tasks": [{"time": "19:00", "new_task": "散步40分钟"}],
    "reason": "用户反馈身体不适，建议降低强度防止受伤",
    "impact_on_goal": "总体卡路里消耗预计减少5%，可通过明日增加10分钟运动弥补"
  },
  "status": "success"
}
```

**OpenClaw**："听到你不舒服我很担心。根据你的状态，我建议将今天的跑步调整为散步40分钟，运动量我会帮你平摊到后面两天，这样不影响月度目标。照顾好自己的身体更重要，你觉得呢？"

### 4. 添加新日程
**您**："明天下午2点我有一个客户会议，地点在公司会议室。"

**OpenClaw**：
```json
{
  "function_name": "update_memory",
  "arguments": {
    "operation": "create",
    "data": {
      "event": "客户会议",
      "start_time": "明天 14:00",
      "end_time": "明天 15:30",
      "location": "公司会议室"
    }
  }
}
```

**服务器响应**：
```json
{
  "result": {"message": "操作成功"},
  "status": "success"
}
```

**OpenClaw**："好的，我已经为你添加了明天下午2点的客户会议，地点在公司会议室。需要我提醒你什么吗？"

### 5. 设定目标
**您**："我想设定一个减重目标，希望在3个月内减重5公斤。"

**OpenClaw**：
```json
{
  "function_name": "update_memory",
  "arguments": {
    "operation": "create",
    "data": {
      "title": "减重目标",
      "description": "3个月内减重5公斤",
      "target_date": "3个月后",
      "progress": 0
    }
  }
}
```

**服务器响应**：
```json
{
  "result": {"message": "操作成功"},
  "status": "success"
}
```

**OpenClaw**："好的，我已经为你设定了3个月内减重5公斤的目标。根据这个目标，我建议你每天保持适量的运动和健康的饮食。需要我帮你制定具体的计划吗？"

## 工具调用格式说明

### 调用请求格式
```json
{
  "function_name": "工具名称",
  "arguments": {
    "参数名": "参数值"
  }
}
```

### 响应格式
```json
{
  "result": {
    // 工具返回的结果
  },
  "status": "success"
}
```

## 工作流程说明

1. **接收用户输入**：理解用户的需求和意图
2. **分析情感状态**：调用 `analyze_sentiment_and_state` 工具分析用户的情感和能量水平
3. **查询相关信息**：调用 `query_memory` 工具获取用户的日程、目标等信息
4. **生成调整方案**：如果需要，调用 `generate_dynamic_adjustment` 工具生成计划调整方案
5. **更新记忆**：如果需要，调用 `update_memory` 工具更新用户的日程、目标等信息
6. **组织回复**：将工具返回的结果整合成自然、友好的回复
7. **发送回复**：向用户发送最终的回复

## 注意事项

1. **工具调用顺序**：通常先分析情感，再查询信息，最后生成调整方案
2. **工具响应时间**：所有工具调用应在500ms内完成，以保证对话流畅性
3. **错误处理**：如果工具调用失败，应优雅处理错误并向用户提供适当的反馈
4. **隐私保护**：确保所有工具调用都在本地进行，不向外部服务器发送敏感信息
5. **格式正确性**：严格按照定义的格式调用工具，确保参数正确

通过以上示例和说明，OpenClaw应该能够理解如何与本地服务器交互，使用提供的工具函数来完成任务，为用户提供智能、贴心的个人协作者服务。
