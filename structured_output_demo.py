from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from env_utils import ALIYUN_API_KEY, ALIYUN_BASE_URL

# ========== 1. 定义结构化输出的 Schema ==========

class StockInfo(BaseModel):
    """股票信息结构化输出"""
    name: str = Field(description="股票名称")
    code: str = Field(description="股票代码")
    current_price: float = Field(description="当前价格")
    change_percent: float = Field(description="涨跌幅百分比")
    analysis: str = Field(description="简要分析")
    recommendation: str = Field(description="投资建议：买入/持有/卖出")


class StockComparison(BaseModel):
    """多只股票对比"""
    stocks: list[StockInfo] = Field(description="股票列表")
    summary: str = Field(description="对比总结")


# ========== 2. 创建 LLM 并绑定结构化输出 ==========

llm = ChatOpenAI(
    model="qwen3.5-plus",
    temperature=0.1,  # 结构化输出建议用低温度
    api_key=ALIYUN_API_KEY,
    base_url=ALIYUN_BASE_URL,
)

# 方式一：绑定 Pydantic 模型（推荐，自动校验）
structured_llm = llm.with_structured_output(StockInfo)

# 方式二：使用 json_mode（返回原始 dict，不做校验）
# structured_llm = llm.with_structured_output(StockInfo, method="json_mode")


# ========== 3. 调用 ==========

result = structured_llm.invoke("请介绍一下贵州茅台的股票情况")

# result 是 StockInfo 实例，可直接访问字段
print(f"股票名称: {result.name}")
print(f"股票代码: {result.code}")
print(f"当前价格: {result.current_price}")
print(f"涨跌幅: {result.change_percent}%")
print(f"分析: {result.analysis}")
print(f"建议: {result.recommendation}")

# 也可以转成 dict 或 JSON
print("\n--- JSON 输出 ---")
print(result.model_dump_json(indent=2))


# ========== 4. 多股票对比示例 ==========

comparison_llm = llm.with_structured_output(StockComparison)
result2 = comparison_llm.invoke("对比贵州茅台和五粮液的股票情况")
print("\n--- 多股票对比 ---")
print(result2.model_dump_json(indent=2))
