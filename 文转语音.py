# 请安装 DashScope SDK 的最新版本
import os
import dashscope

# 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

text = "那我来给大家推荐一款T恤，这款呢真的是超级好看，这个颜色呢很显气质，而且呢也是搭配的绝佳单品，大家可以闭眼入，真的是非常好看，对身材的包容性也很好，不管啥身材的宝宝呢，穿上去都是很好看的。推荐宝宝们下单哦。"
text = """
“蒋阳波”这个名字整体上给人一种阳光、积极、充满活力的感觉，寓意着光明、温暖、智慧与活力，是一个非常适合男孩的名字。

‌“蒋”‌ 字作为姓氏，本身就有“进取稳健、勇往直前、延年益寿、聪明智慧、品行高尚、富有思想”的美好寓意。
‌“阳”‌ 字则代表着“充满生机、正能量、光明正大、坚强勇敢、繁荣昌盛和光芒万丈”，寓意非常积极向上。
‌“波”‌ 字则象征着“智慧、活力、灵动、变化、包容和力量”，给人一种充满智慧与活力的感觉。
综合来看，“蒋阳波”这个名字寓意着拥有光明正大的品格、充满智慧与活力，并且能够勇敢地面对生活中的各种挑战，是一个非常有力量感的名字。
"""
# SpeechSynthesizer接口使用方法：dashscope.audio.qwen_tts.SpeechSynthesizer.call(...)
response = dashscope.MultiModalConversation.call(
    # 仅支持qwen-tts系列模型，请勿使用除此之外的其他模型
    model="qwen3-tts-flash",
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    text=text,
    voice="Cherry",
    language_type="English"
)
print(response)