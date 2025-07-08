# deepseek_local_model.py
from transformers import pipeline
import re
from datetime import datetime

# 使用正确的模型路径（指向snapshots目录）
MODEL_PATH = "D:/huggingface_cache/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-1.5B/snapshots/ad9f0ae0864d7fbcd1cd905e3c6c5b069cc8b562"


def load_model():
    """加载本地DeepSeek模型"""
    try:
        pipe = pipeline(
            "text-generation",
            model=MODEL_PATH,
            device="cpu",  # 使用CPU（如需GPU改为"cuda"）
            trust_remote_code=True,
            max_length=1024
        )
        print("✅ 本地DeepSeek模型加载成功")
        return pipe
    except Exception as e:
        raise ValueError(f"❌ 模型加载失败: {str(e)}")


pipe = load_model()


def parse_generated_text(text: str):
    """
    解析模型生成的文本，提取问题、选项和答案
    返回格式: {
        "question": str,
        "options": {"A": str, "B": str, "C": str, "D": str},
        "correct_answer": str
    }
    """
    try:
        # 清理输出文本
        text = text.split("</think>")[-1].strip() if "</think>" in text else text

        # 提取关键部分
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) < 7:
            raise ValueError("生成内容格式不符合要求")

        return {
            "question": lines[0].replace("问题:", "").strip(),
            "options": {
                "A": lines[2].replace("A.", "").strip(),
                "B": lines[3].replace("B.", "").strip(),
                "C": lines[4].replace("C.", "").strip(),
                "D": lines[5].replace("D.", "").strip()
            },
            "correct_answer": lines[6].replace("正确答案:", "").strip()
        }
    except Exception as e:
        print(f"⚠️ 解析失败: {e}\n原始文本:\n{text}")
        return None


def generate_questions_local(text: str, num_questions=1):
    """
    使用本地DeepSeek模型生成选择题
    参数:
        text: 输入文本
        num_questions: 生成的问题数量
    返回:
        List[dict] 或空列表（失败时）
    """
    if not text.strip():
        return []

    prompt = f"""你是一位专业出题专家。请根据下列内容生成{num_questions}道单项选择题。

要求：
1. 考察文本核心知识点
2. 四个选项（A-D）有且仅一个正确答案
3. 错误选项要有迷惑性

内容：
{text}

输出格式（必须严格遵循）：
问题: [问题内容]
选项:
A. [选项A]
B. [选项B]
C. [选项C]
D. [选项D]
正确答案: [字母]"""

    try:
        result = pipe(
            prompt,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.7
        )

        generated_text = result[0]['generated_text']
        # print(f"🔄 原始生成内容:\n{generated_text}")  # 调试用

        # 解析生成内容
        questions = []
        parsed = parse_generated_text(generated_text)
        if parsed:
            questions.append(parsed)

        return questions if questions else []

    except Exception as e:
        print(f"❌ 生成问题时出错: {e}")
        return []