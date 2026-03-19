# CogniMate 智能日程管理系统

## 核心架构原则

### 1. 数据库为唯一真相源
- 所有日程必须从数据库读取
- 所有变更必须先更新数据库，再同步Cron

### 2. 变更检测与汇报机制
```
用户输入 → 检测变化 → 生成变更清单 → 汇报用户 → 等待确认 → 执行更新 → 同步Cron
```

### 3. 部分同意机制
- 只汇报变化的日程项
- 用户可以说"A不同意，其他同意"
- 只执行用户同意的变更

### 4. 位置感知
- 检测用户位置变化（公司/老家/出差）
- 自动分析影响的日程
- 汇报变更建议

## 快速开始

### 1. 安装依赖

```bash
cd /root/.openclaw/workspace-cognimate/smart_schedule
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python database/migration.py
```

这将创建所有必要的表：
- `schedules` - 日程核心
- `goals` - 长期目标
- `user_context` - 实时状态
- `schedule_changes` - 变更历史
- `location_rules` - 位置规则
- `cron_sync_log` - Cron同步日志

### 3. 启动API服务

```bash
python api/main.py
```

服务将在 `http://localhost:8001` 启动。

访问文档：http://localhost:8001/docs

## 核心API端点

### 变更管理

#### POST /analyze_impact
分析用户输入的影响
```json
{
  "user_input": "明天下午的会议改到后天"
}
```

#### POST /propose_changes
生成变更建议
```json
{
  "old_schedules": [...],
  "new_schedules": [...]
}
```

#### POST /confirm_changes
执行确认的变更
```json
{
  "batch_id": "batch_20260316084500",
  "user_confirmation": "除了第2项，其他同意"
}
```

### 日程查询

#### GET /schedules/today
获取今日日程（从数据库）

#### GET /schedules/range?start=2026-03-16&end=2026-03-20
获取日期范围日程

#### POST /sync_cron
数据库同步到Cron

### 位置感知

#### POST /location/update
更新用户位置
```json
{
  "location": "business_trip"
}
```

#### GET /location/current
获取当前位置

### 日程CRUD

#### POST /schedules
创建日程

#### GET /schedules/{schedule_id}
获取日程

#### PUT /schedules/{schedule_id}
更新日程

#### DELETE /schedules/{schedule_id}
删除日程

## 使用示例

### 示例1：处理用户变更请求

```python
import requests

# 1. 分析用户输入的影响
response = requests.post("http://localhost:8001/analyze_impact", json={
    "user_input": "明天下午的会议改到后天"
})
print(response.json())

# 2. 获取当前日程
response = requests.get("http://localhost:8001/schedules/today")
current_schedules = response.json()['data']

# 3. 模拟修改后的日程
modified_schedules = [...]  # 修改后的日程

# 4. 生成变更建议
response = requests.post("http://localhost:8001/propose_changes", json={
    "old_schedules": current_schedules,
    "new_schedules": modified_schedules
})
result = response.json()['data']
print(result['confirmation_prompt'])  # 显示给用户

# 5. 用户确认后执行变更
response = requests.post("http://localhost:8001/confirm_changes", json={
    "batch_id": result['batch_id'],
    "user_confirmation": "除了第2项，其他同意"
})
print(response.json())
```

### 示例2：位置变更处理

```python
import requests

# 用户告知出差
response = requests.post("http://localhost:8001/location/update", json={
    "location": "business_trip"
})
result = response.json()['data']

if result['location_changed']:
    print(result['report'])  # 显示位置变更报告
    print(f"影响了 {result['affected_count']} 个日程")
```

### 示例3：直接操作数据库

```python
from core.schedule_manager import ScheduleManager

# 初始化管理器
manager = ScheduleManager("smart_schedule.db")

# 获取今日日程
schedules = manager.get_today_schedules()
print(f"今日有 {len(schedules)} 个日程")

# 更新位置
result = manager.update_location("company")
if result['location_changed']:
    print(result['report'])

# 同步到Cron
sync_results = manager.sync_to_cron()
print(f"同步完成: {len(sync_results)} 个日程")
```

## 数据库表结构

### schedules 表
```sql
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    location TEXT,
    category TEXT DEFAULT 'general',
    priority INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    recurrence_rule TEXT,
    source_type TEXT DEFAULT 'manual',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);
```

### schedule_changes 表
```sql
CREATE TABLE schedule_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_type TEXT NOT NULL,
    schedule_id INTEGER,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    user_confirmation TEXT,
    impact_analysis TEXT,
    confirmed_at DATETIME,
    applied_at DATETIME,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 确认回复格式

系统支持多种确认回复格式：

1. **全部同意**
   - "全部同意"
   - "都同意"
   - "ok"
   - "好的"

2. **全部不同意**
   - "全部不同意"
   - "都不同意"
   - "算了"
   - "取消"

3. **部分同意**
   - "除了第2项，其他同意"
   - "第1、3项不同意"
   - "除了1和2，其他都同意"
   - "2除外，其他都ok"

## 位置规则

系统内置以下位置规则：

| 位置 | 影响类别 | 调整策略 |
|------|----------|----------|
| company | meeting,collaboration | 提前10分钟提醒 |
| hometown | work,meeting | 推迟到下周 |
| business_trip | local_activity,personal | 建议取消 |

可通过 `location_rules` 表自定义规则。

## 项目结构

```
smart_schedule/
├── database/
│   ├── __init__.py
│   ├── migration.py      # 数据库迁移脚本
│   └── db.py             # 数据库操作
├── core/
│   ├── __init__.py
│   ├── change_detector.py    # 变更检测引擎
│   ├── impact_analyzer.py    # 影响分析器
│   ├── report_generator.py   # 汇报生成器
│   ├── confirmation_parser.py # 部分确认解析器
│   └── schedule_manager.py   # 日程管理器
├── api/
│   ├── __init__.py
│   └── main.py           # FastAPI路由
├── tests/                # 测试用例
├── requirements.txt
└── README.md             # 本文件
```

## 测试

运行测试：

```bash
pytest tests/
```

## 注意事项

1. **数据库为唯一真相源**：所有操作必须通过API进行，直接修改数据库可能导致数据不一致
2. **先数据库后Cron**：变更必须先写入数据库，再同步到Cron
3. **用户确认**：高影响变更必须获得用户确认才能执行
4. **软删除**：删除操作默认使用软删除，保留历史记录
