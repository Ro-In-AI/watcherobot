"""ASR基础类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ASRResult:
    """ASR识别结果"""

    text: str  # 识别文本
    confidence: float  # 置信度 0-1
    is_final: bool = False  # 是否为最终结果
    timestamp: Optional[float] = None  # 时间戳


class ASRProvider(ABC):
    """ASR提供商基类"""

    def __init__(self):
        """初始化ASR提供商"""
        self._is_initialized = False

    @abstractmethod
    async def initialize(self):
        """初始化ASR引擎"""
        pass

    @abstractmethod
    async def process_audio(self, audio_data: bytes) -> ASRResult:
        """处理音频数据

        Args:
            audio_data: 音频二进制数据

        Returns:
            ASR识别结果
        """
        pass

    @abstractmethod
    async def reset(self):
        """重置ASR状态，用于新的会话"""
        pass

    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._is_initialized
