from wsgiref.validate import validator

from fastapi import FastAPI, UploadFile, HTTPException, Form, Body
from fastapi.responses import HTMLResponse, FileResponse
# from fastapi.templating import Jinja2Templates
# from templates import templates
from fastapi.requests import Request
from pymongo import MongoClient
from starlette.responses import RedirectResponse

from db import collection, user_collection
from deepseek_client import generate_questions, pdf_to_text  # 调用 DeepSeek API 生成问题
from deepseek_local_model import generate_questions_local  # 调用本地 DeepSeek 模型生成问题
import uvicorn
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel
import re

from bson import ObjectId
from fastapi.responses import JSONResponse
from pdfminer.high_level import extract_text

import io
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
import requests
import os

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from pydantic import BaseModel, EmailStr, validator
import re
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from pymongo import MongoClient
import re

from lecture import lecture_router
from user import user_router, verify_password
from question import question_router
from fastapi.staticfiles import StaticFiles



app = FastAPI()

# 设置模板路径
# templates = Jinja2Templates(directory="templates")

# # MongoDB 配置
# client = MongoClient("mongodb://localhost:27017/")
# db = client["mydb"]
# collection = db["qa_collection"]
# user_collection = db["user"]


app.include_router(question_router, prefix="/question", tags=["Question"])


# 加载路由
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(lecture_router, prefix="/lecture", tags=["Lecture"])

#
# app.mount("/", StaticFiles(directory="static", html=True), name="static")

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# 新的初始页面 / ，可以返回一个新的 HTML 文件，例如：home.html
# @app.get("/", response_class=HTMLResponse)
# async def get_home():
#     return FileResponse("templates/login.html")  # 这是你设置的新初始界面

# 把 static 文件夹挂载到 /lecture_list 路径下，且html文件默认访问 lecture_list.html
# app.mount("/lecture_list", StaticFiles(directory="static", html=True), name="lecture_list")
#
# @app.get("/lecture_list")
# async def lecture_list():
#     return FileResponse("static/lecture_list.html")
#
# @app.get("/lecture_detail.html")
# async def lecture_detail():
#     return FileResponse("static/lecture_detail.html")

#
#
# # 设置登录页面
# @app.get("/", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})
#
# @app.get("/personal", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse("personal.html", {"request": request})
#
#
# @app.get("/register", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})

# 处理登录接口，使用 Body 来接收 JSON 格式数据
# @app.post("/login")
# async def login(user: dict = Body(...)):
#     email = user.get("email")
#     password = user.get("password")
#
#     if email == "user@example.com" and password == "password123":
#         return RedirectResponse(url="/index", status_code=303)
#     raise HTTPException(status_code=401, detail="Invalid credentials")
#
# # 路由：主页
# @app.get("/index", response_class=HTMLResponse)
# async def get_index():
#     return FileResponse("templates/person.html")


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

    import io
    from fastapi.responses import JSONResponse
    from pdfminer.high_level import extract_text
#
# @app.post("/upload_pdf")
# async def upload_pdf(file: UploadFile):
#     try:
#         content = await file.read()
#
#         pdf_stream = io.BytesIO(content)
#
#         text = extract_text(pdf_stream)
#         if not text.strip():
#             raise ValueError("PDF文本提取为空")
#
#         questions = generate_questions(text)
#         if not questions:
#             raise ValueError("生成的选择题为空，请检查输入文本或API响应")
#
#         documents = []
#         for q in questions:
#             documents.append({
#                 "filename": file.filename,
#                 "question": q["question"],
#                 "options": q["options"],
#                 "correct_answer": q["correct_answer"],
#                 "source": "DeepSeek API",
#                 "created_at": datetime.now()
#             })
#
#         if documents:
#             collection.insert_many(documents)
#
#         return {"message": "处理成功，选择题已存入数据库", "qa": questions}
#
#     except Exception as e:
#         print(f"/upload_pdf 出错: {e}")
#         return JSONResponse(content={"error": f"处理失败: {str(e)}"}, status_code=500)


from fastapi import UploadFile, File, Form

@app.post("/upload_pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    lecture_id: str = Form(...)  # 添加这个参数
):
    try:
        content = await file.read()
        pdf_stream = io.BytesIO(content)

        text = extract_text(pdf_stream)
        if not text.strip():
            raise ValueError("PDF文本提取为空")

        questions = generate_questions(text)
        if not questions:
            raise ValueError("生成的选择题为空，请检查输入文本或API响应")

        documents = []
        for q in questions:
            documents.append({
                "filename": file.filename,
                "lecture_id": lecture_id,  # 加入 lecture_id
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
        print(f"/upload_pdf 出错: {e}")
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

# https://api.openai.com/v1/audio/transcriptions

# 宏定义 Whisper API 地址和你的API KEY
WHISPER_API_URL = "https://api.gpt.ge/v1/audio/transcriptions"
GPT4O_API_URL = "https://api.gpt.ge/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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

@app.post("/analyze_file/")
async def analyze_file(file: UploadFile = File(...)):
    # 读取文件内容
    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_text = content_bytes.decode("latin1")

    # 请求 GPT-4o 分析文本内容
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "你是一个能够理解并总结文件内容的AI助手。"},
            {"role": "user", "content": f"请分析以下文本并生成简洁的总结：\n\n{content_text}"}
        ],
        "temperature": 0.3
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(GPT4O_API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            return {"error": f"OpenAI API 请求失败: {response.status_code}", "detail": response.text}
        result = response.json()

    summary_text = result["choices"][0]["message"]["content"].strip()

    # 存入 MongoDB
    doc = {
        "filename": file.filename,
        "original_text": content_text,
        "summary": summary_text,
        "created_at": datetime.now()
    }
    collection.insert_one(doc)

    return {
        "filename": file.filename,
        "summary": summary_text
    }




# 启动 FastAPI 应用
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
