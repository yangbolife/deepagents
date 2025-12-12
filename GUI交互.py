system_prompt = """
## 1. 核心角色 (Core Role)
你是一个顶级的AI视觉操作代理。你的任务是分析电脑屏幕截图，理解用户的指令，然后将任务分解为单一、精确的GUI原子操作。

## 2. [CRITICAL] JSON Schema & 绝对规则
你的输出**必须**是一个严格符合以下规则的JSON对象。**任何偏差都将导致失败**。

- **[R1] 严格的JSON**: 你的回复**必须**是且**只能是**一个JSON对象。禁止在JSON代码块前后添加任何文本、注释或解释。
- **[R2] 严格的Parameters结构**:`thought`对象的结构: "在这里用一句话简要描述你的思考过程。例如：用户想打开浏览器，我看到了桌面上的Chrome浏览器图标，所以下一步是点击它。"
- **[R3] 精确的Action值**: `action`字段的值**必须**是`## 3. 工具集`中定义的一个大写字符串（例如 `"CLICK"`, `"TYPE"`），不允许有任何前导/后置空格或大小写变化。
- **[R4] 严格的Parameters结构**: `parameters`对象的结构**必须**与所选Action在`## 3. 工具集`中定义的模板**完全一致**。键名、值类型都必须精确匹配。

## 3. 工具集 (Available Actions)
### CLICK
- **功能**: 单击屏幕。
- **Parameters模板**:
  {
    "x": <integer>,
    "y": <integer>,
    "description": "<string, optional:  (可选) 一个简短的字符串，描述你点击的是什么，例如 "Chrome浏览器图标" 或 "登录按钮"。>"
  }

### TYPE
- **功能**: 输入文本。
- **Parameters模板**:
{
  "text": "<string>",
  "needs_enter": <boolean>
}

### SCROLL
- **功能**: 滚动窗口。
- **Parameters模板**:
{
  "direction": "<'up' or 'down'>",
  "amount": "<'small', 'medium', or 'large'>"
}

### KEY_PRESS
- **功能**: 按下功能键。
- **Parameters模板**:
{
  "key": "<string: e.g., 'enter', 'esc', 'alt+f4'>"
}

### FINISH
- **功能**: 任务成功完成。
- **Parameters模板**:
{
  "message": "<string: 总结任务完成情况>"
}

### FAILE
- **功能**: 任务无法完成。
- **Parameters模板**:
{
  "reason": "<string: 清晰解释失败原因>"
}

## 4. 思维与决策框架
在生成每一步操作前，请严格遵循以下思考-验证流程：

目标分析: 用户的最终目标是什么？
屏幕观察 (Grounded Observation): 仔细分析截图。你的决策必须基于截图中存在的视觉证据。 如果你看不见某个元素，你就不能与它交互。
行动决策: 基于目标和可见的元素，选择最合适的工具。
构建输出:
a. 在thought字段中记录你的思考。
b. 选择一个action。
c. 精确复制该action的parameters模板，并填充值。
最终验证 (Self-Correction): 在输出前，最后检查一遍：
我的回复是纯粹的JSON吗？
action的值是否正确无误（大写、无空格）？
parameters的结构是否与模板100%一致？例如，对于CLICK，是否有独立的x和y键，并且它们的值都是整数？
"""

messages = [
    {
        "role": "system",
        "content": system_prompt},
    {   "role": "user",
        "content": [{"type": "image_url","image_url": {"url": "https://img.alicdn.com/imgextra/i2/O1CN016iJ8ob1C3xP1s2M6z_!!6000000000026-2-tps-3008-1758.png"}},
                  {"type": "text", "text": "帮我打开浏览器。"}]},
 ]
import os
from openai import OpenAI

def get_response(image_url,instruction):
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url},"max_pixels":1280*28*28},
                {"type": "text", "text": instruction}]},
    ]

    client = OpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        model="gui-plus",
        messages=messages
    )
    content = completion.choices[0].message.content
    return content

import json

def parse_json(json_output):
    lines = json_output.splitlines()
    for i, line in enumerate(lines):
        if line == "```json":
            json_output = "\n".join(lines[i + 1:])  # 删除 "```json"之前的所有内容
            json_output = json_output.split("```")[0]  # 删除 "```"之后的所有内容
            break  # 找到"```json"后退出循环
    response_dict = json.loads(json_output)
    return response_dict
import requests
import math
from PIL import Image
from io import BytesIO

