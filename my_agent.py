import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncIterator
#demo
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_core.tools import StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from env_utils import ALIYUN_BASE_URL, ALIYUN_API_KEY


def wrap_tools_with_error_handling(tools):
    """包装 MCP 工具，捕获异常并返回错误消息给 LLM，而非让异常崩溃整个流。"""
    wrapped = []
    for tool in tools:
        if isinstance(tool, StructuredTool) and tool.coroutine:
            original_coroutine = tool.coroutine

            async def safe_coroutine(*args, _orig=original_coroutine, _name=tool.name, **kwargs):
                try:
                    return await _orig(*args, **kwargs)
                except Exception as e:
                    return f"工具 {_name} 调用失败: {type(e).__name__}: {e}"

            wrapped.append(
                StructuredTool.from_function(
                    func=tool.func,
                    coroutine=safe_coroutine,
                    name=tool.name,
                    description=tool.description,
                    args_schema=tool.args_schema,
                )
            )
        else:
            wrapped.append(tool)
    return wrapped


def get_python_executable():
    """获取当前Python解释器的完整路径"""
    python_exe = sys.executable
    print(f"当前Python解释器: {python_exe}")
    return python_exe


# 大模型
llm = ChatOpenAI(
    model_name="deepseek-v3.2",
    temperature=1.1,
    api_key=ALIYUN_API_KEY,
    base_url=ALIYUN_BASE_URL
)




async def main():
    client=MultiServerMCPClient(
        {
            "weather": {
                "transport": "streamable_http",  # HTTP-based remote server
                # Ensure you start your weather server on port 8000
                "url": "https://mcp.api-inference.modelscope.net/aa5a42ddf88a46/mcp",
            }
        }
    )
    tools = await client.get_tools()
    tools = wrap_tools_with_error_handling(tools)


    checkpointer = InMemorySaver()

    # # 本地沙箱
    # backend = LocalShellBackend(
    #     root_dir=".",  # 将Agent的文件系统访问限制在当前目录下
    #     virtual_mode=True,  # 启用虚拟模式，规范化路径，阻止使用 `..` 和 `~` 等越界访问
    #     # 设置环境变量，包含编码相关的配置
    #     env={
    #         "PATH": f"{os.path.dirname(get_python_executable())};{os.environ.get('PATH', '')}",
    #         "PYTHONPATH": str(workspace_dir),
    #         "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
    #     },
    # )

    agent = create_deep_agent(
        # backend=backend,
        model=llm,

        tools=tools,
        checkpointer=checkpointer,
        system_prompt=f'你是一个股票智能小助手，你可以查股票相关信息',
    )

    print('Agent 创建成功')

    # 与Agent进行交互
    thread_id = "demo_thread_01"
    async for response in stream_agent_interaction_corrected(agent, thread_id):
        print(response, end="", flush=True)


async def stream_agent_interaction_corrected(agent, thread_id: str) -> AsyncIterator[str]:
    """
    使用 agent.astream() 进行异步流式交互，兼容异步 MCP 工具。
    chunk 的结构是 (AIMessageChunk, metadata_dict)
    """
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = input("\n\n[用户] >>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n对话结束。")
            break

        if user_input.lower() in ('quit', 'exit', '退出', 'q'):
            print("再见！")
            break
        if not user_input:
            continue

        print("\n[助手] ", end="", flush=True)

        inputs = {"messages": [{"role": "user", "content": user_input}]}

        # 使用 astream 替代 stream，以支持异步 MCP 工具
        stream = agent.astream(inputs, config=config, stream_mode="messages", subgraphs=False)

        try:
            async for chunk in stream:
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    token, metadata = chunk

                    # 流式输出 AI 生成的文本内容
                    if hasattr(token, 'content') and token.content is not None:
                        content_str = str(token.content)
                        if content_str:
                            yield content_str

                    # 捕获并显示工具调用开始
                    if hasattr(token, 'tool_call_chunks') and token.tool_call_chunks:
                        for tool_chunk in token.tool_call_chunks:
                            if tool_chunk and hasattr(tool_chunk, 'get'):
                                if tool_chunk.get('name'):
                                    tool_name = tool_chunk['name']
                                    yield f"\n[调用工具: {tool_name}]\n"

                else:
                    print(f"\n[调试] 意外的 chunk 结构: {type(chunk)}", file=sys.stderr)
                    continue

        except Exception as e:
            yield f"\n❌ Agent 执行出错: {e}\n"
            import traceback
            traceback.print_exc()
            continue

#demo
if __name__ == '__main__':
    asyncio.run(main())