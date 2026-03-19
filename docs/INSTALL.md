# CogniMate 安装指南

## 📋 系统要求

- **操作系统**: Linux / macOS / Windows (WSL2)
- **Python**: 3.9 或更高版本
- **内存**: 最低 512MB，推荐 1GB+
- **存储**: 最低 100MB 可用空间

## 🚀 快速安装

### 方式1：使用初始化脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/rer-coder/cognimate.git
cd cognimate

# 2. 运行初始化脚本
./init.sh

# 3. 编辑配置
nano .env

# 4. 启动服务
python server/main.py
```

### 方式2：手动安装

#### 1. 克隆项目

```bash
git clone https://github.com/rer-coder/cognimate.git
cd cognimate
```

#### 2. 创建虚拟环境

```bash
python3 -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境

```bash
# 复制配置模板
cp .env.example .env
cp config.example.json config.json

# 编辑配置（填入你的信息）
nano .env
```

#### 5. 启动服务

```bash
# 开发模式（热重载）
python server/main.py

# 或使用 uvicorn
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 详细配置

### 飞书机器人配置

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建「企业自建应用」
3. 获取 `App ID` 和 `App Secret`
4. 在 `.env` 文件中配置：
   ```env
   FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
   FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   FEISHU_USER_ID=ou_xxxxxxxxxxxxxxxx
   ```

### AI 服务配置

支持 Kimi 或其他 OpenAI 兼容服务：

```env
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

获取地址：https://platform.moonshot.cn/

## 🧪 验证安装

### 1. 检查服务状态

```bash
curl http://localhost:8000/health
```

预期响应：
```json
{"status": "healthy", "service": "CogniMate"}
```

### 2. 查看 API 文档

浏览器访问：http://localhost:8000/docs

### 3. 测试飞书消息

```bash
curl -X POST http://localhost:8000/tools/send_feishu_message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "你的用户ID", "message": "Hello CogniMate!"}'
```

## 🐳 Docker 部署（可选）

```bash
# 构建镜像
docker build -t cognimate .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  --name cognimate \
  cognimate
```

## ⚠️ 常见问题

### 1. 端口被占用

```bash
# 查找占用 8000 端口的进程
lsof -i :8000

# 使用其他端口启动
SERVER_PORT=8080 python server/main.py
```

### 2. 依赖安装失败

```bash
# 更新 pip
pip install --upgrade pip

# 手动安装核心依赖
pip install fastapi uvicorn requests
```

### 3. 飞书消息发送失败

- 检查 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 是否正确
- 确认应用已发布
- 确认用户已添加应用

## 📚 下一步

- [配置说明](CONFIG.md) - 详细配置选项
- [使用指南](../README.md#-功能使用) - 如何使用 CogniMate
- [API 文档](API.md) - 开发接口文档

---

*遇到问题？请提交 [Issue](https://github.com/rer-coder/cognimate/issues)*