def smart_size(image_url, point,factor = 28, max_pixels = 1280 * 28 * 28, min_pixels = 4 * 28 * 28):
    """
    param
      image_path: 图像url
      max_pixels：输入图像的最大像素值，超过此值则将图像的像素缩小至max_pixels内，与发起模型调用步骤设置的max_pixels值，应保持一致。
      min_pixels：输入图像的最小像素值，一般设置为默认值：4 * 28 * 28即可。
    return: 单张图像的Token数
    """
    response = requests.get(image_url)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content))
    # 获取图片的原始尺寸
    height = image.height
    width = image.width

    # 将高度调整为factor的整数倍
    h_bar = round(height / factor) * factor
    # 将宽度调整为factor的整数倍
    w_bar = round(width / factor) * factor
    # 对图像进行缩放处理，调整像素的总数在范围[min_pixels,max_pixels]内
    if h_bar * w_bar > max_pixels:
        # 计算缩放因子beta，使得缩放后的图像总像素数不超过max_pixels
        beta = math.sqrt((height * width) / max_pixels)
        # 重新计算调整后的高度，确保为factor的整数倍
        h_bar = math.floor(height / beta / factor) * factor
        # 重新计算调整后的宽度，确保为factor的整数倍
        w_bar = math.floor(width / beta / factor) * factor
    elif h_bar * w_bar < min_pixels:
        # 计算缩放因子beta，使得缩放后的图像总像素数不低于min_pixels
        beta = math.sqrt(min_pixels / (height * width))
        # 重新计算调整后的高度，确保为factor的整数倍
        h_bar = math.ceil(height * beta / factor) * factor
        # 重新计算调整后的宽度，确保为factor的整数倍
        w_bar = math.ceil(width * beta / factor) * factor
    abs_x1 = int(point["x"] / w_bar * width)
    abs_y1 = int(point["y"] / h_bar * height)
    return abs_x1, abs_y1


import pyautogui
import time
import sys

# 模拟滚动操作的默认幅度
SCROLL_AMOUNTS = {
    "small": 50,
    "medium": 200,
    "large": 500,
}


def execute_gui_action(action: str, parameters: dict, original_image_url: str):
    """
    根据模型输出的动作和参数执行GUI操作。

    Args:
        action (str): 模型输出的动作类型（如 "CLICK", "TYPE"）。
        parameters (dict): 动作的参数字典。
        original_image_url (str): 原始屏幕截图的URL，用于坐标映射。
    """
    print(f"执行动作: {action}, 参数: {parameters}")

    if action == "CLICK":
        # 确保 'x' 和 'y' 存在并为数值类型
        if "x" not in parameters or "y" not in parameters:
            print("错误: CLICK 动作缺少 'x' 或 'y' 坐标。")
            return

        # 将模型输出的坐标映射到原始屏幕分辨率
        try:
            abs_x, abs_y = smart_size(original_image_url, parameters)
            pyautogui.click(abs_x, abs_y)
            print(f"已点击坐标 ({abs_x}, {abs_y})")
        except Exception as e:
            print(f"坐标映射或点击失败: {e}")

    elif action == "TYPE":
        if "text" not in parameters:
            print("错误: TYPE 动作缺少 'text' 参数。")
            return

        text_to_type = parameters["text"]
        needs_enter = parameters.get("needs_enter", False)

        pyautogui.write(text_to_type)
        if needs_enter:
            pyautogui.press("enter")
        print(f"已输入文本: '{text_to_type}', 是否按回车: {needs_enter}")

    elif action == "SCROLL":
        if "direction" not in parameters or "amount" not in parameters:
            print("错误: SCROLL 动作缺少 'direction' 或 'amount' 参数。")
            return

        direction = parameters["direction"].lower()
        amount_key = parameters["amount"].lower()

        scroll_value = SCROLL_AMOUNTS.get(amount_key, SCROLL_AMOUNTS["medium"])  # 默认中等

        if direction == "up":
            pyautogui.scroll(scroll_value)
            print(f"已向上滚动 {scroll_value} 单位。")
        elif direction == "down":
            pyautogui.scroll(-scroll_value)  # pyautogui向下滚动需要负值
            print(f"已向下滚动 {scroll_value} 单位。")
        else:
            print(f"警告: 未知滚动方向: {direction}")

    elif action == "KEY_PRESS":
        if "key" not in parameters:
            print("错误: KEY_PRESS 动作缺少 'key' 参数。")
            return

        key_to_press = parameters["key"].lower()
        pyautogui.press(key_to_press)
        print(f"已按下按键: {key_to_press}")

    elif action == "FINISH":
        message = parameters.get("message", "任务已完成。")
        print(f"任务完成: {message}")

    elif action == "FAIL":
        reason = parameters.get("reason", "任务失败。")
        print(f"任务失败: {reason}")

    else:
        print(f"警告: 收到未知动作类型: {action}")

    # 模拟人类操作的延时，避免GUI操作过快
    time.sleep(1)  # 每次操作后等待1秒


if __name__ == "__main__":
    original_image_url = "https://img.alicdn.com/imgextra/i2/O1CN016iJ8ob1C3xP1s2M6z_!!6000000000026-2-tps-3008-1758.png"
    instruction = "帮我打开浏览器。"

    model_response = get_response(original_image_url, instruction)
    print("大模型的回复：", model_response)

    try:
        response_dict = parse_json(model_response)
        action = response_dict["action"]
        parameters = response_dict["parameters"]
    except ValueError as e:
        print(f"处理模型响应失败: {e}")
        sys.exit()

    execute_gui_action(action, parameters, original_image_url)