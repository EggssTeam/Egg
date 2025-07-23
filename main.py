# 内置库
import os
import io
import random
import tempfile
from datetime import datetime


# 第三方库
import uvicorn
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from moviepy import VideoFileClip
from pptx import Presentation

# 配置相关
from config import OPENAI_API_KEY, WHISPER_API_URL, GPT4O_API_URL

# 自定义模块
from db import collection
from ai_client import (
    generate_questions,
    extract_text_from_file,
    extract_images_from_pdf,
    analyze_images_with_o4,
    extract_images_from_pptx,
)
from invitation import invitation_router
from lecture import lecture_router
from user import user_router
from question import question_router




app = FastAPI()
app.include_router(invitation_router, prefix="/invitation", tags=["invitation"])
app.include_router(question_router, prefix="/question", tags=["Question"])
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(lecture_router, prefix="/lecture", tags=["Lecture"])

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
@app.get("/", response_class=FileResponse)
async def serve_login_page():
    return FileResponse("static/login.html")

# ========== 上传并处理文件 ==========-----txt--pptx--pdf--audio--video-----
@app.post("/upload_any_file")
async def upload_any_file(file: UploadFile = File(...), lecture_id: str = Form(None)):
    try:
        ext = os.path.splitext(file.filename)[-1].lower()
        text = ""
        audio_bytes = None
        image_analysis_text = ""
        text_questions = []
        image_questions = []

        if ext == ".txt":
            content = await file.read()
            text = content.decode("utf-8", errors="ignore").strip()
            await file.seek(0)

        elif ext == ".pdf":
            content = await file.read()
            file_stream = io.BytesIO(content)
            text = extract_text_from_file(file_stream, suffix="pdf")
            images = extract_images_from_pdf(file_stream)

            if images:
                selected_images = random.sample(images, min(3, len(images)))
                image_analysis_text = analyze_images_with_o4(selected_images)
                image_questions = generate_questions(image_analysis_text)

            if text.strip():
                text_questions = generate_questions(text)

            if not text.strip() and not image_questions:
                raise ValueError("PDF 文件中未提取到有效内容")

        elif ext == ".pptx":
            content = await file.read()
            text = extract_text_from_file(io.BytesIO(content), suffix="pptx")
            if not text.strip():
                raise ValueError("PPTX 文件中未提取到文本内容")
            text_questions = generate_questions(text)

            images = extract_images_from_pptx(io.BytesIO(content))
            if images:
                selected_images = random.sample(images, min(3, len(images)))
                image_analysis_text = analyze_images_with_o4(selected_images)
                image_questions = generate_questions(image_analysis_text)

        elif ext in [".mp3", ".wav", ".m4a", ".aac"]:
            audio_bytes = await file.read()

        elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_video:
                tmp_video.write(await file.read())
                tmp_video_path = tmp_video.name

            tmp_audio_path = tmp_video_path + ".mp3"
            try:
                video_clip = VideoFileClip(tmp_video_path)
                video_clip.audio.write_audiofile(tmp_audio_path)
                video_clip.close()

                with open(tmp_audio_path, "rb") as f:
                    audio_bytes = f.read()
            finally:
                if os.path.exists(tmp_video_path):
                    os.remove(tmp_video_path)
                if os.path.exists(tmp_audio_path):
                    os.remove(tmp_audio_path)

        else:
            raise ValueError("不支持的文件类型，请上传 txt/pdf/pptx/音频/视频")

        # 处理音频转录和生成问题
        if audio_bytes:
            whisper_response = requests.post(
                WHISPER_API_URL,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={
                    "file": (file.filename, audio_bytes, file.content_type or "application/octet-stream"),
                    "model": (None, "whisper-1")
                },
                timeout=60
            )
            whisper_response.raise_for_status()
            transcribed = whisper_response.json()
            text = transcribed.get("text", "").strip()
            if not text:
                raise ValueError("Whisper API 未返回有效文本")
            text_questions = generate_questions(text)

        # print(f"text_questions count: {len(text_questions)}")
        # print(f"image_questions count: {len(image_questions)}")
        # print(f"image_analysis_text: {image_analysis_text[:200]}")
        # print(f"text snippet: {text[:100]}")

        # 保存问题
        all_questions = text_questions + image_questions
        if not all_questions:
            raise ValueError("未生成任何选择题")

        docs = []
        for q in all_questions:
            source = (
                "音频/视频 + Whisper + DeepSeek" if audio_bytes else
                "图像 + GPT-4o + DeepSeek" if q in image_questions else
                "文本 + DeepSeek"
            )
            docs.append({
                "lecture_id": lecture_id,
                "filename": file.filename,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "source": source,
                "created_at": datetime.now()
            })

        collection.insert_many(docs)

        return {
            "message": "处理成功，选择题已存入数据库",
            "qa_text": text_questions,
            "qa_image": image_questions,
            "text": text,
            "image_summary": image_analysis_text or None
        }

    except Exception as e:
        # print(f"上传处理出错：{e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 启动 FastAPI 应用
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
