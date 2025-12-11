import os
from typing import Literal
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import PromptTemplate
from dashscope import api_key
from tavily import TavilyClient
from deepagents import create_deep_agent
import dotenv

dotenv.load_dotenv()
# 初始化搜索客户端
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
# a=tavily_client.search(query="who is Bill Gates")
# 定义搜索工具
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

# 定义系统提示
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

def tongyi_llm(s):
    """Run a web search"""
    # return "hello"

    prompt = PromptTemplate.from_template("{question}")
    tongyi_chat=ChatTongyi(model="qwen-plus",api_key=os.environ["DASHSCOPE_API_KEY"])
    value=prompt.invoke({"question":s})
    return tongyi_chat.invoke(value).content
# 创建 Deep Agent
agent = create_deep_agent(
    model="qwen-plus",
    tools=[tongyi_llm],
    system_prompt=research_instructions,
)

# 运行智能体
result = agent.invoke({"messages": [{"role": "user", "content": "What is langgraph?"}]})
print(result["messages"][-1].content)