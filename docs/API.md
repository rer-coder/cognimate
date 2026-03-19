# API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 文档**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI 规范**: `http://localhost:8000/openapi.json`

## 接口列表

### 健康检查

```http
GET /health
```

**响应：**
```json
{
  "status": "healthy",
  "service": "CogniMate"
}
```

### 发送飞书消息

```http
POST /tools/send_feishu_message
Content-Type: application/json

{
  "user_id": "ou_xxxxxxxxxxxxxxxx",
  "message": "消息内容"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "message_id": "om_xxxxxxxxxxxxxxxx"
  }
}
```

### 获取待打卡列表

```http
GET /checkin/get_pending?user_id=ou_xxxxxxxxxxxxxxxx
```

**响应：**
```json
{
  "pending": [
    {
      "id": 1,
      "type": "water",
      "scheduled_time": "09:30",
      "message": "喝水提醒"
    }
  ]
}
```

### 提交打卡

```http
POST /checkin/submit
Content-Type: application/json

{
  "user_id": "ou_xxxxxxxxxxxxxxxx",
  "checkin_id": 1,
  "status": "completed",
  "note": "已完成"
}
```

### 创建目标

```http
POST /goals/create
Content-Type: application/json

{
  "user_id": "ou_xxxxxxxxxxxxxxxx",
  "name": "减肥",
  "target": "3个月减重10斤",
  "deadline": "2026-06-30"
}
```

### 获取目标列表

```http
GET /goals/list?user_id=ou_xxxxxxxxxxxxxxxx
```

**响应：**
```json
{
  "goals": [
    {
      "id": 1,
      "name": "减肥",
      "target": "3个月减重10斤",
      "progress": 30,
      "status": "active"
    }
  ]
}
```

---

*更多接口详见 Swagger UI: http://localhost:8000/docs*
