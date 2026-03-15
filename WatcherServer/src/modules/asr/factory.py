"""ASR工厂类"""
from typing import Optional

from src.config import settings
from src.modules.asr.base import ASRProvider
from src.modules.asr.aliyun_asr import AliyunASR
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ASRFactory:
    """ASR工厂类，用于创建ASR实例"""

    @staticmethod
    def create_provider() -> Optional[ASRProvider]:
        """根据配置创建ASR实例

        Returns:
            ASRProvider实例，如果不支持的provider则返回None
        """
        provider = settings.asr_provider.lower()

        if provider == "aliyun":
            logger.info("创建阿里云ASR实例")
            return AliyunASR(
                appkey=settings.aliyun_appkey,
                token=settings.aliyun_token,  # 兼容旧的临时 Token 方式
                url=settings.aliyun_asr_url,
                sample_rate=settings.asr_sample_rate,
                channels=settings.asr_channels,
                enable_intermediate_result=settings.aliyun_asr_enable_intermediate_result,
                enable_punctuation_prediction=settings.aliyun_asr_enable_punctuation_prediction,
                enable_inverse_text_normalization=settings.aliyun_asr_enable_inverse_text_normalization,
                # 新增：AK/SK 方式
                ak_id=settings.aliyun_ak_id,
                ak_secret=settings.aliyun_ak_secret,
            )
        elif provider == "xunfei":
            logger.warning("讯飞ASR尚未实现")
            return None
        elif provider == "whisper":
            logger.warning("Whisper ASR尚未实现")
            return None
        else:
            logger.warning(f"不支持的ASR提供商: {provider}")
            return None
