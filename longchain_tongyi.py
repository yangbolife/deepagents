import dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import PromptTemplate
# dotenv.load_dotenv()
prompt = PromptTemplate.from_template("{question}")
tongyi_chat=ChatTongyi(model="qwen-plus",)
value=prompt.invoke({"question":"完整输出静夜思"})

print(tongyi_chat.invoke(value).content)