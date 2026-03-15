"""TTS模块 - 文本转语音"""
from .base import TTSProvider, TTSResult
from .huoshan_tts import HuoshanTTS

__all__ = ["TTSProvider", "TTSResult", "HuoshanTTS"]
