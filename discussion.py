from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from bson import ObjectId
from datetime import datetime
# from pymongo import MongoClient
from db import db

# ===== MongoDB 连接 =====
discussion_collection = db["discussion"]
user_collection = db["user"]

# ===== FastAPI 路由器 =====
router = APIRouter()

# ===== Pydantic 模型 =====
class DiscussionCreate(BaseModel):
    lecture_id: str
    user_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DiscussionOut(BaseModel):
    id: str
    lecture_id: str
    user_id: str
    content: str
    created_at: datetime

class DiscussionOutWithUser(BaseModel):
    id: str
    lecture_id: str
    user_id: str
    content: str
    created_at: datetime
    username: str
    avatar: str


# ===== 添加讨论 =====
@router.post("/add", response_model=DiscussionOut)
def add_discussion(discussion: DiscussionCreate):
    doc = discussion.dict()
    doc["lecture_id"] = ObjectId(doc["lecture_id"])
    doc["user_id"] = ObjectId(doc["user_id"])
    result = discussion_collection.insert_one(doc)
    return {
        "id": str(result.inserted_id),
        **discussion.dict()
    }

# ===== 查询某个演讲下的所有讨论 =====
@router.get("/lecture/{lecture_id}", response_model=List[DiscussionOutWithUser])
def get_discussions_by_lecture(lecture_id: str):
    try:
        cursor = discussion_collection.find({"lecture_id": ObjectId(lecture_id)})
    except:
        raise HTTPException(status_code=400, detail="无效的 lecture_id")

    discussions = []
    for d in cursor:
        user = user_collection.find_one({"_id": ObjectId(d["user_id"])})
        discussions.append({
            "id": str(d["_id"]),
            "lecture_id": str(d["lecture_id"]),
            "user_id": str(d["user_id"]),
            "content": d["content"],
            "username": user["username"],
            "avatar": user["avatar"],
            "created_at": d.get("created_at", datetime.utcnow())
        })
    return discussions
