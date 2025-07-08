# import pymongo
# from fastapi import FastAPI, HTTPException
# from pymongo import MongoClient, ASCENDING, DESCENDING
# from pydantic import BaseModel
# from typing import List
#
# # 创建 FastAPI 应用实例
# app = FastAPI()
#
# # 连接 MongoDB
# client = MongoClient("mongodb://localhost:27017/")
# db = client["uDatabase"]
# collection = db["uCollection"]
#
# # 定义数据模型
# class Person(BaseModel):
#     name: str
#     age: int
#
# # 插入单条数据
# @app.post("/add", response_model=Person)
# async def add_person(person: Person):
#     # 插入数据到 MongoDB
#     collection.insert_one(person.dict())
#     return person
#
# # 插入多条数据
# @app.post("/add_multiple")
# async def add_multiple_people(people: List[Person]):
#     people_dict = [person.dict() for person in people]
#     collection.insert_many(people_dict)
#     return {"message": "Multiple people added successfully"}
#
# # 查询单条数据
# @app.get("/get/{name}", response_model=Person)
# async def get_person(name: str):
#     # 查询数据
#     person = collection.find_one({"name": name})
#     if person:
#         return Person(**person)
#     else:
#         raise HTTPException(status_code=404, detail="Person not found")
#
# # 查询所有数据
# @app.get("/get_all", response_model=List[Person])
# async def get_all_people():
#     # 查询所有数据
#     people = collection.find()
#     result = [Person(**person) for person in people]
#     return result
#
# # 查找年龄大于 25 的人
# @app.get("/get_older_than_25", response_model=List[Person])
# async def get_older_than_25():
#     older_than_25 = collection.find({"age": { "$gt": 25 }})
#     #gt,lt,gte,lte,eq,ne,in,nin
#     result = [Person(**person) for person in older_than_25]
#     return result
#         # 使用 motor 后，查询将变成异步操作，能够更好地支持高并发请求
#         # from motor.motor_asyncio import AsyncIOMotorClient
#         # # 连接 MongoDB (使用 motor 异步客户端)
#         # client = AsyncIOMotorClient("mongodb://localhost:27017/")
#         # # 异步获取年龄大于25的数据
#         # @app.get("/get_older_than_25", response_model=List[Person])
#         # async def get_older_than_25():
#         #     # 异步查询 MongoDB 数据
#         #     cursor = collection.find({"age": {"$gt": 25}})
#         #     result = []
#         #
#         #     async for person in cursor:  # 异步遍历游标
#         #         result.append(Person(**person))
#         #
#         #     return result
#
# # 更新数据
# @app.put("/update/{name}", response_model=Person)
# async def update_person(name: str, person: Person):
#     result = collection.update_one(
#         {"name": name},
#         {"$set": person.dict()}
#     )
#     if result.modified_count == 0:
#         raise HTTPException(status_code=404, detail="Person not found")
#     return person
#
# # 删除数据
# @app.delete("/delete/{name}")
# async def delete_person(name: str):
#     result = collection.delete_one({"name": name})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Person not found")
#     return {"message": f"Person {name} deleted successfully"}
#
# # 排序查询 - 按年龄降序排序，返回前 2 条数据
# @app.get("/get_sorted")
# async def get_sorted():
#     sorted_people = collection.find().sort("age", DESCENDING).limit(2)
#     result = [Person(**person) for person in sorted_people]
#     return result
#
# # 创建单字段索引
# @app.post("/create_index")
# async def create_index():
#     collection.create_index([("name", ASCENDING)])  # 按 name 字段升序创建索引
#     return {"message": "Index created on 'name' field"}
#
# # 聚合操作 - 统计每个名字的平均年龄
# @app.get("/aggregate")
# async def aggregate_avg_age():
#     pipeline = [
#         {"$group": {"_id": "$name", "avg_age": {"$avg": "$age"}}}
#     ]
#     result = collection.aggregate(pipeline)
#     return [{"name": doc["_id"], "avg_age": doc["avg_age"]} for doc in result]
#
# # 创建新集合
# @app.post("/create_collection")
# async def create_collection():
#     new_collection = db["newCollection"]
#     return {"message": "New collection created: newCollection"}
#
# # 删除集合
# @app.delete("/drop_collection")
# async def drop_collection():
#     db.drop_collection("newCollection")
#     return {"message": "Collection 'newCollection' dropped"}
#
# # 删除数据库
# @app.delete("/drop_database")
# async def drop_database():
#     client.drop_database("myDatabase")
#     return {"message": "Database 'myDatabase' dropped"}
#
# # 异常处理 - 连接失败或操作失败
# @app.post("/insert_with_error_handling")
# async def insert_with_error_handling(person: Person):
#     try:
#         # 可能会引发异常的 MongoDB 操作
#         collection.insert_one(person.dict())
#         return {"status": "success"}
#     except pymongo.errors.ConnectionError as e:
#         return {"error": "连接失败", "details": str(e)}
#     except pymongo.errors.OperationFailure as e:
#         return {"error": "操作失败", "details": str(e)}
#
# # 运行 FastAPI 应用（通常通过 uvicorn 启动）
