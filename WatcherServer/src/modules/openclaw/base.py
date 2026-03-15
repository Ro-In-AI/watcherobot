"""OpenClaw基础类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str  # 消息内容


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str  # 响应内容
    model: str  # 使用的模型
    finish_reason: Optional[str] = None  # 结束原因
    usage: Optional[dict] = field(default_factory=dict)  # 使用量统计


class OpenClawProvider(ABC):
    """OpenClaw提供商基类"""

    def __init__(self):
        """初始化OpenClaw提供商"""
        self._is_initialized = False

    @abstractmethod
    async def initialize(self):
        """初始化OpenClaw客户端"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """发送聊天请求

        Args:
            messages: 消息列表
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            聊天响应
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
