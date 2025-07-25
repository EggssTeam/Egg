from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

from pymongo import MongoClient

# 数据库连接
client = MongoClient("mongodb://localhost:27017/")
db = client["mydb"]
la_collection = db["la"]
user_collection = db["user"]
lecture_collection = db["lecture"]

router = APIRouter()

# Pydantic 模型
class LARecord(BaseModel):
    lecture_id: str
    audience_id: str
    is_present: Optional[bool] = False
    joined_at: Optional[datetime] = None

#  添加记录
@router.post("/add")
def add_la(record: LARecord):
    la_collection.insert_one({
        "lecture_id": ObjectId(record.lecture_id),
        "audience_id": ObjectId(record.audience_id),
        "is_present": record.is_present,
        "joined_at": record.joined_at or datetime.utcnow()
    })
    return {"message": "加入成功"}

#  删除记录
@router.delete("/delete")
def delete_la(lecture_id: str = Query(...), audience_id: str = Query(...)):
    result = la_collection.delete_one({
        "lecture_id": ObjectId(lecture_id),
        "audience_id": ObjectId(audience_id)
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="记录未找到")
    return {"message": "删除成功"}

#  根据 lecture_id 查询听众
@router.get("/by-lecture")
def get_by_lecture(lecture_id: str):
    records = list(la_collection.find({"lecture_id": ObjectId(lecture_id)}))
    for r in records:
        r["_id"] = str(r["_id"])
        r["lecture_id"] = str(r["lecture_id"])
        r["audience_id"] = str(r["audience_id"])
    return {"records": records}

#  根据 audience_id 查询参加的演讲
@router.get("/by-audience")
def get_by_audience(audience_id: str):
    records = list(la_collection.find({"audience_id": ObjectId(audience_id)}))
    for r in records:
        r["_id"] = str(r["_id"])
        r["lecture_id"] = str(r["lecture_id"])
        r["audience_id"] = str(r["audience_id"])
    return {"records": records}

#  查询 is_present 为 true 的记录（可选条件）
# @router.get("/present")
# def get_present_records(
#     lecture_id: str,
# ):
#     query = {
#         "is_present": True,
#         "lecture_id": ObjectId(lecture_id)
#     }
#
#     records = list(la_collection.find(query))
#     for r in records:
#         r["_id"] = str(r["_id"])
#         r["lecture_id"] = str(r["lecture_id"])
#         r["audience_id"] = str(r["audience_id"])
#     return {"records": records}

@router.get("/present")
def get_present_users(lecture_id: str):
    try:
        lecture_oid = ObjectId(lecture_id)
    except:
        return {"error": "无效的 lecture_id"}

    # 查找 LA 中 is_present = True 的记录
    la_records = list(la_collection.find({
        "lecture_id": lecture_oid,
        "is_present": True
    }))

    user_ids = [r["audience_id"] for r in la_records]

    # 再从用户表中查对应的用户信息
    users = list(user_collection.find({
        "_id": {"$in": user_ids}
    }, {
        "_id": 1,
        "username": 1,
        "email": 1,
        "gender": 1,
        "age": 1,
        "role": 1,
        "avatar": 1
    }))

    # 转换 ObjectId 为字符串
    for u in users:
        u["_id"] = str(u["_id"])

    return {"users": users}


# 更新 is_present
@router.patch("/update_is_present")
def update_is_present(lecture_id: str, audience_id: str, is_present: bool):
    result = la_collection.update_one(
        {
            "lecture_id": ObjectId(lecture_id),
            "audience_id": ObjectId(audience_id)
        },
        {
            "$set": {"is_present": is_present}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="记录未找到")

    return {"message": f"is_present 已更新为 {is_present}"}


class LACreateRequest(BaseModel):
    lecture_id: str  # ObjectId as string
    audience_id: str  # ObjectId as string


@router.post("/create")
async def create_la_entry(data: LACreateRequest):
    try:
        # 检查 ObjectId 是否有效
        if not ObjectId.is_valid(data.lecture_id) or not ObjectId.is_valid(data.audience_id):
            raise HTTPException(status_code=400, detail="无效的 lecture_id 或 audience_id")

        la_doc = {
            "lecture_id": ObjectId(data.lecture_id),
            "audience_id": ObjectId(data.audience_id),
            "is_present": False,
            "joined_at": datetime.utcnow()
        }

        result = la_collection.insert_one(la_doc)

        return {
            "message": "成功加入演讲",
            "la_id": str(result.inserted_id),
            "joined_at": la_doc["joined_at"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")


# def convert_objectid(doc):
#     doc["_id"] = str(doc["_id"])
#     if "lecture_id" in doc:
#         doc["lecture_id"] = str(doc["lecture_id"])
#     return doc
#

@router.get("/lectures_by_user/{user_id}")
async def get_lectures_by_user(user_id: str):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    lectures = list(la_collection.find({"audience_id": oid}))
    # 处理 ObjectId 转字符串
    for l in lectures:
        l["_id"] = str(l["_id"])
        l["lecture_id"] = str(l["lecture_id"])
        l["audience_id"] = str(l["audience_id"])

    return lectures
