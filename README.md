# 📚 基于 AI 的智能题库生成系统

## 📋 项目概述

本系统是一个基于 **FastAPI + MongoDB** 的智能题库生成平台，支持通过 **在线 AI API** 自动生成选择题，适用于教学辅助、学习平台等场景。

### ✅ 支持以下文件格式上传并自动生成题目：

* 📄 文本文件（.txt）
* 📘 演示文稿（.pptx）
* 📕 PDF 文件（.pdf）
* 🎧 音频文件（.mp3、.wav）
* 🎬 视频文件（.mp4、.avi）

生成的题目将自动保存到 MongoDB 数据库中，可通过 Web 界面进行管理与展示。

---

## 🛠️ 安装指南

### 1️⃣ 环境准备

```bash
# 可选：清理旧环境
conda remove -n summer1 --all -y

# 创建并激活 Python 环境
conda create -n summer1 python=3.10 -y
conda activate summer1

# 安装依赖
pip install -r requirements.txt
```

---

## 🔑 API 密钥配置

系统支持以下两个核心 API：

| API 类型         | 环境变量名              | 默认地址（可替换为代理）                                     |
| -------------- | ------------------ | ------------------------------------------------ |
| OpenAI GPT-4o  | `OPENAI_API_KEY`   | `https://api.openai.com/v1/chat/completions`     |
| OpenAI Whisper | `OPENAI_API_KEY`   | `https://api.openai.com/v1/audio/transcriptions` |
| DeepSeek       | `DEEPSEEK_API_KEY` | `https://api.deepseek.com/v1/chat/completions`   |

---

### ✅ 方案 A：使用环境变量（推荐）

请将密钥设置为环境变量，避免明文写入代码。

**Linux/macOS：**

```bash
export OPENAI_API_KEY="你的 OpenAI Key"
export DEEPSEEK_API_KEY="你的 DeepSeek Key"
```

**Windows CMD：**

```cmd
set OPENAI_API_KEY=你的 OpenAI Key
set DEEPSEEK_API_KEY=你的 DeepSeek Key
```

**Windows PowerShell：**

```powershell
$env:OPENAI_API_KEY="你的 OpenAI Key"
$env:DEEPSEEK_API_KEY="你的 DeepSeek Key"
```

---

### ⚠️ 方案 B：直接在代码中写入密钥（不推荐）

你可以直接在config.py中写死密钥，而不依赖环境变量，但这会带来安全风险：

```python
OPENAI_API_KEY = "你的 OpenAI Key"
DEEPSEEK_API_KEY = "你的 DeepSeek Key"
```



---

### 🌐 代理服务器配置提示
**API 地址（URL）可以替换为你自己的代理地址**，当你无法直接访问官方 API 时，可以通过代理服务器转发请求，实现对官方 API 的访问。例如在config.py中更改URL：

```python
# 替换 API URL
GPT4O_API_URL="https://your-proxy.com/v1/chat/completions"
WHISPER_API_URL="https://your-proxy.com/v1/audio/transcriptions"
DEEPSEEK_API_URL="https://your-proxy.com/v1/chat/completions"
```

---

## 🚀 启动系统

### 1️⃣ 启动 MongoDB 数据库服务

```bash
# Linux/macOS
sudo mkdir -p /data/db
sudo chown -R $USER /data/db
mongod --dbpath=/data/db
```

```cmd
:: Windows（管理员运行）
mongod --dbpath=C:\mongodb-data
```

默认数据库连接为：`mongodb://localhost:27017/`，数据库名：`mydb`

---

### 2️⃣ 启动 FastAPI 应用服务

```bash
uvicorn main:app --reload
```

浏览器访问： [http://localhost:8000](http://localhost:8000)

---

## 📬 联系与反馈

如遇问题，欢迎到 https://github.com/EggssTeam/Egg 下留言，谢谢支持！

