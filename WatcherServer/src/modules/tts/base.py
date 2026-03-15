"""TTS基础类"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, AsyncIterator


@dataclass
class TTSResult:
    """TTS合成结果"""

    audio_data: bytes  # 音频二进制数据
    format: str  # 音频格式 (wav, mp3, etc.)
    sample_rate: int  # 采样率
    duration: Optional[float] = None  # 时长(秒)


class TTSProvider(ABC):
    """TTS提供商基类"""

    def __init__(self):
        """初始化TTS提供商"""
        self._is_initialized = False

    @abstractmethod
    async def initialize(self):
        """初始化TTS引擎"""
        pass

    @abstractmethod
    async def synthesize(self, text: str) -> TTSResult:
        """合成语音

        Args:
            text: 要合成的文本

        Returns:
            TTS合成结果
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

    @staticmethod
    def split_text_by_sentences(text: str, max_length: int = 200) -> list[str]:
        """按标点符号分句，支持长文本切分

        Args:
            text: 原始文本
            max_length: 单句最大字符数

        Returns:
            list[str]: 句子列表
        """
        if not text:
            return []

        # 标点符号正则
        sentence_end = re.compile(r'([。！？；\n]+)')
        # 分割句子
        sentences = sentence_end.split(text)

        result = []
        current = ""

        for part in sentences:
            # 如果是分隔符，直接添加到当前句子并结束
            if sentence_end.match(part):
                current += part
                if current.strip():
                    result.append(current.strip())
                current = ""
            else:
                # 检查当前部分是否超长
                if len(current) + len(part) > max_length:
                    # 当前句子太长，需要分割
                    if current.strip():
                        result.append(current.strip())
                    # 尝试在当前部分中找到合适的位置分割
                    remaining = part
                    while len(remaining) > max_length:
                        # 找到逗号分割
                        comma_pos = remaining[:max_length].rfind('，')
                        if comma_pos > max_length // 2:
                            result.append(remaining[:comma_pos + 1].strip())
                            remaining = remaining[comma_pos + 1:]
                        else:
                            # 没有合适的分割点，直接截断
                            result.append(remaining[:max_length].strip())
                            remaining = remaining[max_length:]
                    current = remaining
                else:
                    current += part

        # 处理最后剩余的文本
        if current.strip():
            result.append(current.strip())

        return result if result else [text]

    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncIterator[TTSResult]:
        """流式合成语音（边合成边返回）

        Args:
            text: 要合成的文本

        Yields:
            TTSResult: 音频片段结果
        """
        pass
