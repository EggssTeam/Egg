# MongoDB 配置
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["mydb"]
collection = db["qa_collection"]
user_collection = db["user"]
lecture_collection = db["lecture"]
invitation_collection = db["invitation"]