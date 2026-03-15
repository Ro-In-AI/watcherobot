"""ASR模块 - 自动语音识别"""
from .base import ASRProvider, ASRResult
from .aliyun_asr import AliyunASR

__all__ = ["ASRProvider", "ASRResult", "AliyunASR"]
