# CogniMate 智伴

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Beta-yellow.svg" alt="Status">
</p>

<p align="center">
  <strong>你的专属 AI 伙伴 — 懂你、陪你、成就你</strong>
</p>

---

## 📖 简介

CogniMate 智伴是一款运行在本地设备上的个人 AI 协作者，帮助用户高效管理日程、养成健康习惯、达成个人目标。

### 核心特点

- 🔒 **本地部署** - 所有数据存储在本地，零隐私风险
- ⏰ **准时可靠** - ±30秒精准提醒，准时率 95%+
- 💝 **情感陪伴** - 识别情绪，温暖回应
- 🧠 **长期记忆** - 记住你的偏好，越用越懂你

---

## ✨ 功能特性

- 📅 **智能日程管理** - 日程提醒、动态调整
- 💧 **健康习惯打卡** - 喝水、运动、睡眠追踪
- 🎯 **目标管理** - 目标设定、进度跟踪、成就庆祝
- ❤️ **情感支持** - 情绪识别、主动关怀
- 🤖 **多模态交互** - 飞书机器人、Web 界面

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- SQLite 3
- 飞书企业账号（用于消息推送）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/rer-coder/cognimate.git
cd cognimate

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 5. 启动服务
python server/main.py
```

---

## 🏗️ 项目结构

```
cognimate/
├── server/                 # 后端服务
│   ├── main.py            # FastAPI 主服务
│   ├── feishu_messenger.py # 飞书消息推送
│   ├── checkin_tracker.py  # 打卡系统
│   ├── goal_tracker.py     # 目标管理
│   └── ...
├── cognimate-agent-skill/ # Agent 技能
├── smart_schedule/        # 智能日程
├── memory/                # 记忆存储
├── skills/                # 技能扩展
├── requirements.txt       # 依赖列表
└── README.md             # 本文件
```

---

## 📚 文档

- [项目说明书](docs/PROJECT.md) - 详细介绍项目背景、技术架构
- [安装指南](docs/INSTALL.md) - 详细安装步骤
- [配置说明](docs/CONFIG.md) - 配置飞书机器人
- [API 文档](docs/API.md) - 接口文档

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

- [Kimi AI](https://kimi.moonshot.cn/) - 提供 AI 能力支持
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
