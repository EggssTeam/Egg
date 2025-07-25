import os

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 宏定义 Whisper API 地址和你的API KEY
WHISPER_API_URL = "https://api.gpt.ge/v1/audio/transcriptions"
GPT4O_API_URL = "https://api.gpt.ge/v1/chat/completions"
# WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
# GPT4O_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")