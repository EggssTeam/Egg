#
# from fastapi import HTTPException, status, APIRouter
# from pydantic import BaseModel, EmailStr, validator
# from passlib.context import CryptContext
#
# import re
# from db import user_collection
# # from main import app
#
# # from main import user_collection, app
#
# user_router = APIRouter()
#
#
# # 密码加密上下文
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#
#
# # Pydantic模型：用于注册请求体的验证
# class UserCreate(BaseModel):
#     username: str
#     email: EmailStr  # 本地格式验证
#     password: str
#     role: int  # 添加角色属性，类型为int
#     gender: int  # 性别属性，0为男，1为女
#     age: int  # 年龄
#     avatar: str  # 头像路径或URL
#     motto: str
#
#     # 使用@validator装饰器进行邮箱格式验证
#     @validator("email")
#     def validate_email_format(cls, v):
#         # 正则表达式来验证邮箱格式
#         email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
#         if not re.match(email_regex, v):
#             raise ValueError("Invalid email format")
#         return v
#
#
# # 加密密码
# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)
#
#
# # 验证密码
# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)
#
#
# # 注册接口：用户注册并存储到MongoDB
# @user_router.post("/register")
# async def register(user: UserCreate):
#     # 检查用户名是否已存在
#     if user_collection.find_one({"username": user.username}):
#         raise HTTPException(status_code=400, detail="Username already taken")
#
#     # 检查电子邮件是否已注册
#     if user_collection.find_one({"email": user.email}):
#         raise HTTPException(status_code=400, detail="Email already registered")
#
#     # 哈希加密用户密码
#     hashed_password = hash_password(user.password)
#
#     # 创建用户文档
#     user_doc = {
#         "username": user.username,
#         "email": user.email,
#         "password": hashed_password,
#         "role": user.role,  # 存储角色信息
#         "gender": user.gender,  # 存储性别
#         "age": user.age,  # 存储年龄
#         "avatar": user.avatar,  # 存储头像路径或URL
#         "motto": user.motto
#     }
#
#     # 插入到MongoDB
#     user_collection.insert_one(user_doc)
#
#     return {"message": "User successfully created", "username": user.username}
#
# # Pydantic模型：用于登录请求体的验证
# class UserLogin(BaseModel):
#     email: EmailStr  # 使用邮箱而不是用户名
#     password: str
#
# # 登录接口：验证邮箱和密码
# @user_router.post("/login")
# async def login(user: UserLogin):
#     # 查询数据库查找该邮箱的用户
#     db_user = user_collection.find_one({"email": user.email})
#
#     if db_user is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid credentials"
#         )
#
#     # 验证密码是否匹配
#     if not verify_password(user.password, db_user["password"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid credentials"
#         )
#
#     return {"message": "Login successful", "email": user.email}
from uuid import uuid4

from fastapi import HTTPException, status, APIRouter, Body, Form
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from typing import Optional
import re
from db import user_collection  # 假设你已经正确连接 MongoDB
from fastapi import UploadFile, File, HTTPException
import shutil
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

user_router = APIRouter()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic模型：用于注册请求体的验证（简化）
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: int

    @validator("email")
    def validate_email_format(cls, v):
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v


# # Pydantic模型：用于修改信息的请求体（可选字段）
# class UserUpdate(BaseModel):
#     gender: Optional[int]
#     age: Optional[int]
#     avatar: Optional[str]
#     motto: Optional[str]


# 加密密码
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 注册接口：仅填写基本信息
@user_router.post("/register")
async def register(user: UserCreate):
    if user_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")

    if user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)

    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": user.role,
        # 其余字段默认不填，待后续补充
    }

    user_collection.insert_one(user_doc)
    return {"message": "User successfully created", "username": user.username}


# 登录模型
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# 登录接口
@user_router.post("/login")
async def login(user: UserLogin):
    db_user = user_collection.find_one({"email": user.email})
    if db_user is None or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return {"message": "Login successful", "email": user.email}

#
# # 修改用户信息接口（根据邮箱定位用户）
# @user_router.put("/update/{email}")
# async def update_user(email: str, update_data: UserUpdate):
#     db_user = user_collection.find_one({"email": email})
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
#     if not update_dict:
#         raise HTTPException(status_code=400, detail="No valid fields to update")
#
#     user_collection.update_one({"email": email}, {"$set": update_dict})
#
#     return {"message": "User info updated", "updated_fields": list(update_dict.keys())}


#
# from fastapi import APIRouter, HTTPException, Body
# from pydantic import BaseModel, EmailStr, validator
# from typing import Optional
# import re
#
# user_router = APIRouter()

