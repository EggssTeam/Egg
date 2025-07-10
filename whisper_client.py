import requests
from datetime import datetime

WHISPER_API_URL = "https://api.gpt.ge/v1/audio/transcriptions"
OPENAI_API_KEY = "sk-RxDy2FlSA3PP89erC8257937AfE9482cBe6400E14d16E692"

def generate_questions(text: str):
    """
    调用 DeepSeek API 根据输入文本生成一个选择题，
    并返回结构化的选择题数据。
    """
    prompt = f"""
请根据以下文本生成 **1 个选择题**，每个问题包含 **4 个选项（ABCD）**，并标注正确答案。格式如下：

问题: ...
A) ...
B) ...
C) ...
D) ...
正确答案: 只给出字母

文本内容:
{text}
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个擅长出选择题的AI助手，问题清晰，选项合理。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    response_data = response.json()

    if "choices" in response_data and response_data["choices"]:
        qa_text = response_data["choices"][0]["message"]["content"]
        lines = qa_text.strip().splitlines()

        if len(lines) < 6:
            return []

        question = lines[0].strip().replace("问题:", "").strip()
        options = {
            "A": lines[1].strip()[3:],
            "B": lines[2].strip()[3:],
            "C": lines[3].strip()[3:],
            "D": lines[4].strip()[3:]
        }
        correct_answer = lines[5].strip().split(":")[1].strip()

        return [{
            "question": question,
            "options": options,
            "correct_answer": correct_answer
        }]
    else:
        return []
