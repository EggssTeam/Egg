from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pymongo import MongoClient

from deepseek_client import generate_questions, pdf_to_text  # 调用 DeepSeek API 生成问题
from deepseek_local_model import generate_questions_local  # 调用本地 DeepSeek 模型生成问题
import uvicorn
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel

from bson import ObjectId
from fastapi.responses import JSONResponse
from pdfminer.high_level import extract_text

import io
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
import requests

app = FastAPI()

# 设置模板路径
templates = Jinja2Templates(directory="templates")

# MongoDB 配置
client = MongoClient("mongodb://localhost:27017/")
db = client["mydb"]
collection = db["qa_collection"]

# 路由：主页
@app.get("/", response_class=HTMLResponse)
async def get_index():
    return FileResponse("templates/index.html")


# 将 ObjectId 转为字符串（为了 JSON 传输）
def objectid_to_str(obj):
    return str(obj['_id'])

# 路由：主页，获取所有问题
@app.get("/question", response_class=HTMLResponse)
async def get_questions(request: Request):
    try:
        questions = list(collection.find())  # 获取所有文档
        # 格式化问题列表
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                "id": objectid_to_str(q),
                "question": q.get("question", "未提供问题"),
                "options": q.get("options", {}),
                "correct_answer": q.get("correct_answer", "未提供正确答案")
            })

        # 渲染 HTML 页面并传递问题数据
        return templates.TemplateResponse("question.html", {
            "request": request,
            "questions": formatted_questions
        })
    except Exception as e:
        # 错误处理
        return HTMLResponse(content=f"发生错误: {e}", status_code=500)

# 定义问题模型
class QuestionUpdate(BaseModel):
    question: str
    options: Dict[str, str]
    correct_answer: str


# 更新问题 API
@app.put("/question/{id}")
async def update_question(id: str, question: QuestionUpdate):
    try:
        # 确保提供的ID是有效的ObjectId格式
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ObjectId")

        # 查询问题是否存在
        existing_question = collection.find_one({"_id": ObjectId(id)})
        if not existing_question:
            raise HTTPException(status_code=404, detail="Question not found")

        # 更新问题
        updated_data = {
            "question": question.question,
            "options": question.options,
            "correct_answer": question.correct_answer,
        }

        # 执行更新操作
        collection.update_one({"_id": ObjectId(id)}, {"$set": updated_data})

        return JSONResponse(status_code=200, content={"message": "Question updated successfully"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 删除问题 API
@app.delete("/question/{id}")
async def delete_question(id: str):
    try:
        # 确保提供的ID是有效的ObjectId格式
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ObjectId")

        # 查询问题是否存在
        existing_question = collection.find_one({"_id": ObjectId(id)})
        if not existing_question:
            raise HTTPException(status_code=404, detail="Question not found")

        # 执行删除操作
        collection.delete_one({"_id": ObjectId(id)})

        return JSONResponse(status_code=200, content={"message": "Question deleted successfully"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


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
                "options": question["options"],  # 存储字典
                "correct_answer": question["correct_answer"],
                "source": "DeepSeek API",
                "created_at": datetime.now()  # 增加时间戳
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


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile):
    try:
        # 直接在内存中创建BytesIO对象
        content = await file.read()
        pdf_stream = io.BytesIO(content)

        # 从内存中提取文本
        text = extract_text(pdf_stream)

        # 调用 DeepSeek API
        questions = generate_questions(text)
        if not questions:
            raise ValueError("生成的选择题为空，请检查输入文本或API响应")

        documents = []
        for q in questions:
            documents.append({
                "filename": file.filename,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "source": "DeepSeek API",
                "created_at": datetime.now()
            })

        if documents:
            collection.insert_many(documents)

        return {"message": "处理成功，选择题已存入数据库", "qa": questions}

    except Exception as e:
        return JSONResponse(content={"error": f"处理失败: {str(e)}"}, status_code=500)


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


# https://api.openai.com/v1/audio/transcriptions

# 宏定义 Whisper API 地址和你的API KEY
WHISPER_API_URL = "https://api.gpt.ge/v1/audio/transcriptions"
OPENAI_API_KEY = "sk-RxDy2FlSA3PP89erC8257937AfE9482cBe6400E14d16E692"
#
# @app.post("/upload_audio/")
# async def upload_audio(file: UploadFile = File(...)):
#     if not file.content_type.startswith("audio/"):
#         raise HTTPException(status_code=400, detail="请上传音频文件")
#
#     audio_bytes = await file.read()
#
#     headers = {
#         "Authorization": f"Bearer {OPENAI_API_KEY}"
#     }
#     files = {
#         "file": (file.filename, audio_bytes, file.content_type),
#         "model": (None, "whisper-1"),
#     }
#
#     async with httpx.AsyncClient() as client:
#         response = await client.post(WHISPER_API_URL, headers=headers, files=files)
#         print("接口返回内容：", response.text)  # <----- 这里打印接口响应原始内容
#
#     if response.status_code != 200:
#         return JSONResponse(status_code=response.status_code, content={"error": response.text})
#
#     result = response.json()
#     text = result.get("text", "")
#
#     # 存入 MongoDB
#     doc = {
#         "filename": file.filename,
#         "transcription": text,
#         "source": "whisper_api",
#         "created_at": datetime.utcnow()
#     }
#     collection.insert_one(doc)
#
#     return {"text": text, "message": "已存入数据库"}



@app.post("/upload_audio/")
async def upload_audio(file: UploadFile = File(...)):
    """
    接收音频文件 -> Whisper识别 -> DeepSeek生成题目 -> 存入数据库
    """
    try:
        # 读取音频数据
        audio_bytes = await file.read()

        # 调用Whisper API
        whisper_headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        whisper_files = {
            "file": (file.filename, audio_bytes, file.content_type),
            "model": (None, "whisper-1")
        }

        whisper_response = requests.post(
            WHISPER_API_URL,
            headers=whisper_headers,
            files=whisper_files,
            timeout=60
        )
        whisper_response.raise_for_status()
        whisper_result = whisper_response.json()
        transcribed_text = whisper_result["text"]

        if not transcribed_text.strip():
            raise ValueError("Whisper API 未返回有效文本")

        # 调用 DeepSeek 生成选择题
        questions = generate_questions(transcribed_text)

        if not questions:
            raise ValueError("生成的选择题为空，请检查输入文本或API响应")

        # 插入MongoDB
        documents = []
        for q in questions:
            documents.append({
                "filename": file.filename,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "source": "Whisper + DeepSeek",
                "created_at": datetime.now()
            })

        collection.insert_many(documents)

        return {
            "message": "音频识别完成，选择题已存入数据库",
            "transcribed_text": transcribed_text,
            "qa": questions
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"处理失败: {str(e)}"}
        )





# 启动 FastAPI 应用
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
