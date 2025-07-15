# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from datetime import datetime
# from bson import ObjectId
# from db import db  # 假设你有一个db.py文件，其中定义了数据库连接
#
# # 创建路由，改名为 lecture_router
# lecture_router = APIRouter()
#
#
# # 定义演讲类
# class Lecture(BaseModel):
#     topic: str  # 演讲主题
#     start_time: datetime  # 演讲开始时间
#     duration: int  # 演讲时长（单位：分钟）
#     description: str = ""  # 演讲简介
#     speaker_id: str  # 演讲者ID 使用str来代替ObjectId
#     organizer_id: str  # 组织者ID 使用str来代替ObjectId
#     status: int  # 演讲状态（例如：1=已安排，2=进行中，3=已结束）
#
#     # class Config:
#     #     # 设置模型可以从数据库文档（dict）创建
#     #     json_encoders = {
#     #         ObjectId: str  # 将ObjectId转为字符串进行输出
#     #     }
#     #     arbitrary_types_allowed = True  # 允许使用任意类型（如ObjectId）
#
#
# # 获取演讲集合
# lecture_collection = db["lecture"]
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
# # 获取所有演讲列表
# @lecture_router.get("/", response_model=list[Lecture])
# async def get_all_lecturees():
#     lecturees = lecture_collection.find()
#     return [Lecture(**lecture) for lecture in lecturees]
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
#     # 返回演讲
#     return Lecture(**lecture)
#
#
# # 更新演讲信息
# @lecture_router.put("/{lecture_id}", response_model=Lecture)
# async def update_lecture(lecture_id: str, updated_lecture: Lecture):
#     # 查找并更新演讲
#     result = lecture_collection.update_one({"_id": ObjectId(lecture_id)}, {"$set": updated_lecture.dict()})
#
#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail="Lecture not found")
#
#     # 返回更新后的演讲
#     updated_lecture_dict = updated_lecture.dict()
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
import bson

from pydantic import BaseModel, root_validator
from bson import ObjectId
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from db import db  # 假设你有一个db.py文件，其中定义了数据库连接

# 创建路由，改名为 lecture_router
lecture_router = APIRouter()

# 自定义 ObjectId 序列化器
class ObjectIdStr(ObjectId):
    def __str__(self):
        return str(self)

# 定义演讲类
class Lecture(BaseModel):
    topic: str  # 演讲主题
    start_time: datetime  # 演讲开始时间
    duration: int  # 演讲时长（单位：分钟）
    description: str = ""  # 演讲简介
    speaker_id: str  # 演讲者ID 使用str来代替ObjectId
    organizer_id: str  # 组织者ID 使用str来代替ObjectId
    status: int  # 演讲状态（例如：1=已安排，2=进行中，3=已结束）

    @root_validator(pre=True)
    def convert_objectid(cls, values):
        # 将 speaker_id 和 organizer_id 转换为 str 类型
        if "speaker_id" in values and isinstance(values["speaker_id"], ObjectId):
            values["speaker_id"] = str(values["speaker_id"])
        if "organizer_id" in values and isinstance(values["organizer_id"], ObjectId):
            values["organizer_id"] = str(values["organizer_id"])
        return values

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)  # 将 ObjectId 转为字符串进行输出
        }
        arbitrary_types_allowed = True  # 允许使用任意类型（如 ObjectId）

# 获取演讲集合
lecture_collection = db["lecture"]

# 创建演讲接口
@lecture_router.post("/create", response_model=Lecture)
async def create_lecture(lecture: Lecture):
    # 插入演讲数据到数据库
    lecture_doc = lecture.dict()

    # 将 speaker_id 和 organizer_id 从字符串转换为 ObjectId
    lecture_doc["speaker_id"] = ObjectId(lecture_doc["speaker_id"])
    lecture_doc["organizer_id"] = ObjectId(lecture_doc["organizer_id"])

    result = lecture_collection.insert_one(lecture_doc)

    # 返回创建的演讲信息（包括自动生成的 _id）
    lecture_doc["id"] = str(result.inserted_id)
    return lecture_doc


# 获取所有演讲列表
@lecture_router.get("/", response_model=List[Lecture])
async def get_all_lectures():
    lecturees = lecture_collection.find()
    # 手动将 ObjectId 转为字符串
    return [Lecture(
        **{**lecture, "speaker_id": str(lecture["speaker_id"]), "organizer_id": str(lecture["organizer_id"])}
    ) for lecture in lecturees]


# 根据演讲ID获取演讲信息
@lecture_router.get("/{lecture_id}", response_model=Lecture)
async def get_lecture(lecture_id: str):
    # 查找演讲
    lecture = lecture_collection.find_one({"_id": ObjectId(lecture_id)})
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    # 手动将 ObjectId 转为字符串
    return Lecture(
        **{**lecture, "speaker_id": str(lecture["speaker_id"]), "organizer_id": str(lecture["organizer_id"])}
    )


# 更新演讲信息
@lecture_router.put("/{lecture_id}", response_model=Lecture)
async def update_lecture(lecture_id: str, updated_lecture: Lecture):
    # 查找并更新演讲
    updated_lecture_dict = updated_lecture.dict()

    # 将 speaker_id 和 organizer_id 从字符串转换为 ObjectId
    updated_lecture_dict["speaker_id"] = ObjectId(updated_lecture_dict["speaker_id"])
    updated_lecture_dict["organizer_id"] = ObjectId(updated_lecture_dict["organizer_id"])

    result = lecture_collection.update_one({"_id": ObjectId(lecture_id)}, {"$set": updated_lecture_dict})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lecture not found")

    # 返回更新后的演讲
    updated_lecture_dict["id"] = lecture_id  # 添加 ID 字段
    return updated_lecture_dict


# 删除演讲
@lecture_router.delete("/{lecture_id}", response_model=str)
async def delete_lecture(lecture_id: str):
    # 删除演讲
    result = lecture_collection.delete_one({"_id": ObjectId(lecture_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lecture not found")

    return f"Lecture with ID {lecture_id} has been deleted"
