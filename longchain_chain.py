import dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
# dotenv.load_dotenv()
prompt = PromptTemplate.from_template("{question}")
tongyi_chat=ChatTongyi(model="qwen-plus",streaming=True)
# value=prompt.invoke({"question":"完整输出静夜思"})
chain = prompt | tongyi_chat | StrOutputParser()
# 增加自动画图
print(chain.invoke({"question":"随机选一首古诗，完整输出，再给出白话文解释给小学生"}))
# print(tongyi_chat.invoke(value).content)

#目标，随机找到一首古诗，然后完整输出，然后白话翻译给小朋友