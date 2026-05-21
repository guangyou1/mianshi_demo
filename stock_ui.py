import json
import os

import gradio as gr
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from env_utils import ALIYUN_BASE_URL, ALIYUN_API_KEY
from db import save_analysis, get_all_analysis


# ==================== 结构化输出 Schema ====================

class StockAnalysis(BaseModel):
    summary: str = Field(description="对股票数据的分析总结")
    sentiment: str = Field(description="市场情绪，只可能是：Bullish、Neutral、Bearish")
    risk_level: str = Field(description="风险等级，如：Low、Medium、High")


# ==================== AI 分析 LLM ====================

analysis_llm = ChatOpenAI(
    model="qwen3.5-plus",
    temperature=0.1,
    api_key=ALIYUN_API_KEY,
    base_url=ALIYUN_BASE_URL,
).with_structured_output(StockAnalysis, method="json_mode")

analysis_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "你是一个专业的股票分析师。根据以下数据，严格按照 JSON schema 返回分析结果。\n"
     "schema: {schema}\n"
     "注意：sentiment 只能是 Bullish / Neutral / Bearish 之一。"),
    ("human", "股票数据：\n{data}"),
])

analysis_chain = analysis_prompt | analysis_llm


def do_analysis(stock_data: str) -> tuple[str, StockAnalysis | None]:
    """调用 LLM 分析，返回 (格式化展示, 分析结果对象)"""
    result = analysis_chain.invoke({
        "data": stock_data,
        "schema": StockAnalysis.model_json_schema(),
    })
    return format_result(result), result


def do_fallback(stock_data: str) -> tuple[str, dict | None]:
    """降级模式：response_format + JsonOutputParser"""
    fallback_llm = ChatOpenAI(
        model="qwen3.5-plus",
        temperature=0.1,
        api_key=ALIYUN_API_KEY,
        base_url=ALIYUN_BASE_URL,
    ).bind(response_format={"type": "json_object"})

    fallback_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是股票分析师。返回严格 JSON，字段：summary(str), sentiment(Bullish/Neutral/Bearish), risk_level(Low/Medium/High)。只返回 JSON，不要其他内容。"),
        ("human", "股票数据：\n{data}"),
    ])
    fallback_chain = fallback_prompt | fallback_llm | JsonOutputParser()
    raw = fallback_chain.invoke({"data": stock_data})

    formatted = (
        f"### 🤖 AI 分析结果（降级模式）\n\n"
        f"**总结**：{raw.get('summary', '')}\n\n"
        f"**市场情绪**：{raw.get('sentiment', '')}\n\n"
        f"**风险等级**：{raw.get('risk_level', '')}\n\n"
        f"---\n"
        f"```json\n{json.dumps(raw, ensure_ascii=False, indent=2)}\n```"
    )
    return formatted, raw


def format_result(result: StockAnalysis) -> str:
    sentiment_emoji = {"Bullish": "📈", "Neutral": "➡️", "Bearish": "📉"}
    risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
    emoji = sentiment_emoji.get(result.sentiment, "❓")
    risk = risk_emoji.get(result.risk_level, "❓")

    return (
        f"### 🤖 AI 分析结果\n\n"
        f"**总结**：{result.summary}\n\n"
        f"**市场情绪**：{emoji} {result.sentiment}\n\n"
        f"**风险等级**：{risk} {result.risk_level}\n\n"
        f"---\n"
        f"<details><summary>原始 JSON</summary>\n\n"
        f"```json\n{result.model_dump_json(indent=2)}\n```\n"
        f"</details>"
    )


def run_ai_analysis(stock_data: str):
    """点击按钮：分析 + 存库"""
    if not stock_data or not stock_data.strip():
        return "请先输入股票数据"

    try:
        formatted, result = do_analysis(stock_data)
        record_id = save_analysis(stock_data, result.summary, result.sentiment, result.risk_level)
        return formatted + f"\n\n💾 已保存到数据库（ID: {record_id}）"

    except Exception:
        try:
            formatted, raw = do_fallback(stock_data)
            record_id = save_analysis(
                stock_data,
                raw.get("summary", ""),
                raw.get("sentiment", ""),
                raw.get("risk_level", ""),
            )
            return formatted + f"\n\n💾 已保存到数据库（ID: {record_id}）"
        except Exception as e2:
            return f"分析失败：{e2}"


def load_history():
    """加载历史记录"""
    records = get_all_analysis()
    if not records:
        return "暂无历史记录"
    lines = []
    for r in records:
        lines.append(
            f"**#{r['id']}** | {r['created_at'].strftime('%Y-%m-%d %H:%M')} | "
            f"{r['sentiment']} | {r['risk_level']}\n"
            f"> {r['summary'][:80]}...\n"
        )
    return "\n".join(lines)


# ==================== Gradio UI ====================

#demo
with gr.Blocks(title="股票 AI 分析") as demo:
    gr.Markdown("# 股票 AI 结构化分析")

    stock_data_input = gr.Textbox(
        label="股票数据",
        placeholder="粘贴股票数据或输入股票名称...\n如：贵州茅台 2024年营收1695亿，净利润860亿...",
        lines=10,
    )
    analyze_btn = gr.Button("🔍 AI 分析", variant="primary", size="lg")
    analysis_output = gr.Markdown(label="分析结果")

    analyze_btn.click(
        fn=run_ai_analysis,
        inputs=stock_data_input,
        outputs=analysis_output,
    )

    gr.Markdown("---")
    with gr.Row():
        refresh_btn = gr.Button("🔄 刷新历史")
        history_output = gr.Markdown(label="历史记录")
        refresh_btn.click(fn=load_history, outputs=history_output)

    gr.Markdown(
        "---\n**返回格式**：\n"
        "- `summary`：分析总结\n"
        "- `sentiment`：Bullish / Neutral / Bearish\n"
        "- `risk_level`：Low / Medium / High"
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