class UserUpdate(BaseModel):
    username: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    avatar: Optional[str] = None
    motto: Optional[str] = None
    background: Optional[str] = None

    @validator("username")
    def username_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("用户名不能为空")
        return v

@user_router.get("/{email}")
async def get_user(email: str):
    user = user_collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#
#
# @user_router.put("/update/{email}")
# async def update_user(email: str, update_data: UserUpdate = Body(...)):
#     db_user = user_collection.find_one({"email": email})
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
#     if not update_dict:
#         raise HTTPException(status_code=400, detail="No valid fields to update")
#
#     # 校验用户名唯一性
#     if "username" in update_dict:
#         new_username = update_dict["username"]
#         if new_username != db_user.get("username"):
#             exists = user_collection.find_one({"username": new_username})
#             if exists:
#                 raise HTTPException(status_code=400, detail="用户名已被使用")
#
#     # 执行更新
#     user_collection.update_one({"email": email}, {"$set": update_dict})
#
#     return {"message": "User info updated", "updated_fields": list(update_dict.keys())}



UPLOAD_DIR = "static/uploads"  # 你存图片的目录

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# UPLOAD_FOLDER = "static/uploads"  # 本地保存头像的目录
#
# @user_router.put("/update/{email}")
# async def update_user_with_avatar(
#     email: str,
#     username: str = Form(None),
#     gender: int = Form(None),
#     age: int = Form(None),
#     motto: str = Form(None),
#     avatar: UploadFile = File(None),
# ):
#     # 查找用户
#     db_user = user_collection.find_one({"email": email})
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     update_data = {}
#
#     if username:
#         if username != db_user.get("username"):
#             if user_collection.find_one({"username": username}):
#                 raise HTTPException(status_code=400, detail="用户名已被使用")
#         update_data["username"] = username
#
#     if gender is not None:
#         update_data["gender"] = gender
#
#     if age is not None:
#         update_data["age"] = age
#
#     if motto:
#         update_data["motto"] = motto
#
#     # 处理头像上传
#     if avatar:
#         ext = os.path.splitext(avatar.filename)[1]  # e.g. .jpg
#         filename = f"{uuid4().hex}{ext}"
#         filepath = os.path.join(UPLOAD_DIR, filename)
#         os.makedirs(UPLOAD_DIR, exist_ok=True)  # 确保文件夹存在
#
#         with open(filepath, "wb") as f:
#             f.write(await avatar.read())
#
#         # 存储相对路径
#         update_data["avatar"] = f"/static/uploads/{filename}"
#
#     if not update_data:
#         raise HTTPException(status_code=400, detail="No valid fields to update")
#
#     # 执行更新
#     user_collection.update_one({"email": email}, {"$set": update_data})
#
#     return {"message": "User info updated", "updated_fields": list(update_data.keys())}

@user_router.put("/update/{email}")
async def update_user_with_files(
    email: str,
    username: Optional[str] = Form(None),
    gender: Optional[int] = Form(None),
    age: Optional[int] = Form(None),
    motto: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    background: Optional[UploadFile] = File(None),
):
    # 查找用户
    db_user = user_collection.find_one({"email": email})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {}

    # 校验并更新用户名
    if username:
        if username != db_user.get("username"):
            if user_collection.find_one({"username": username}):
                raise HTTPException(status_code=400, detail="用户名已被使用")
        update_data["username"] = username

    if gender is not None:
        update_data["gender"] = gender

    if age is not None:
        update_data["age"] = age

    if motto:
        update_data["motto"] = motto

    # 上传头像
    if avatar:
        ext = os.path.splitext(avatar.filename)[1]
        avatar_filename = f"{uuid4().hex}{ext}"
        avatar_path = os.path.join(UPLOAD_DIR, avatar_filename)
        with open(avatar_path, "wb") as f:
            f.write(await avatar.read())
        update_data["avatar"] = f"/static/uploads/{avatar_filename}"

    # 上传背景图
    if background:
        ext = os.path.splitext(background.filename)[1]
        background_filename = f"{uuid4().hex}{ext}"
        background_path = os.path.join(UPLOAD_DIR, background_filename)
        with open(background_path, "wb") as f:
            f.write(await background.read())
        update_data["background"] = f"/static/uploads/{background_filename}"

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # 执行数据库更新
    user_collection.update_one({"email": email}, {"$set": update_data})

    return {
        "message": "User info updated",
        "updated_fields": list(update_data.keys()),
        "paths": {
            "avatar": update_data.get("avatar"),
            "background": update_data.get("background")
        }
    }