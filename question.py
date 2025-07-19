from fastapi import HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, root_validator
from typing import Dict
from bson import ObjectId

from db import collection  # collection = db["qa_collection"]

question_router = APIRouter()


# 问题数据模型
class QaCollection(BaseModel):
    lecture_id: str
    question: str
    options: Dict[str, str]
    correct_answer: str

    @root_validator(pre=True)
    def convert_objectid(cls, values):
        if "lecture_id" in values and isinstance(values["lecture_id"], ObjectId):
            values["lecture_id"] = str(values["lecture_id"])
        return values

    class Config:
        json_encoders = {
            ObjectId: str
        }
        arbitrary_types_allowed = True


# 1. 获取所有问题（返回 Python list）
@question_router.get("/")
async def get_questions():
    try:
        questions = list(collection.find())
        formatted = [
            {
                "id": str(q["_id"]),
                "lecture_id": q.get("lecture_id", "无"),
                "question": q.get("question", "未提供问题"),
                "options": q.get("options", {}),
                "correct_answer": q.get("correct_answer", "未提供答案")
            }
            for q in questions
        ]
        return formatted
    except Exception as e:
        return [{"error": str(e)}]



@question_router.get("/uptodata")
async def get_latest_question():
    try:
        # 获取最新问题
        question_data = collection.find_one({}, sort=[('_id', -1)])
        if question_data:
            # 手动构造返回格式，确保 lecture_id 被转换为 str
            formatted = {
                "id": str(question_data["_id"]),
                "lecture_id": str(question_data.get("lecture_id", "")),
                "question": question_data.get("question", "未提供问题"),
                "options": question_data.get("options", {}),
                "correct_answer": question_data.get("correct_answer", "未提供答案")
            }
            return formatted
        else:
            return {"error": "没有问题数据"}
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}




# 2. 获取单条问题（通过 question 的 _id）
@question_router.get("/{id}")
async def get_question_by_id(id: str):
    try:
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ObjectId")

        question = collection.find_one({"_id": ObjectId(id)})
        if question:
            question["id"] = str(question["_id"])
            question.pop("_id", None)
            return question
        else:
            raise HTTPException(status_code=404, detail="Question not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 3. 更新问题（通过 question 的 _id）
class QuestionUpdate(BaseModel):
    question: str
    options: Dict[str, str]
    correct_answer: str


@question_router.put("/{id}")
async def update_question(id: str, q: QuestionUpdate):
    try:
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ObjectId")

        result = collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer
            }}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Question not found")

        return {"message": "Question updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# 4. 删除问题（通过 question 的 _id）
@question_router.delete("/{id}")
async def delete_question(id: str):
    try:
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ObjectId")

        result = collection.delete_one({"_id": ObjectId(id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Question not found")

        return {"message": "Question deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

