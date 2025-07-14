
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext

import re
from db import user_collection
# from main import app

# from main import user_collection, app

user_router = APIRouter()


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic模型：用于注册请求体的验证
class UserCreate(BaseModel):
    username: str
    email: EmailStr  # 本地格式验证
    password: str
    role: int  # 添加角色属性，类型为int

    # 使用@validator装饰器进行邮箱格式验证
    @validator("email")
    def validate_email_format(cls, v):
        # 正则表达式来验证邮箱格式
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v

# 加密密码
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 注册接口：用户注册并存储到MongoDB
@user_router.post("/register")
async def register(user: UserCreate):
    # 检查用户名是否已存在
    if user_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken")

    # 检查电子邮件是否已注册
    if user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # 哈希加密用户密码
    hashed_password = hash_password(user.password)

    # 创建用户文档
    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": user.role  # 存储角色信息
    }

    # 插入到MongoDB
    user_collection.insert_one(user_doc)

    return {"message": "User successfully created", "username": user.username}


# Pydantic模型：用于登录请求体的验证
class UserLogin(BaseModel):
    email: EmailStr  # 使用邮箱而不是用户名
    password: str

# 登录接口：验证邮箱和密码
@user_router.post("/login")
async def login(user: UserLogin):
    # 查询数据库查找该邮箱的用户
    db_user = user_collection.find_one({"email": user.email})

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 验证密码是否匹配
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return {"message": "Login successful", "email": user.email}
