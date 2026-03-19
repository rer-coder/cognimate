# CogniMate 工具集 v2.0

## 工具概述
CogniMate 通过调用以下工具函数来完成任务，实现智能伴秘的核心功能。

## 基础工具

### 1. query_memory
- **功能**：查询用户的记忆库（日程、目标、档案）
- **参数**：`query` - 自然语言查询
- **调用端点**：`http://localhost:8000/tools/query_memory`

### 2. update_memory
- **功能**：创建、更新或删除记忆库中的条目
- **参数**：`operation`, `data`
- **调用端点**：`http://localhost:8000/tools/update_memory`

### 3. analyze_sentiment_and_state
- **功能**：分析用户输入的情感和隐含状态
- **参数**：`user_input`
- **调用端点**：`http://localhost:8000/tools/analyze_sentiment_and_state`

### 4. generate_dynamic_adjustment
- **功能**：根据用户当前状态生成动态调整方案
- **参数**：`current_plan`, `user_status`
- **调用端点**：`http://localhost:8000/tools/generate_dynamic_adjustment`

---

## 🆕 学习记录工具（新增）

### 5. log_learning
**功能**：记录学习/纠正/知识缺口/最佳实践

**使用场景**：
- 用户纠正你的回答
- 你发现知识过时
- 找到更好的做法

**调用格式**：
```json
{
  "function_name": "log_learning",
  "arguments": {
    "category": "correction",
    "summary": "简短描述",
    "details": "详细内容",
    "suggested_action": "建议操作",
    "priority": "medium",
    "area": "general",
    "source": "user_feedback",
    "tags": ["tag1", "tag2"],
    "related_files": "path/to/file"
  }
}
```

**category 选项**：
- `correction` - 用户纠正
- `knowledge_gap` - 知识缺口
- `best_practice` - 最佳实践

**area 选项**：
- `general` - 通用
- `frontend` - 前端
- `backend` - 后端
- `config` - 配置
- `workflow` - 工作流程
- `sentiment` - 情感支持
- `goal` - 目标管理
- `schedule` - 日程管理

**调用端点**：`http://localhost:8000/tools/log_learning`

---

### 6. log_error
**功能**：记录错误和异常

**使用场景**：
- 命令执行失败
- API 调用异常
- 工具返回错误

**调用格式**：
```json
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
```

**调用端点**：`http://localhost:8000/tools/log_error`

---

### 7. log_feature_request
**功能**：记录用户请求的功能

**使用场景**：
- 用户想要但你做不到的功能
- 用户提出的新需求

**调用格式**：
```json
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
```

**调用端点**：`http://localhost:8000/tools/log_feature_request`

---

### 8. query_learnings
**功能**：查询学习记录

**使用场景**：
- 决策前查看历史学习
- 复盘时检索记录
- 晋升有效学习到 USER.md

**调用格式**：
```json
{
  "function_name": "query_learnings",
  "arguments": {
    "query": "搜索关键词",
    "area": "config",
    "status": "pending",
    "limit": 5
  }
}
```

**调用端点**：`http://localhost:8000/tools/query_learnings`

---

### 9. get_learning_stats
**功能**：获取学习记录统计

**调用格式**：
```json
{
  "function_name": "get_learning_stats",
  "arguments": {}
}
```

**调用端点**：`http://localhost:8000/tools/get_learning_stats`

---

## 学习记录使用原则

### 何时记录？

| 场景 | 工具 | 示例 |
|------|------|------|
| 用户纠正你 | log_learning | "不，提醒应该晚一点" |
| 你发现知识过时 | log_learning | "这个 API 已经废弃了" |
| 找到更好的做法 | log_learning | "用这种方式更快" |
| 命令/工具失败 | log_error | API 返回 500 |
| 用户想要新功能 | log_feature_request | "你能帮我做 X 吗？" |

### 记录流程

```
用户纠正/错误发生
       ↓
调用 log_learning / log_error
       ↓
写入 .learnings/*.md
       ↓
定期 review → 有效学习
       ↓
晋升到 USER.md / AGENTS.md
```

### 最佳实践

1. **即时记录** - 纠正/错误发生后立即记录
2. **具体描述** - 包含上下文和复现步骤
3. **建议修复** - 不只是记录问题，还要提供解决方案
4. **定期 Review** - 每周检查学习记录，晋升有效条目
5. **标签分类** - 使用一致的标签便于检索

---

## 完整工作流程示例

### 示例1：用户纠正

**用户**："明天提醒别那么早"

**CogniMate**：
```json
{
  "function_name": "log_learning",
  "arguments": {
    "category": "correction",
    "summary": "用户偏好较晚的提醒时间",
    "details": "用户反馈当前提醒时间太早，希望延后",
    "suggested_action": "将提醒时间从 7:50 调整到 8:20",
    "priority": "high",
    "area": "schedule",
    "source": "user_feedback",
    "tags": ["reminder", "time_preference"]
  }
}
```

