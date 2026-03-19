# CogniMate 智伴

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-orange.svg" alt="FastAPI">
</p>

<p align="center">
  <strong>你的专属 AI 伙伴 — 懂你、陪你、成就你</strong>
</p>

---

## 📖 简介

CogniMate 智伴是一款**本地化部署**的个人 AI 协作者，帮助你：

- 📅 管理日程，准时提醒重要事项
- 💧 养成健康习惯（喝水、运动、睡眠）
- 🎯 设定目标，跟踪进度，达成成就
- ❤️ 提供情感支持和陪伴

### ✨ 核心特点

| 特性 | 说明 |
|------|------|
| 🔒 **隐私安全** | 数据本地存储，不上传云端 |
| ⏰ **准时可靠** | ±30秒精准提醒，多重备用保障 |
| 💝 **情感陪伴** | 识别情绪，温暖回应 |
| 🤖 **多模态** | 支持飞书、Web 等多种交互方式 |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/rer-coder/cognimate.git
cd cognimate
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制模板文件
cp .env.example .env

# 编辑 .env 文件，填入你的配置
nano .env  # 或使用你喜欢的编辑器
```

**必填配置：**
```env
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_USER_ID=ou_xxxxxxxxxxxxxxxx
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 📖 **配置详细说明**见 [CONFIG.md](docs/CONFIG.md)

### 5. 启动服务

```bash
# 方式1：直接启动
python server/main.py

# 方式2：使用启动脚本
cd server && ./start.sh

# 方式3：使用 uvicorn
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问 http://localhost:8000/docs 查看 API 文档。

---

## 📁 项目结构

```
cognimate/
├── server/                    # 后端服务
│   ├── main.py               # FastAPI 主服务入口
│   ├── feishu_messenger.py   # 飞书消息推送
│   ├── checkin_tracker.py    # 打卡系统
│   ├── goal_tracker.py       # 目标管理
│   ├── decision_helper.py    # 决策辅助
│   └── ...
├── smart_schedule/           # 智能日程模块
│   ├── api/                  # API 接口
│   ├── core/                 # 核心逻辑
│   └── database/             # 数据库
├── cognimate-agent-skill/    # Agent 技能扩展
├── docs/                     # 文档
├── .env.example              # 环境变量模板
├── config.example.json       # JSON 配置模板
├── requirements.txt          # 依赖列表
└── README.md                 # 本文件
```

---

## ⚙️ 配置说明

### 飞书机器人配置

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建「企业自建应用」
3. 获取 `App ID` 和 `App Secret`
4. 配置权限：
   - `im:chat:readonly`
   - `im:message:send`
   - `im:message.group_msg`
5. 发布应用并获取用户授权

### AI 服务配置

支持多种 AI 服务：

**Kimi（推荐）：**
```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**OpenAI 兼容：**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
```

---

## 🎯 功能使用

### 设置提醒

通过飞书向 CogniMate 发送消息：

```
设置每天早上8点提醒我吃早饭
```

### 打卡

收到提醒后回复：

```
吃了
```

或

```
打卡完成
```

### 设定目标

```
我想减肥，目标3个月减10斤
```

CogniMate 会帮你制定计划并跟踪进度。

---

## 📚 文档

- [安装指南](docs/INSTALL.md) - 详细安装步骤
- [配置说明](docs/CONFIG.md) - 完整配置选项
- [API 文档](docs/API.md) - 接口文档
- [开发指南](docs/DEVELOPMENT.md) - 二次开发说明
- [部署指南](docs/DEPLOY.md) - 生产环境部署

---

## 🏗️ 技术栈

- **后端**：FastAPI + Uvicorn
- **数据库**：SQLite
- **AI**：Kimi / OpenAI 兼容 API
- **消息**：飞书开放平台
- **任务调度**：APScheduler / Cron

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📜 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

- [Kimi AI](https://kimi.moonshot.cn/) - AI 能力支持
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Feishu Open Platform](https://open.feishu.cn/) - 飞书开放平台

---

## 📮 联系我们

- 项目主页：https://github.com/rer-coder/cognimate
- 问题反馈：https://github.com/rer-coder/cognimate/issues

---

<p align="center">
  Made with ❤️ by CogniMate Team
</p>
