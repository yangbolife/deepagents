import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# 加载环境变量
load_dotenv(override=True)

deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
deepseek_base_url = "https://api.deepseek.com"

# 初始化 DeepSeek 模型
model = init_chat_model(
    api_key=deepseek_api_key,
    base_url=deepseek_base_url,
    model_provider="deepseek",
    model="deepseek-chat"
)

# 测试模型调用
print("测试 DeepSeek 模型连接...")
result = model.invoke("你好，请用一句话介绍DeepSeek-v3.2。")
print(f"DeepSeek 回复: {result.content}")