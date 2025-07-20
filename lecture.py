#
# from pydantic import BaseModel, root_validator
# from bson import ObjectId
# from datetime import datetime
# from typing import List, Optional
# from fastapi import APIRouter, HTTPException
#
# from db import db  # 假设你有一个db.py文件，其中定义了数据库连接
#
# # 创建路由，改名为 lecture_router
# lecture_router = APIRouter()
# # 获取演讲集合
# lecture_collection = db["lecture"]
#
# # 自定义 ObjectId 序列化器
# class ObjectIdStr(ObjectId):
#     def __str__(self):
#         return str(self)
#
#
# class Lecture(BaseModel):
#     id: Optional[str] = None  # 对应数据库的 _id
#     topic: str  # 演讲主题
#     start_time: datetime  # 演讲开始时间
#     duration: int  # 演讲时长（单位：分钟）
#     description: str = ""  # 演讲简介
#     speaker_id: str  # 演讲者ID 使用str来代替ObjectId
#     organizer_id: str  # 组织者ID 使用str来代替ObjectId
#     status: int  # 演讲状态（例如：1=已安排，2=进行中，3=已结束）
#
#     @root_validator(pre=True)
#     def convert_objectid(cls, values):
#         # 将 _id, speaker_id 和 organizer_id 转换为字符串
#         if "_id" in values and isinstance(values["_id"], ObjectId):
#             values["id"] = str(values["_id"])
#         if "speaker_id" in values and isinstance(values["speaker_id"], ObjectId):
#             values["speaker_id"] = str(values["speaker_id"])
#         if "organizer_id" in values and isinstance(values["organizer_id"], ObjectId):
#             values["organizer_id"] = str(values["organizer_id"])
#         return values
#
#     class Config:
#         json_encoders = {
#             ObjectId: lambda v: str(v)
#         }
#         arbitrary_types_allowed = True
#
#
# # 创建演讲接口
# @lecture_router.post("/create", response_model=Lecture)
# async def create_lecture(lecture: Lecture):
#     # 插入演讲数据到数据库
#     lecture_doc = lecture.dict()
#
#     # 将 speaker_id 和 organizer_id 从字符串转换为 ObjectId
#     lecture_doc["speaker_id"] = ObjectId(lecture_doc["speaker_id"])
#     lecture_doc["organizer_id"] = ObjectId(lecture_doc["organizer_id"])
#
#     result = lecture_collection.insert_one(lecture_doc)
#
#     # 返回创建的演讲信息（包括自动生成的 _id）
#     lecture_doc["id"] = str(result.inserted_id)
#     return lecture_doc
#
#
# @lecture_router.get("/", response_model=List[Lecture])
# async def get_all_lectures():
#     lecturees = lecture_collection.find()
#     result = []
#     for lecture in lecturees:
#         lecture["id"] = str(lecture["_id"])  # 这一行很重要，给前端提供 id
#         lecture["speaker_id"] = str(lecture["speaker_id"])
#         lecture["organizer_id"] = str(lecture["organizer_id"])
#         result.append(Lecture(**lecture))
#     return result
#
#
# # 根据演讲ID获取演讲信息
# @lecture_router.get("/{lecture_id}", response_model=Lecture)
# async def get_lecture(lecture_id: str):
#     # 查找演讲
#     lecture = lecture_collection.find_one({"_id": ObjectId(lecture_id)})
#     if not lecture:
#         raise HTTPException(status_code=404, detail="Lecture not found")
#
#     # 手动将 ObjectId 转为字符串
#     return Lecture(
#         **{**lecture, "speaker_id": str(lecture["speaker_id"]), "organizer_id": str(lecture["organizer_id"])}
#     )
#
#
# # 更新演讲信息
# @lecture_router.put("/{lecture_id}", response_model=Lecture)
# async def update_lecture(lecture_id: str, updated_lecture: Lecture):
#     # 查找并更新演讲
#     updated_lecture_dict = updated_lecture.dict()
#
#     # 将 speaker_id 和 organizer_id 从字符串转换为 ObjectId
#     updated_lecture_dict["speaker_id"] = ObjectId(updated_lecture_dict["speaker_id"])
#     updated_lecture_dict["organizer_id"] = ObjectId(updated_lecture_dict["organizer_id"])
#
#     result = lecture_collection.update_one({"_id": ObjectId(lecture_id)}, {"$set": updated_lecture_dict})
#
#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail="Lecture not found")
#
#     # 返回更新后的演讲
#     updated_lecture_dict["id"] = lecture_id  # 添加 ID 字段
#     return updated_lecture_dict
#
#
# # 删除演讲
# @lecture_router.delete("/{lecture_id}", response_model=str)
# async def delete_lecture(lecture_id: str):
#     # 删除演讲
#     result = lecture_collection.delete_one({"_id": ObjectId(lecture_id)})
#
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Lecture not found")
#
#     return f"Lecture with ID {lecture_id} has been deleted"
#



