# CogniMate 配置指南

## 📋 配置方式

CogniMate 支持两种配置方式：

1. **环境变量**（推荐）- 通过 `.env` 文件配置
2. **JSON 配置** - 通过 `config.json` 文件配置

---

## 🔧 环境变量配置（推荐）

### 快速开始

```bash
# 1. 复制模板文件
cp .env.example .env

# 2. 编辑 .env 文件，填入你的配置
nano .env
```

### 配置项说明

#### 飞书应用配置（必填）

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_USER_ID=ou_xxxxxxxxxxxxxxxx
```

**获取方式：**

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建企业自建应用」
3. 填写应用名称（如：CogniMate）
4. 在「凭证与基础信息」中获取 `App ID` 和 `App Secret`
5. 在「权限管理」中添加以下权限：
   - `im:chat:readonly` - 获取群组信息
   - `im:message:send` - 发送消息
   - `im:message.group_msg` - 发送群组消息
6. 发布应用后，在飞书客户端添加该应用，获取用户 `open_id`

#### AI 服务配置（必填）

**Kimi（推荐）：**
```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
获取地址：https://platform.moonshot.cn/

**其他 OpenAI 兼容服务：**
```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 服务端配置（可选）

```env
SERVER_PORT=8000          # 服务端口
SERVER_HOST=0.0.0.0       # 监听地址
DEBUG=false               # 调试模式
timezone=Asia/Shanghai    # 时区
USER_NICKNAME=主人         # 用户昵称
```

---

## 📄 JSON 配置

### 快速开始

```bash
# 1. 复制模板文件
cp config.example.json config.json

# 2. 编辑 config.json 文件
nano config.json
```

### 完整配置示例

```json
{
  "user": {
    "name": "你的昵称",
    "user_id": "ou_xxxxxxxxxxxxxxxx",
    "timezone": "Asia/Shanghai"
  },
  "feishu": {
    "app_id": "cli_xxxxxxxxxxxxxxxx",
    "app_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "encrypt_key": "",
    "verification_token": ""
  },
  "ai": {
    "provider": "kimi",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "base_url": "https://api.moonshot.cn/v1",
    "model": "kimi-coding/k2p5"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false
  },
  "reminders": {
    "water": {
      "enabled": true,
      "times": ["09:30", "11:00", "14:00", "16:00", "20:00"],
      "cup_size_ml": 300
    },
    "work": {
      "enabled": true,
      "time": "07:50",
      "workdays_only": true
    },
    "exercise": {
      "enabled": true,
      "time": "19:00",
      "duration_minutes": 30
    },
    "sleep": {
      "enabled": true,
      "time": "22:30"
    }
  },
  "features": {
    "checkin": true,
    "goal_tracking": true,
    "emotion_support": true,
    "smart_schedule": true
  }
}
```

---

## 🔐 安全配置

### 重要提醒

1. **不要将 `.env` 和 `config.json` 提交到 Git**
   - 它们已经在 `.gitignore` 中
   - 提交前请检查：`git status`

2. **保护好你的 API Keys**
   - 不要分享给他人
   - 定期更换密钥
   - 如果发现泄露，立即在平台撤销

3. **飞书应用权限**
   - 只申请必要的权限
   - 定期检查应用授权情况

---

## 🧪 配置验证

启动服务后，可以通过以下方式验证配置：

```bash
# 1. 检查服务是否启动
curl http://localhost:8000/health

# 2. 测试飞书消息发送
curl -X POST http://localhost:8000/tools/send_feishu_message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "你的用户ID", "message": "测试消息"}'
```

---

## ❓ 常见问题

**Q: 启动时报错 "FEISHU_APP_ID not found"**
> A: 检查 `.env` 文件是否存在，且变量名拼写正确

**Q: 飞书消息发送失败**
> A: 检查：
> 1. App ID 和 App Secret 是否正确
> 2. 应用是否已发布
> 3. 用户是否已添加该应用
> 4. 网络是否能访问飞书 API

**Q: AI 回复异常**
> A: 检查：
> 1. API Key 是否有效
> 2. 账户余额是否充足
> 3. 模型名称是否正确

---

*最后更新：2026年3月*
