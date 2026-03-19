# CogniMate 学习记录功能 - 使用指南

## ✅ 已完成的功能

### 1. 学习记录器 (learning_logger.py)
- ✅ 记录学习/纠正/最佳实践
- ✅ 记录错误和异常
- ✅ 记录功能请求
- ✅ 查询学习记录
- ✅ 统计信息

### 2. API 端点 (learning_routes.py)
- ✅ `/tools/log_learning` - 记录学习
- ✅ `/tools/log_error` - 记录错误
- ✅ `/tools/log_feature_request` - 记录功能请求
- ✅ `/tools/query_learnings` - 查询学习
- ✅ `/tools/get_learning_stats` - 获取统计

### 3. 完整服务器 (main.py)
- ✅ 整合原有工具（记忆、情感、调整）
- ✅ 新增学习记录工具
- ✅ 数据库初始化
- ✅ 健康检查

### 4. 辅助文件
- ✅ `start.sh` - 启动脚本
- ✅ `test_learning.py` - 测试脚本
- ✅ 更新的 `TOOLS.md` - 工具文档

---

## 🚀 快速开始

### 1. 启动服务器

```bash
cd /root/.openclaw/workspace-cognimate/server
./start.sh
```

服务器将在 `http://localhost:8000` 启动。

### 2. 测试功能

```bash
python3 /root/.openclaw/workspace-cognimate/server/test_learning.py
```

### 3. 查看 API 文档

浏览器访问: http://localhost:8000/docs

---

## 📝 使用示例

### 示例1：用户纠正时记录

当用户说："不，提醒应该晚一点"

CogniMate 自动调用：
```json
{
  "function_name": "log_learning",
  "arguments": {
    "category": "correction",
    "summary": "用户偏好较晚的提醒时间",
    "details": "用户反馈当前 7:50 的提醒太早，希望延后到 8:20",
    "suggested_action": "更新 USER.md 中的提醒时间偏好",
    "priority": "high",
    "area": "schedule",
    "source": "user_feedback",
    "tags": ["reminder", "time_preference", "correction"]
  }
}
```

记录会保存到：`.learnings/LEARNINGS.md`

### 示例2：工具调用失败时记录

当 API 调用失败：
```json
{
  "function_name": "log_error",
  "arguments": {
    "summary": "天气 API 返回 403 错误",
    "details": "调用天气查询接口时返回 403，可能是 API 密钥过期或达到限额",
    "suggested_action": "检查 API 密钥状态，考虑添加备用天气源",
    "priority": "medium",
    "area": "backend",
    "source": "tool_execution",
    "tags": ["api", "weather", "error"]
  }
}
```

记录会保存到：`.learnings/ERRORS.md`

### 示例3：用户想要新功能

当用户说："你能帮我记录每日饮水量吗？"
```json
{
  "function_name": "log_feature_request",
  "arguments": {
    "summary": "增加每日饮水量记录功能",
    "details": "用户希望 CogniMate 能记录和追踪每日饮水量，与减重目标结合",
    "suggested_action": "设计饮水记录工具，添加到目标追踪模块",
    "priority": "medium",
    "area": "goal",
    "source": "user_request",
    "tags": ["feature", "hydration", "health"]
  }
}
```

记录会保存到：`.learnings/FEATURE_REQUESTS.md`

---

## 🔄 工作流程

```
┌─────────────────┐
│   用户交互       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ 判断是否需要记录？        │
│ • 用户纠正 → log_learning│
│ • 发生错误 → log_error   │
│ • 功能需求 → log_feature │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 调用相应工具             │
│ 写入 .learnings/*.md     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 定期 Review (每周)       │
│ • 查看学习记录            │
│ • 验证有效学习            │
│ • 晋升到 USER.md         │
└─────────────────────────┘
```

---

## 📂 文件结构

```
/root/.openclaw/workspace-cognimate/
├── .learnings/                    # 学习记录目录
│   ├── LEARNINGS.md              # 学习/纠正/最佳实践
│   ├── ERRORS.md                 # 错误记录
│   └── FEATURE_REQUESTS.md       # 功能请求
├── server/                        # 服务器代码
│   ├── main.py                   # 主服务器
│   ├── learning_logger.py        # 学习记录器
│   ├── learning_routes.py        # API 路由
│   ├── start.sh                  # 启动脚本
│   └── test_learning.py          # 测试脚本
├── TOOLS.md                       # 工具文档（已更新）
└── COGNIMATE_IMPROVEMENT_PLAN.md # 融合方案文档
```

---

## 🎯 接下来的观察重点

建议你在使用过程中观察：

1. **我是否会主动记录学习？**
   - 当你纠正我时，我是否记录了？
   - 记录的内容是否准确？

2. **记录的实用性如何？**
   - 是否包含了足够的上下文？
   - 建议操作是否可行？

3. **查询功能是否有用？**
   - 决策前查询历史学习是否有帮助？
   - 查询结果是否相关？

4. **晋升机制是否有效？**
   - 有效学习是否能及时晋升到 USER.md？
   - 晋升后的学习是否被实际应用？

---

## 🔧 故障排除

### 问题1：服务器启动失败
```bash
# 检查 Python 版本
python3 --version  # 需要 3.8+

# 安装依赖
pip3 install fastapi uvicorn

# 手动启动
cd server
python3 main.py
```

### 问题2：无法连接服务器
```bash
# 检查端口占用
lsof -i :8000

# 检查防火墙
curl http://localhost:8000/health
```

### 问题3：学习记录未保存
```bash
# 检查目录权限
ls -la /root/.openclaw/workspace-cognimate/.learnings/

# 检查文件是否存在
cat /root/.openclaw/workspace-cognimate/.learnings/LEARNINGS.md
```

---

## 📊 预期效果

使用学习记录功能后，预期 CogniMate 会：

1. **越来越少犯同样的错误** - 被纠正过的问题会记住
2. **建议越来越符合你的偏好** - 学习你的习惯和喜好
3. **情感支持越来越精准** - 学习哪种回应对你有效
4. **目标管理越来越高效** - 记录有效的达成策略

---

现在基础功能已实现，你可以：

1. **启动服务器** - `./server/start.sh`
2. **运行测试** - `python3 server/test_learning.py`
3. **开始观察** - 在对话中观察我是否记录学习

有任何问题随时告诉我！ 🚀
