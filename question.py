from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict
from bson import ObjectId
from datetime import datetime
from db import db  # 假设你有 db.py 统一连接 MongoDB

router = APIRouter()
question_collection = db["question"]

# Pydantic 模型
class QuestionCreate(BaseModel):
    lecture_id: str
    question: str
    options: Dict[str, str]
    correct_answer: str

# 添加问题接口
@router.post("/add")
def add_question(q: QuestionCreate):
    doc = {
        "lecture_id": ObjectId(q.lecture_id),
        "question": q.question,
        "options": q.options,
        "correct_answer": q.correct_answer,
        "is_send": False,
        "created_at": datetime.utcnow()
    }
    result = question_collection.insert_one(doc)
    return {"message": "问题添加成功", "id": str(result.inserted_id)}

@router.get("/all")
def get_all_questions(lecture_id: str):
    questions = list(question_collection.find(
        {"lecture_id": ObjectId(lecture_id)},
        {"_id": 1, "question": 1, "options": 1, "is_send": 1}
    ))
    for q in questions:
        q["_id"] = str(q["_id"])
    return {"questions": questions}

# @router.get("/auto")
# def auto_get_questions(lecture_id: str):
#     questions = list(question_collection.find(
#         {
#             "lecture_id": ObjectId(lecture_id),
#             "is_send": False,
#         },
#         {"_id": 1, "question": 1, "options": 1, "is_send": 1}
#     ))
#     for q in questions:
#         q["_id"] = str(q["_id"])
#     return {"questions": questions}