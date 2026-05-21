#demo
# from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_tavily import TavilySearch

from env_utils import ALIYUN_API_KEY, ALIYUN_BASE_URL, TAVILY_API_KEY

# llm = ChatOpenAI(
#     model="gpt-4o-mini",
#     temperature=0.9,
#     api_key=OPENAI_API_KEY,
#     base_url=OPENAI_BASE_URL
# )

# llm = ChatOpenAI(
#     model="deepseek-r1-0528",
#     temperature=0.9,
#     api_key=ALIYUN_API_KEY,
#     base_url=ALIYUN_BASE_URL
# )
llm = ChatOpenAI(
    model="qwen3.5-plus",
    temperature=0.9,
    api_key=ALIYUN_API_KEY,
    base_url=ALIYUN_BASE_URL
)
# embedding = OpenAIEmbeddings(
#     api_key=ALIYUN_API_KEY,
#     base_url=ALIYUN_BASE_URL,
#     model="text-embedding-v4",
#     dimensions=1024,
#     check_embedding_ctx_length=False  # 关键参数
# )

# multiModal_llm = ChatOpenAI(  # 多模态大模型
#     model='qwen3-vl-plus',
#     api_key=ALIYUN_API_KEY,
#     base_url=ALIYUN_BASE_URL,
# )
# print(embedding.embed_query("今天，北京的天气怎么样？"))

# llm = ChatDeepSeek(
#     model="deepseek-r1-0528",
#     api_key=ALIYUN_API_KEY,
#     api_base=ALIYUN_BASE_URL,
#     temperature=1.0,
# )
# llm = ChatOpenAI(
#     model="claude-3-5-sonnet-20240620",
#     temperature=0.9,
#     api_key=OPENAI_API_KEY,
#     base_url=OPENAI_BASE_URL
# )

# llm= ChatOpenAI(
#     model="Qwen3.5-9B",
#     base_url=LOCAL_BASE_URL,
#     api_key="xx",
#
#     temperature=1.0,
#
#
# )

# llm = ChatOpenAI(
#     model="DeepSeek-R1-0528-Qwen3-8B",
#     base_url=LOCAL_BASE_URL,
#     api_key="xx",
#
#     temperature=1.0,
#     extra_body={'chat_template_kwargs': {'enable_thinking': False}}
#
# )


# multiModal_llm = ChatOpenAI(
#     model="qwen2.5-omni-7b",
#     base_url=QWEN_BASE_URL,
#     api_key=QWEN_API_KEY,
#
# )

# zhipuai_client = ZhipuAiClient(api_key=ZAI_API_KEY)

# tavily_tool = TavilySearch(
#     max_results=1,
#     api_key=TAVILY_API_KEY
# )

