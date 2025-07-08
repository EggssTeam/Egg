# 📚 基于DeepSeek的智能题库生成系统
## 📋 项目概述
```
基于FastAPI构建的智能题库生成系统，支持双模引擎：
- **本地模型**：部署DeepSeek-R1-Distill-Qwen-1.5B模型
- **在线API**：通过系统环境变量配置API密钥
- 核心功能：
  - 文本文件上传自动生成选择题
  - MongoDB题目存储与管理
  - 提供FastAPI接口和网页界面
   ```

## 🛠️ 安装指南

### 1. 环境准备
```bash
# 创建conda虚拟环境（Python 3.10）
conda remove -n summer1 --all -y
conda create -n summer1 python=3.10 -y
conda activate summer1

# 安装依赖
pip install -r requirements.txt
```

### 2. 模型配置（二选一）
#### 选项A：使用在线API
```bash
# 设置系统环境变量（临时生效）
export DEEPSEEK_API_KEY="您的API密钥"  # Linux/macOS
set DEEPSEEK_API_KEY="您的API密钥"     # Windows cmd
$env:DEEPSEEK_API_KEY="您的API密钥"    # Windows PowerShell

# 永久生效配置（推荐）：
# Linux/macOS: 添加到 ~/.bashrc 或 ~/.zshrc
# Windows: 通过系统属性->高级->环境变量添加
```

#### 选项B：使用本地模型
```bash
# 下载模型（约5GB）
huggingface-cli login
huggingface-cli download \
  deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
  --local-dir ./models/deepseek \
  --resume-download
```

## 🚀 运行系统

### 1. 启动数据库服务
```bash
# Linux/macOS
sudo mkdir -p /data/db
sudo chown -R $USER /data/db
mongod --dbpath=/data/db

# Windows（管理员权限运行）
mongod --dbpath=C:\\mongodb-data
```

### 2. 启动应用服务
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