from pydantic import BaseModel, root_validator
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from db import db  # 假设你有一个db.py文件，其中定义了数据库连接

# 创建路由，改名为 lecture_router
lecture_router = APIRouter()
# 获取演讲集合
lecture_collection = db["lecture"]

# 自定义 ObjectId 序列化器
class ObjectIdStr(ObjectId):
    def __str__(self):
        return str(self)


class Lecture(BaseModel):
    id: Optional[str] = None  # 对应数据库的 _id
    topic: str  # 演讲主题
    start_time: datetime  # 演讲开始时间
    duration: int  # 演讲时长（单位：分钟）
    description: str = ""  # 演讲简介
    speaker_id: Optional[str] = None  # 演讲者ID 允许为空
    organizer_id: Optional[str] = None  # 组织者ID 允许为空
    status: int  # 演讲状态（例如：1=已安排，2=进行中，3=已结束）

    @root_validator(pre=True)
    def convert_objectid(cls, values):
        if "_id" in values and isinstance(values["_id"], ObjectId):
            values["id"] = str(values["_id"])
        if "speaker_id" in values and isinstance(values["speaker_id"], ObjectId):
            values["speaker_id"] = str(values["speaker_id"])
        if "organizer_id" in values and isinstance(values["organizer_id"], ObjectId):
            values["organizer_id"] = str(values["organizer_id"])
        return values

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)
        }
        arbitrary_types_allowed = True


# 创建演讲接口
@lecture_router.post("/create", response_model=Lecture)
async def create_lecture(lecture: Lecture):
    lecture_doc = lecture.dict()

    if lecture_doc.get("speaker_id"):
        lecture_doc["speaker_id"] = ObjectId(lecture_doc["speaker_id"])
    if lecture_doc.get("organizer_id"):
        lecture_doc["organizer_id"] = ObjectId(lecture_doc["organizer_id"])

    result = lecture_collection.insert_one(lecture_doc)
    lecture_doc["id"] = str(result.inserted_id)
    return lecture_doc


@lecture_router.get("/", response_model=List[Lecture])
async def get_all_lectures():
    lecturees = lecture_collection.find()
    result = []
    for lecture in lecturees:
        lecture["id"] = str(lecture["_id"])
        if "speaker_id" in lecture:
            lecture["speaker_id"] = str(lecture["speaker_id"])
        if "organizer_id" in lecture:
            lecture["organizer_id"] = str(lecture["organizer_id"])
        result.append(Lecture(**lecture))
    return result


@lecture_router.get("/{lecture_id}", response_model=Lecture)
async def get_lecture(lecture_id: str):
    lecture = lecture_collection.find_one({"_id": ObjectId(lecture_id)})
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    if "speaker_id" in lecture:
        lecture["speaker_id"] = str(lecture["speaker_id"])
    if "organizer_id" in lecture:
        lecture["organizer_id"] = str(lecture["organizer_id"])

    return Lecture(**lecture)


@lecture_router.put("/{lecture_id}", response_model=Lecture)
async def update_lecture(lecture_id: str, updated_lecture: Lecture):
    updated_lecture_dict = updated_lecture.dict()

    if updated_lecture_dict.get("speaker_id"):
        updated_lecture_dict["speaker_id"] = ObjectId(updated_lecture_dict["speaker_id"])
    if updated_lecture_dict.get("organizer_id"):
        updated_lecture_dict["organizer_id"] = ObjectId(updated_lecture_dict["organizer_id"])

    result = lecture_collection.update_one({"_id": ObjectId(lecture_id)}, {"$set": updated_lecture_dict})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lecture not found")

    updated_lecture_dict["id"] = lecture_id
    return updated_lecture_dict


@lecture_router.delete("/{lecture_id}", response_model=str)
async def delete_lecture(lecture_id: str):
    result = lecture_collection.delete_one({"_id": ObjectId(lecture_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lecture not found")

    return f"Lecture with ID {lecture_id} has been deleted"