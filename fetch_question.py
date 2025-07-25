from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta
from db import db  # 假设你有 db = MongoClient(...).your_database

router = APIRouter()
fq_collection = db["fetch_question"]
la_collection = db["la"]
q_collection = db["question"]

# Pydantic 模型
class PushRequest(BaseModel):
    lecture_id: str
    question_ids: List[str]

class FetchDeleteRequest(BaseModel):
    lecture_id: str
    user_id: str

class AutoPushRequest(BaseModel):
    lecture_id: str
    number: int
# 系统自动发送题目
@router.post("/autopush")
def auto_push_questions(req: AutoPushRequest):
    lecture_oid = ObjectId(req.lecture_id)
    number = req.number
    questions = list(q_collection.find(
        {
            "lecture_id": lecture_oid,
            "is_send": False,
        },
        {"_id": 1, "question": 1, "options": 1}
    ))

    if not questions:
        return {"message": "所有生成的题目都已推送完", "is_finish": True}

    selected_questions = questions[:min(number, len(questions))]
    question_ids = [q["_id"] for q in selected_questions]

    # 获取听众
    audience = la_collection.find({"lecture_id": lecture_oid})

    count = 0
    for a in audience:
        fq_collection.insert_one({
            "lecture_id": lecture_oid,
            "user_id": a["audience_id"],
            "question_ids": question_ids,
            "created_at": datetime.utcnow()
        })
        count += 1

    q_collection.update_many(
        {"_id": {"$in": question_ids}},
        {"$set": {"is_send": True}}
    )

    return {"message": f"题目已推送给 {count} 位听众，共推送了 {len(selected_questions)} 道题", "is_finish": False, "count": len(selected_questions)}


@router.post("/push")
def push_questions(req: PushRequest):
    lecture_oid = ObjectId(req.lecture_id)
    question_oids = [ObjectId(qid) for qid in req.question_ids]

    # 获取听众
    audience = la_collection.find({"lecture_id": lecture_oid})

    count = 0
    for a in audience:
        fq_collection.insert_one({
            "lecture_id": lecture_oid,
            "user_id": a["audience_id"],
            "question_ids": question_oids,
            "created_at": datetime.utcnow()
        })
        count += 1

    q_collection.update_many(
        {"_id": {"$in": question_oids}},
        {"$set": {"is_send": True}}
    )

    return {"message": f"题目已推送给 {count} 位听众"}

# 听众拉取题目（只弹一次）
@router.get("/fetch")
def fetch_question(lecture_id: str, user_id: str):
    record = fq_collection.find_one({
        "lecture_id": ObjectId(lecture_id),
        "user_id": ObjectId(user_id)
    })

    if record:
        question_ids = record["question_ids"]
        questions = list(q_collection.find({
            "_id": {"$in": question_ids}
        }, {
            "_id": 1, "question": 1, "options": 1, "correct_answer": 1
        }))

        # 将 ObjectId 转换为字符串
        for q in questions:
            q["_id"] = str(q["_id"])

        return {
            "questions": questions
        }

    return {}

# 听众提交答题后删除记录
@router.post("/delete")
def delete_fetched_question(req: FetchDeleteRequest):
    result = fq_collection.delete_many({
        "lecture_id": ObjectId(req.lecture_id),
        "user_id": ObjectId(req.user_id)
    })
    return {"deleted_count": result.deleted_count}

# 清除过期记录（建议放在定时任务中调用）
@router.post("/cleanup")
def cleanup_fetched_question(lecture_id: str):
    result = fq_collection.delete_many({
        "lecture_id": ObjectId(lecture_id),
    })
    return {"deleted_count": result.deleted_count}


# from datetime import datetime, timedelta
#
# expire_time = datetime.utcnow() - timedelta(seconds=题目数 * 10)
#
# fq_collection.delete_many({
#     "lecture_id": lecture_id,
#     "created_at": {"$lt": expire_time}
# })