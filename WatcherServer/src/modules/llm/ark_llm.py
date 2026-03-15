"""Ark LLM 实现"""
import json
from typing import Optional

import requests

from src.modules.llm.base import LLMProvider, LLMResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArkLLM(LLMProvider):
    """Ark LLM 提供商"""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v3-2-251201",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ):
        """初始化 Ark LLM

        Args:
            api_key: API Key
            model: 模型名称
            base_url: API 基础地址
        """
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._url = f"{base_url}/responses"

    async def initialize(self):
        """初始化"""
        # Ark LLM 不需要特殊初始化
        self._is_initialized = True
        logger.info(f"Ark LLM 初始化完成: model={self.model}")

    async def chat(
        self,
        prompt: str,
        user_message: str,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求（单轮对话）

        Args:
            prompt: 系统提示词
            user_message: 用户消息
            **kwargs: 其他参数

        Returns:
            LLM响应
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "stream": False,
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

        try:
            response = requests.post(self._url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()

            # 提取回复内容
            output = result.get("output", [])
            content = ""
            for item in output:
                if item.get("type") == "message":
                    msg_content = item.get("content", [])
                    for c in msg_content:
                        if c.get("type") == "output_text":
                            content = c.get("text", "")

            return LLMResponse(
                content=content,
                model=self.model,
                finish_reason="stop"
            )
        except Exception as e:
            logger.error(f"Ark LLM 调用失败: {e}")
            raise

    async def cleanup(self):
        """清理资源"""
        self._is_initialized = False
        logger.info("Ark LLM 已清理")
