from pydantic import BaseModel, Field, validator
from bson import ObjectId
from typing import Optional
from fastapi import APIRouter, HTTPException
from db import db, invitation_collection, lecture_collection  # 假设你有一个db.py文件，其中定义了数据库连接
from datetime import datetime


from fastapi import Query

# 创建路由
invitation_router = APIRouter()


# 自定义 ObjectId 序列化器
class ObjectIdStr(ObjectId):
    def __str__(self):
        return str(self)


# 输入模型（用于创建/更新）
class InvitationCreate(BaseModel):
    lecture_id: str = Field(..., description="关联的演讲ID（字符串格式）")
    speaker_id: str = Field(..., description="受邀的演讲者ID（字符串格式）")
    status: int = Field(1, description="状态：0=pending, 1=accepted, -1=declined")

    @validator('status')
    def validate_status(cls, v):
        if v not in {1, -1, 0}:
            raise ValueError("Status must be 1, -1, or 0")
        return v


# 输出模型（包含自动生成的id）
class InvitationResponse(InvitationCreate):
    id: str = Field(..., description="自动生成的邀请ID")

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)
        }


# 创建邀请（不需要前端传递id）
@invitation_router.post("/create", response_model=InvitationResponse)
async def create_invitation(invitation: InvitationCreate):
    try:
        # 转换字符串ID为ObjectId（如果格式非法会抛出异常）
        lecture_id = ObjectId(invitation.lecture_id)
        speaker_id = ObjectId(invitation.speaker_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid lecture_id or speaker_id format")

    # 构建插入文档（_id由MongoDB自动生成）
    invitation_doc = {
        "lecture_id": lecture_id,
        "speaker_id": speaker_id,
        "status": invitation.status
    }

    # 插入数据库
    result = invitation_collection.insert_one(invitation_doc)

    # 返回包含新_id的完整数据
    return {
        "id": str(result.inserted_id),
        "lecture_id": invitation.lecture_id,
        "speaker_id": invitation.speaker_id,
        "status": invitation.status
    }


# 获取所有邀请
@invitation_router.get("/", response_model=list[InvitationResponse])
async def get_all_invitations():
    invitations = invitation_collection.find()
    return [
        InvitationResponse(
            id=str(invite["_id"]),
            lecture_id=str(invite["lecture_id"]),
            speaker_id=str(invite["speaker_id"]),
            status=invite["status"]
        )
        for invite in invitations
    ]


# 根据ID获取单个邀请
@invitation_router.get("/{invitation_id}", response_model=InvitationResponse)
async def get_invitation(invitation_id: str):
    try:
        invite = invitation_collection.find_one({"_id": ObjectId(invitation_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid invitation_id format")

    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")

    return InvitationResponse(
        id=str(invite["_id"]),
        lecture_id=str(invite["lecture_id"]),
        speaker_id=str(invite["speaker_id"]),
        status=invite["status"]
    )


# 更新邀请状态
@invitation_router.put("/{invitation_id}", response_model=InvitationResponse)
async def update_invitation(invitation_id: str, updated_invite: InvitationCreate):
    try:
        # 验证ID格式
        obj_id = ObjectId(invitation_id)
        lecture_id = ObjectId(updated_invite.lecture_id)
        speaker_id = ObjectId(updated_invite.speaker_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # 构建更新数据
    update_data = {
        "lecture_id": lecture_id,
        "speaker_id": speaker_id,
        "status": updated_invite.status
    }

    result = invitation_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found")

    return InvitationResponse(
        id=invitation_id,
        lecture_id=updated_invite.lecture_id,
        speaker_id=updated_invite.speaker_id,
        status=updated_invite.status
    )


# 删除邀请
@invitation_router.delete("/{invitation_id}", response_model=dict)
async def delete_invitation(invitation_id: str):
    try:
        result = invitation_collection.delete_one({"_id": ObjectId(invitation_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid invitation_id format")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found")

    return {"message": f"Invitation {invitation_id} deleted successfully"}



@invitation_router.get("/byspeaker/{speaker_id}", response_model=list[InvitationResponse])
async def get_invitations_by_speaker(speaker_id: str):
    try:
        speaker_obj_id = ObjectId(speaker_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid speaker_id format")

    invitations = invitation_collection.find({"speaker_id": speaker_obj_id})
    return [
        InvitationResponse(
            id=str(invite["_id"]),
            lecture_id=str(invite["lecture_id"]),
            speaker_id=str(invite["speaker_id"]),
            status=invite["status"]
        )
        for invite in invitations
    ]

# 更新 invitation 状态，并把 speaker_id 写入 lecture 表中
@invitation_router.put("/accept/{invitation_id}", response_model=InvitationResponse)
async def accept_invitation(invitation_id: str):
    try:
        obj_id = ObjectId(invitation_id)
        invite = invitation_collection.find_one({"_id": obj_id})
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid invitation ID")

    # 更新 invitation 状态为 1（接受）
    invitation_collection.update_one(
        {"_id": obj_id},
        {"$set": {"status": 1}}
    )

    # 同步更新 lecture 中的 speaker_id
    lecture_collection.update_one(
        {"_id": invite["lecture_id"]},
        {"$set": {"speaker_id": invite["speaker_id"]}}
    )

    # # 加入LA中
    # db["LA"].insert_one({
    #     "lecture_id": invite["lecture_id"],
    #     "audience_id": invite["speaker_id"],
    #     "is_present": False,
    #     "joined_at": datetime.utcnow()
    # })

    return InvitationResponse(
        id=str(invite["_id"]),
        lecture_id=str(invite["lecture_id"]),
        speaker_id=str(invite["speaker_id"]),
        status=1
    )
