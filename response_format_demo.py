"""
使用 response_format 控制智能体返回结构化数据

三种方式对比：
1. response_format={"type": "json_object"}  — 仅要求返回 JSON，不校验 schema
2. with_structured_output(schema)            — 通过 function_calling 返回，自动校验（默认方式）
3. with_structured_output(schema, method="json_mode") — 结合 response_format + schema 校验
"""

import json

from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from env_utils import ALIYUN_API_KEY, ALIYUN_BASE_URL


# ==================== 定义输出 Schema ====================

class StockInfo(BaseModel):
    name: str = Field(description="股票名称")
    code: str = Field(description="股票代码")
    current_price: float = Field(description="当前价格（元）")
    change_percent: float = Field(description="涨跌幅百分比")
    analysis: str = Field(description="简要分析")


class AgentResponse(BaseModel):
    """智能体的最终结构化输出"""
    answer: str = Field(description="对用户问题的回答")
    stocks: list[StockInfo] = Field(description="涉及的股票信息")
    confidence: float = Field(description="回答置信度 0~1", ge=0, le=1)
    sources: list[str] = Field(description="信息来源")


# ==================== 方式一：response_format 直接控制 ====================

llm = ChatOpenAI(
    model="qwen3.5-plus",
    temperature=0.1,
    api_key=ALIYUN_API_KEY,
    base_url=ALIYUN_BASE_URL,
)

# 告诉模型"必须返回 JSON"，但不强制 schema
llm_json = llm.bind(response_format={"type": "json_object"})

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个股票助手。你必须以 JSON 格式返回数据，包含以下字段：answer, stocks, confidence, sources。stocks 是数组，每个元素包含 name, code, current_price, change_percent, analysis。"),
    ("human", "{question}"),
])

chain = prompt | llm_json | JsonOutputParser()

result = chain.invoke({"question": "贵州茅台最近走势如何？"})
print("=== 方式一：response_format json_object ===")
print(json.dumps(result, ensure_ascii=False, indent=2))


# ==================== 方式二：with_structured_output（推荐） ====================
# 内部通过 function_calling 实现，自动校验 Pydantic schema

structured_llm = llm.with_structured_output(AgentResponse)

prompt2 = ChatPromptTemplate.from_messages([
    ("system", "你是一个股票助手，请根据用户问题返回结构化数据。"),
    ("human", "{question}"),
])

chain2 = prompt2 | structured_llm

result2 = chain2.invoke({"question": "贵州茅台最近走势如何？"})
print("\n=== 方式二：with_structured_output (function_calling) ===")
# result2 是 AgentResponse 实例，类型安全
print(f"回答: {result2.answer}")
print(f"置信度: {result2.confidence}")
print(f"股票: {[s.name for s in result2.stocks]}")
print(result2.model_dump_json(indent=2))


# ==================== 方式三：with_structured_output + json_mode ====================
# 底层使用 response_format={"type": "json_object"} + schema 约束 + Pydantic 校验

structured_llm_v3 = llm.with_structured_output(AgentResponse, method="json_mode")

prompt3 = ChatPromptTemplate.from_messages([
    ("system", "你是一个股票助手，请以 JSON 格式返回数据，遵循以下 schema：{schema}"),
    ("human", "{question}"),
])

chain3 = prompt3 | structured_llm_v3

result3 = chain3.invoke({
    "question": "贵州茅台最近走势如何？",
    "schema": AgentResponse.model_json_schema(),
})
print("\n=== 方式三：with_structured_output (json_mode) ===")
print(result3.model_dump_json(indent=2))


# ==================== 智能体场景：agent 输出结构化 ====================
# 先让 agent 正常运行（调用工具等），最后一步用 structured_llm 格式化输出

async def agent_with_structured_output(user_question: str) -> AgentResponse:
    """
    智能体工作流：
    1. agent 正常执行（调用工具、搜索等）
    2. 拿到 agent 的原始文本回复
    3. 用 structured_llm 将回复转为结构化数据
    """
    # Step 1: agent 正常运行拿到原始回复（这里简化演示）
    raw_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个股票智能小助手，你可以查股票相关信息。请详细回答用户问题。"),
        ("human", "{question}"),
    ])
    raw_chain = raw_prompt | llm
    raw_response = raw_chain.invoke({"question": user_question})

    # Step 2: 用 structured_llm 将原始回复转为结构化输出
    format_prompt = ChatPromptTemplate.from_messages([
        ("system", "将以下股票分析内容转为结构化数据。"),
        ("human", "原始内容：\n{content}"),
    ])
    format_chain = format_prompt | structured_llm
    structured_result = format_chain.invoke({"content": raw_response.content})

    return structured_result


if __name__ == "__main__":
    import asyncio

    async def main():
        result = await agent_with_structured_output("贵州茅台和五粮液最近走势如何？")
        print("\n=== 智能体结构化输出 ===")
        print(result.model_dump_json(indent=2))

    asyncio.run(main())
