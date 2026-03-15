"""
测试大模型对话
"""
import requests
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取 API Key
ARK_API_KEY = os.getenv("ARK_API_KE")

if not ARK_API_KEY:
    raise ValueError("未找到 ARK_API_KE 环境变量")

# API 配置
URL = "https://ark.cn-beijing.volces.com/api/v3/responses"
MODEL = "deepseek-v3-2-251201"


def chat(prompt: str, user_message: str):
    """调用大模型对话

    Args:
        prompt: 系统提示词
        user_message: 用户消息

    Returns:
        str: 大模型回复
    """
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "stream": False,  # 非流式输出
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_message
                    }
                ]
            }
        ]
    }

    response = requests.post(URL, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    # 提取回复内容
    output = result.get("output", [])
    if output:
        for item in output:
            if item.get("type") == "message":
                content = item.get("content", [])
                for c in content:
                    if c.get("type") == "output_text":
                        return c.get("text", "")

    return ""


def chat_stream(prompt: str, user_message: str):
    """流式调用大模型对话

    Args:
        prompt: 系统提示词
        user_message: 用户消息
    """
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "stream": True,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_message
                    }
                ]
            }
        ]
    }

    response = requests.post(URL, headers=headers, json=data, stream=True)
    response.raise_for_status()

    print("大模型回复: ", end="")
    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data_json = json.loads(data_str)
                    # 提取内容
                    output = data_json.get("output", [])
                    for item in output:
                        if item.get("type") == "message":
                            content = item.get("content", [])
                            for c in content:
                                if c.get("type") == "output_text":
                                    text = c.get("text", "")
                                    print(text, end="", flush=True)
                except json.JSONDecodeError:
                    pass
    print()  # 换行


if __name__ == "__main__":
    # 测试对话
    test_prompt = "你是一个友好的AI助手，请用简短的方式回答问题。"

    print("=" * 50)
    print("测试1: 普通对话")
    print("=" * 50)
    reply = chat(test_prompt, "你好，请介绍一下你自己")
    print(f"回复: {reply}")

    print()
    print("=" * 50)
    print("测试2: 流式对话")
    print("=" * 50)
    chat_stream(test_prompt, "今天有什么热点新闻")

    print()
    print("=" * 50)
    print("测试3: 多轮对话")
    print("=" * 50)
    reply = chat(test_prompt, "我的名字叫小明")
    print(f"回复: {reply}")
    reply = chat(test_prompt + f"\n\n用户说: 我的名字叫小明", "你知道我叫什么吗?")
    print(f"回复: {reply}")
