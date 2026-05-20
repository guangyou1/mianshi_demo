import os
#demo
from dotenv import load_dotenv

load_dotenv(override=True)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY")
ZAI_API_KEY = os.getenv("ZAI_API_KEY")
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")



OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL")
ALIYUN_BASE_URL = os.getenv("ALIYUN_BASE_URL")
