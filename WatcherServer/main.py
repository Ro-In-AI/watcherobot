"""主程序入口"""
import asyncio

from src.config import settings
from src.core.websocket_server import WebSocketServer
from src.modules.asr.aliyun_asr import AliyunASR
from src.modules.openclaw import create_openclaw_provider
from src.modules.tts.huoshan_tts import HuoshanTTS
from src.utils.logger import setup_logger, get_logger

# 配置日志
setup_logger()
logger = get_logger(__name__)


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("语音识别 WebSocket 服务器启动")
    logger.info("=" * 60)

    # 创建 ASR 提供商
    asr_provider = AliyunASR(
        appkey=settings.aliyun_appkey,
        token=settings.aliyun_token,
        sample_rate=16000,
        channels=1,
        enable_intermediate_result=True,  # 启用中间结果，实时返回识别内容
        enable_punctuation_prediction=True,
        enable_inverse_text_normalization=True,
        # AK/SK 方式获取 Token
        ak_id=settings.aliyun_ak_id,
        ak_secret=settings.aliyun_ak_secret,
    )

    # 创建 TTS 提供商
    tts_app_key = settings.huoshan_app_key
    tts_access_key = settings.huoshan_access_key
    tts_voice_type = settings.huoshan_voice_type
    tts_sample_rate = settings.tts_sample_rate

    tts_provider = None
    if tts_app_key and tts_access_key:
        tts_provider = HuoshanTTS(
            app_key=tts_app_key,
            access_key=tts_access_key,
            voice_type=tts_voice_type or "ICL_zh_male_nuanxintitie_tob",
            sample_rate=tts_sample_rate,
            encoding="pcm",
        )
        logger.info(f"TTS提供商已配置: sample_rate={tts_sample_rate}")
    else:
        logger.warning("TTS配置未找到，跳过TTS初始化")

    # 创建 OpenClaw 提供商（自动选择 CLI 或 TMUX 方式）
    openclaw_provider = create_openclaw_provider(
        agent=settings.openclaw_agent,
        poll_interval=settings.openclaw_status_poll_interval,
    )
    logger.info(f"OpenClaw提供商已配置: agent={settings.openclaw_agent}, type={type(openclaw_provider).__name__}")

    # 创建 WebSocket 服务器
    server = WebSocketServer(
        host=settings.ws_host,
        port=settings.ws_port,
        asr_provider=asr_provider,
        openclaw_provider=openclaw_provider,
        tts_provider=tts_provider,
    )

    logger.info(f"服务器地址: ws://{settings.ws_host}:{settings.ws_port}")
    logger.info("请打开 test_client.html 进行测试")
    logger.info("按 Ctrl+C 停止服务器")

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        # 清理TTS资源
        if tts_provider:
            await tts_provider.cleanup()
        await server.stop()
        logger.info("服务器已关闭")


if __name__ == "__main__":
    asyncio.run(main())