### 示例2：工具调用失败

**CogniMate**：
```json
{
  "function_name": "log_error",
  "arguments": {
    "summary": "天气 API 调用失败",
    "details": "调用 weather API 返回 403，可能是密钥过期",
    "suggested_action": "检查 API 密钥，考虑备用方案",
    "priority": "high",
    "area": "backend",
    "source": "tool_execution",
    "tags": ["api", "weather", "authentication"]
  }
}
```

### 示例3：查询历史学习

**CogniMate**：
```json
{
  "function_name": "query_learnings",
  "arguments": {
    "query": "提醒时间",
    "area": "schedule",
    "limit": 3
  }
}
```

**返回**：历史关于提醒时间的学习记录，用于优化当前建议。

---

## 服务器启动

```bash
cd /root/.openclaw/workspace-cognimate/server
./start.sh
```

服务器将在 `http://localhost:8000` 启动。

## API 文档

启动服务器后访问：http://localhost:8000/docs

---

## 🆕 打卡系统工具（新增）

### 10. create_checkin
**功能**：创建打卡记录

**调用格式**：
```json
{
  "function_name": "create_checkin",
  "arguments": {
    "type": "water",
    "title": "下午喝水提醒",
    "scheduled_time": "2026-03-15T15:00:00",
    "note": "",
    "user_id": "default"
  }
}
```

**调用端点**：`http://localhost:8000/tools/create_checkin`

---

### 11. update_checkin
**功能**：更新打卡状态

**调用格式**：
```json
{
  "function_name": "update_checkin",
  "arguments": {
    "checkin_id": 123,
    "status": "completed",
    "actual_time": "2026-03-15T15:05:00",
    "note": "已喝500ml温水"
  }
}
```

**status 选项**：
- `pending` - 待完成
- `completed` - 已完成
- `missed` - 未完成
- `skipped` - 已跳过

**调用端点**：`http://localhost:8000/tools/update_checkin`

---

### 12. get_pending_checkins
**功能**：获取待处理的打卡记录（用于识别用户是否在回复打卡）

**调用格式**：
```json
{
  "function_name": "get_pending_checkins",
  "arguments": {
    "user_id": "default",
    "limit": 5
  }
}
```

**调用端点**：`http://localhost:8000/tools/get_pending_checkins`

---

### 13. parse_checkin_response
**功能**：解析用户回复，自动识别打卡状态

**调用格式**：
```json
{
  "function_name": "parse_checkin_response",
  "arguments": {
    "user_input": "喝了",
    "checkin_id": 123
  }
}
```

**自动识别规则**：
- ✅ `completed`："喝了"、"完成"、"做了"、"✅"、"ok"、"搞定"
- ❌ `missed`："没喝"、"忘了"、"❌"、"错过"、"没做"
- ⏭️ `skipped`："跳过"、"不需要"、"取消"、"pass"

**调用端点**：`http://localhost:8000/tools/parse_checkin_response`

---

### 14. get_today_checkins
**功能**：获取今日打卡列表

**调用格式**：
```json
{
  "function_name": "get_today_checkins",
  "arguments": {
    "user_id": "default"
  }
}
```

**调用端点**：`http://localhost:8000/tools/get_today_checkins`

---

### 15. get_checkin_stats
**功能**：获取打卡统计

**调用格式**：
```json
{
  "function_name": "get_checkin_stats",
  "arguments": {
    "days": 7,
    "user_id": "default"
  }
}
```

**返回内容**：
- 总打卡数、完成数、完成率
- 按类型统计（喝水、运动等）
- 当前连续打卡天数
- 历史最长连续天数

**调用端点**：`http://localhost:8000/tools/get_checkin_stats`

---

## 打卡系统工作流程

### 完整打卡流程示例

**1. 发送提醒时自动创建打卡**：
```json
{
  "function_name": "create_checkin_from_reminder",
  "arguments": {
    "reminder_type": "water",
    "scheduled_time": "2026-03-15T15:00:00",
    "message": "💧 骷髅王，第5杯水时间到！"
  }
}
```

**2. 用户回复后识别打卡状态**：
```json
{
  "function_name": "parse_checkin_response",
  "arguments": {
    "user_input": "喝了",
    "checkin_id": 1
  }
}
```

**3. 根据解析结果回复用户**：
- 高置信度："✅ 已记录！下午喝水打卡完成！继续保持 💪"
- 低置信度："请明确告诉我'完成'、'没做'或'跳过'好吗？"

---

## 提醒发送时的打卡提示

所有提醒消息末尾添加打卡提示：

```
💧 骷髅王，第5杯水时间到！下午茶时间到~ 用水代替零食，健康又减脂~

💡 回复我确认打卡：喝了 / 没喝 / 跳过
```
