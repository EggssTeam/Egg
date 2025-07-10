import os
import requests
import re  # 用于正则表达式解析文本

from pdfminer.high_level import extract_text

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")



if not DEEPSEEK_API_KEY:
    raise RuntimeError("环境变量 DEEPSEEK_API_KEY 未设置，请先配置！")

def pdf_to_text(file_path: str) -> str:
    return extract_text(file_path)

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

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        if "choices" in response_data and response_data["choices"]:
            qa_text = response_data["choices"][0]["message"]["content"]

            # 按行分割文本
            lines = qa_text.splitlines()

            # 确保生成的数据符合预期
            if len(lines) < 6:
                print("生成的选择题文本格式不完整")
                return []

            # 提取问题并去除"问题:"前缀
            question = lines[0].strip().replace("问题:", "").strip()

            # 提取选项
            options = {
                "A": lines[1].strip()[3:],  # 去掉 "A) " 前缀
                "B": lines[2].strip()[3:],  # 去掉 "B) " 前缀
                "C": lines[3].strip()[3:],  # 去掉 "C) " 前缀
                "D": lines[4].strip()[3:],  # 去掉 "D) " 前缀
            }

            # 提取正确答案
            correct_answer = lines[5].strip().split(":")[1].strip()  # 只保留字母

            # 返回结构化的数据
            return [{
                "question": question,
                "options": options,
                "correct_answer": correct_answer
            }]
        else:
            print("API 返回数据没有包含 'choices' 或返回为空")
            return []

    except Exception as e:
        print(f"API 请求失败: {e}")
        return []
