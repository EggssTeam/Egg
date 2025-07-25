from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
from db import db  # 假设你已有 db 连接模块

router = APIRouter()
feedback_collection = db["feedback"]
user_collection = db["user"]

# ===== Pydantic 模型 =====
class FeedbackRequest(BaseModel):
    lecture_id: str
    user_id: str
    too_fast: bool = False
    too_slow: bool = False
    boring: bool = False
    bad_question_quality: bool = False
    other: str = ""
    created_at: datetime = datetime.utcnow()

# ===== 提交或更新反馈 =====
@router.post("/submit")
def submit_feedback(feedback: FeedbackRequest):
    filter_query = {
        "lecture_id": ObjectId(feedback.lecture_id),
        "user_id": ObjectId(feedback.user_id)
    }

    update_data = {
        "$set": {
            "too_fast": feedback.too_fast,
            "too_slow": feedback.too_slow,
            "boring": feedback.boring,
            "bad_question_quality": feedback.bad_question_quality,
            "other": feedback.other,
            "created_at": feedback.created_at
        }
    }

    result = feedback_collection.update_one(filter_query, update_data, upsert=True)

    return {
        "message": "反馈提交成功（已覆盖旧记录）",
        "upserted_id": str(result.upserted_id) if result.upserted_id else "existing"
    }

@router.get("/lecture/{lecture_id}/feedback_summary")
def feedback_summary(lecture_id: str):
    lecture_oid = ObjectId(lecture_id)

    stats = {
        "too_fast": feedback_collection.count_documents({"lecture_id": lecture_oid, "too_fast": True}),
        "too_slow": feedback_collection.count_documents({"lecture_id": lecture_oid, "too_slow": True}),
        "boring": feedback_collection.count_documents({"lecture_id": lecture_oid, "boring": True}),
        "bad_question_quality": feedback_collection.count_documents({"lecture_id": lecture_oid, "bad_question_quality": True}),
    }

    return {"feedback_summary": stats}

@router.get("/lecture/{lecture_id}/user/{user_id}/feedback")
def get_user_feedback(lecture_id: str, user_id: str):
    try:
        lecture_oid = ObjectId(lecture_id)
        user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="无效的 ObjectId")

    feedback = feedback_collection.find_one({
        "lecture_id": lecture_oid,
        "user_id": user_oid
    })

    if feedback:
        return {
            "too_fast": feedback.get("too_fast", False),
            "too_slow": feedback.get("too_slow", False),
            "boring": feedback.get("boring", False),
            "bad_question_quality": feedback.get("bad_question_quality", False),
            "other": feedback.get("other", "")
        }
    else:
        raise HTTPException(status_code=404, detail="未找到该用户的反馈信息")

@router.get("/lecture/{lecture_id}/feedback_details")
def feedback_detail_comments(lecture_id: str):
    lecture_oid = ObjectId(lecture_id)

    feedbacks = feedback_collection.find({
        "lecture_id": lecture_oid,
        "other": {"$ne": ""}
    })

    results = []
    for fb in feedbacks:
        user = user_collection.find_one({"_id": fb["user_id"]})
        results.append({
            "user_id": str(fb["user_id"]),
            "username": user["username"] if user else "未知用户",
            "avatar": user["avatar"] if user else "",
            "comment": fb["other"]
        })

    return {"feedback_comments": results}
