
from deepagents import create_deep_agent
from tavily import TavilyClient
from langchain_community.chat_models import ChatTongyi

tongyi_chat = ChatTongyi(model="qwen-plus", )

tavily_client = TavilyClient(api_key="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")

def internet_search(query: str):
    """联网搜索功能"""
    return tavily_client.search(query)

system_prompt = "你是一个专家级的研究助理，任务是进行彻底的调研并撰写报告"

agent = create_deep_agent(
    model=tongyi_chat,
    tools=[internet_search],
    system_prompt=system_prompt,
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "详细调研Langchain最新发展写一个总结"}
    ]
})
pass
