from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from pymongo import MongoClient
from deepseek_client import generate_questions  # 调用 DeepSeek API 生成问题
from deepseek_local_model import generate_questions_local  # 调用本地 DeepSeek 模型生成问题
import uvicorn

from fastapi import FastAPI, UploadFile, HTTPException
from deepseek_local_model import generate_questions_local  # 确保导入修改后的函数
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict
app = FastAPI()

# MongoDB 配置
client = MongoClient("mongodb://localhost:27017/")
db = client["mydb"]
collection = db["qa_collection"]

# 路由：主页
@app.get("/", response_class=HTMLResponse)
async def get_index():
    return FileResponse("index.html")

# 路由：上传文件并调用 DeepSeek API 生成选择题
@app.post("/upload")
async def upload_file(file: UploadFile):
    content = (await file.read()).decode("utf-8")
    try:
        # 调用 DeepSeek API 生成问题
        questions = generate_questions(content)

        # 检查是否有问题数据
        if not questions:
            raise ValueError("生成的选择题为空，请检查输入文本或API响应")

        # 将每个问题作为一个独立文档插入到 MongoDB
        documents = []
        for question in questions:
            doc = {
                "filename": file.filename,
                "question": question["question"],
                "option_A": question["options"]["A"],
                "option_B": question["options"]["B"],
                "option_C": question["options"]["C"],
                "option_D": question["options"]["D"],
                "correct_answer": question["correct_answer"],
                "source": "DeepSeek API"
            }
            documents.append(doc)

        # 确保列表非空后才执行插入
        if documents:
            collection.insert_many(documents)
        else:
            raise ValueError("没有有效的选择题可以插入数据库")

        return {
            "message": "生成完成，选择题已存入数据库（DeepSeek API）。",
            "qa": questions  # 返回生成的问题
        }
    except Exception as e:
        return {"error": f"处理失败: {str(e)}"}


@app.post("/upload_local")
async def upload_file_local(file: UploadFile):
    """
    上传文件并用本地 DeepSeek 模型生成选择题
    修改点：
    1. 更严格的错误处理
    2. 适配新的 generate_questions_local() 返回格式
    3. 优化数据库文档结构
    """
    try:
        # 读取文件内容
        content = (await file.read()).decode("utf-8")
        if not content.strip():
            raise HTTPException(status_code=400, detail="文件内容为空")

        # 调用本地模型生成问题
        generated_questions = generate_questions_local(content)
        if not generated_questions:
            raise HTTPException(status_code=500, detail="模型未能生成有效问题")

        # 构建 MongoDB 文档
        documents = []
        for question in generated_questions:
            doc = {
                "filename": file.filename,
                "question": question["question"],
                "options": question["options"],  # 改为统一存储为字典
                "correct_answer": question["correct_answer"],
                "source": "deepseek_local",
                "created_at": datetime.now()
            }
            documents.append(doc)

        # 批量插入数据库
        if documents:
            result = collection.insert_many(documents)
            return {
                "message": f"成功生成并存储 {len(result.inserted_ids)} 道选择题",
                "qa": generated_questions
            }
        else:
            raise HTTPException(status_code=500, detail="没有有效数据可存储")

    except HTTPException as he:
        raise he  # 直接传递已处理的HTTP异常
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

# 路由：从 MongoDB 获取最新问题
@app.get("/get_question")
async def get_question():
    try:
        # 从 MongoDB 中获取最新的一条问题数据
        question_data = collection.find_one({}, sort=[('_id', -1)])  # 按照 _id 排序，获取最新的
        if question_data:
            # 返回问题内容（去掉 _id）
            question_data["_id"] = str(question_data["_id"])  # 转换 _id 为字符串以便 JSON 序列化
            return question_data
        else:
            return {"error": "没有问题数据"}
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}

# 启动 FastAPI 应用
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
