"""阿里云ASR测试脚本"""
import asyncio
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.asr.aliyun_asr import AliyunASR
from src.config import settings
from src.utils.logger import setup_logger, get_logger

# 配置日志
setup_logger()
logger = get_logger(__name__)


async def test_aliyun_asr_with_file(audio_file: str):
    """使用音频文件测试阿里云ASR

    Args:
        audio_file: PCM音频文件路径（16000Hz, 16bit, 单声道）
    """
    logger.info(f"开始测试阿里云ASR，音频文件: {audio_file}")

    # 检查文件是否存在
    if not Path(audio_file).exists():
        logger.error(f"音频文件不存在: {audio_file}")
        return

    # 创建ASR实例
    asr = AliyunASR(
        appkey=settings.aliyun_appkey,
        token=settings.aliyun_token,
        sample_rate=16000,
        channels=1,
        enable_intermediate_result=True,
        enable_punctuation_prediction=True,
        enable_inverse_text_normalization=True,
    )

    try:
        # 初始化
        await asr.initialize()
        logger.info("ASR初始化成功")

        # 读取音频文件
        with open(audio_file, "rb") as f:
            audio_data = f.read()

        logger.info(f"音频文件大小: {len(audio_data)} bytes")

        # 分块发送音频数据（每640字节一块）
        chunk_size = 640
        chunks = [audio_data[i:i + chunk_size] for i in range(0, len(audio_data), chunk_size)]

        logger.info(f"开始发送音频数据，共 {len(chunks)} 块")

        for i, chunk in enumerate(chunks):
            result = await asr.process_audio(chunk)
            if i % 10 == 0:  # 每10块打印一次中间结果
                logger.info(f"进度: {i + 1}/{len(chunks)}, 当前识别: {result.text}")

            # 模拟实时音频流
            await asyncio.sleep(0.01)

        # 停止识别并获取最终结果
        logger.info("音频数据发送完成，等待最终结果...")
        await asr.stop()

        # 等待一下让回调完成
        await asyncio.sleep(1)

        logger.info("测试完成")
        logger.info(f"最终识别文本: {asr._current_text}")

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
    finally:
        # 清理资源
        await asr.cleanup()
        logger.info("ASR资源已清理")


async def test_aliyun_asr_realtime():
    """使用麦克风实时测试阿里云ASR（正确实时流）"""

    import sounddevice as sd
    import numpy as np

    logger.info("开始麦克风实时ASR测试")

    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_DURATION = 0.1  # 100ms
    CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

    asr = AliyunASR(
        appkey=settings.aliyun_appkey,
        token=settings.aliyun_token,
        sample_rate=SAMPLE_RATE,
        channels=CHANNELS,
    )

    try:
        # 1️⃣ 初始化
        await asr.initialize()
        logger.info("ASR初始化成功")

        # ⭐⭐ 关键：第一次调用 process_audio 时会自动启动 session
        # 不需要手动调用 start()

        loop = asyncio.get_running_loop()
        audio_queue = asyncio.Queue()

        # ===== 麦克风回调 =====
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(status)

            # float32 → int16 PCM
            pcm = (indata * 32767).astype(np.int16).tobytes()

            loop.call_soon_threadsafe(audio_queue.put_nowait, pcm)

        logger.info("开始监听麦克风（Ctrl+C停止）")

        # ===== 打开麦克风 =====
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=CHUNK_SIZE,
            callback=audio_callback,
        ):

            while True:
                chunk = await audio_queue.get()
                result = await asr.process_audio(chunk)

                # 每10个chunk打印一次调试信息
                if not hasattr(test_aliyun_asr_realtime, '_chunk_count'):
                    test_aliyun_asr_realtime._chunk_count = 0
                test_aliyun_asr_realtime._chunk_count += 1

                if test_aliyun_asr_realtime._chunk_count % 10 == 0:
                    logger.info(f"已发送 {test_aliyun_asr_realtime._chunk_count} 个音频块")

                # 无论有没有文字都打印，方便调试
                if result:
                    if result.text:
                        logger.info(f"识别: {result.text}")
                    # else:
                    #     logger.debug("音频已发送，等待识别...")

                await asyncio.sleep(CHUNK_DURATION)

    except KeyboardInterrupt:
        logger.info("用户停止识别")

    except Exception as e:
        logger.error(f"实时测试失败: {e}", exc_info=True)

    finally:
        await asr.stop()
        await asr.cleanup()
        logger.info("ASR资源已清理")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="阿里云ASR测试脚本")
    parser.add_argument(
        "--mode",
        choices=["file", "realtime"],
        default="file",
        help="测试模式: file(文件模式) 或 realtime(实时模式)"
    )
    parser.add_argument(
        "--audio",
        type=str,
        help="音频文件路径（仅file模式需要）"
    )

    args = parser.parse_args()

    if args.mode == "file":
        if not args.audio:
            logger.error("文件模式需要指定 --audio 参数")
            return

        asyncio.run(test_aliyun_asr_with_file(args.audio))
    else:
        asyncio.run(test_aliyun_asr_realtime())


if __name__ == "__main__":
    main()
