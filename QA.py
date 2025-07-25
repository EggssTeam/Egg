from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from db import db

qa_collection = db["qa"]
q_collection = db["question"]

router = APIRouter()

# Pydantic 请求模型
class SubmitAnswersRequest(BaseModel):
    user_id: str
    question_ids: List[str]
    selected_options: List[Optional[str]]  # 支持 null 值

@router.post("/submit")
def submit_answers(req: SubmitAnswersRequest):
    if len(req.question_ids) != len(req.selected_options):
        raise HTTPException(status_code=400, detail="题目数量与选项数量不匹配")

    user_oid = ObjectId(req.user_id)
    question_oids = [ObjectId(qid) for qid in req.question_ids]

    # 获取 correct_answer
    correct_answers = {
        str(q["_id"]): q["correct_answer"]
        for q in q_collection.find({"_id": {"$in": question_oids}}, {"correct_answer": 1})
    }

    records = []
    for i in range(len(req.question_ids)):
        qid_str = req.question_ids[i]
        selected = req.selected_options[i]
        correct = correct_answers.get(qid_str)

        if correct is None:
            continue  # 防止意外问题 ID

        record = {
            "question_id": ObjectId(qid_str),
            "user_id": user_oid,
            "selected_option": selected if selected else None,
            "is_correct": selected == correct if selected else False ,
            "answered_at": datetime.utcnow()
        }
        records.append(record)

    if records:
        qa_collection.insert_many(records)

    return {"message": f"{len(records)} 条回答已记录"}

# @router.get("/lecture/{lecture_id}/accuracy")
# def get_question_accuracy(lecture_id: str):
#     lecture_oid = ObjectId(lecture_id)
#
#     # 获取该 lecture 下所有已发送题目的 ID
#     questions = list(q_collection.find({
#         "lecture_id": lecture_oid,
#         "is_send": True
#     }, {"_id": 1, "question": 1}))
#
#     results = []
#
#     for q in questions:
#         qid = q["_id"]
#         total = qa_collection.count_documents({"question_id": qid})
#         correct = qa_collection.count_documents({"question_id": qid, "is_correct": True})
#
#         results.append({
#             "question_id": str(qid),
#             "question": q["question"],
#             "correct": correct,
#             "total": total,
#             "accuracy": round(correct / total, 2) if total else None
#         })
#
#     return {"accuracy_report": results}

@router.get("/lecture/{lecture_id}/question_report")
def get_question_report(lecture_id: str):
    lecture_oid = ObjectId(lecture_id)

    # 获取已发送的题目
    questions = list(q_collection.find({
        "lecture_id": lecture_oid,
        "is_send": True
    }))

    report = []

    for q in questions:
        qid = q["_id"]
        options = q["options"]
        correct_answer = q["correct_answer"]

        # 获取所有对这个题作答的记录
        answers = list(qa_collection.find({"question_id": qid}))
        total = len(answers)
        correct = sum(1 for a in answers if a["is_correct"])

        # 初始化每个选项的统计次数
        option_stats = {key: 0 for key in options.keys()}
        for a in answers:
            selected = a.get("selected_option")
            if selected in option_stats:
                option_stats[selected] += 1

        report.append({
            "question_id": str(qid),
            "question": q["question"],
            "options": options,
            "correct_answer": correct_answer,
            "option_counts": option_stats,
            "correct": correct,
            "total": total,
            "accuracy": round(correct / total, 2) if total else None
        })

    return {"question_report": report}

@router.get("/user_answers")
def get_user_answers(lecture_id: str, user_id: str):
    lecture_oid = ObjectId(lecture_id)
    user_oid = ObjectId(user_id)

    # 获取该演讲下所有已发送的题目
    questions = list(q_collection.find({
        "lecture_id": lecture_oid,
        "is_send": True
    }, {"_id": 1, "question": 1}))

    results = []

    for q in questions:
        qid = q["_id"]
        qa_record = qa_collection.find_one({
            "question_id": qid,
            "user_id": user_oid
        })

        selected_option = qa_record["selected_option"] if qa_record else None

        # results.append({
        #     "question_id": str(qid),
        #     "selected_option": selected_option
        # })
        results.append({str(qid): selected_option})

    return {"answers": results}