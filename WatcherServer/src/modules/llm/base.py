"""LLM基础类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str  # 响应内容
    model: str  # 使用的模型
    finish_reason: Optional[str] = None  # 结束原因


class LLMProvider(ABC):
    """LLM提供商基类"""

    def __init__(self):
        """初始化LLM提供商"""
        self._is_initialized = False

    @abstractmethod
    async def initialize(self):
        """初始化LLM客户端"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._is_initialized
