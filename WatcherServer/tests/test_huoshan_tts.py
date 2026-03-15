"""火山引擎TTS测试"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.modules.tts import HuoshanTTS
from src.utils.logger import setup_logger, get_logger

# 配置日志
setup_logger()
logger = get_logger(__name__)


async def test_tts_synthesize():
    """测试TTS语音合成"""
    logger.info("=" * 60)
    logger.info("开始测试火山引擎TTS语音合成")
    logger.info("=" * 60)

    # 从环境变量或配置文件获取配置
    app_key = os.getenv("App_Key", "7997928033").strip()
    access_key = os.getenv("Access_Key", "MmAGzY3U3-H1dEmmEvZCV9sQpArwZh-6").strip()
    voice_type = os.getenv("voice_type", "ICL_zh_male_nuanxintitie_tob").strip()

    logger.info(f"配置信息:")
    logger.info(f"  App Key: {app_key[:8]}...")
    logger.info(f"  Voice Type: {voice_type}")

    # 创建TTS实例 - 关闭连接复用，确保每次请求使用最新配置
    tts = HuoshanTTS(
        app_key=app_key,
        access_key=access_key,
        voice_type=voice_type,
        sample_rate=24000,  # 火山引擎PCM默认采样率是24000Hz
        encoding="pcm",
        speed_ratio=1.0,   # 语速
        volume_ratio=1.0,  # 音量
        pitch_ratio=1.0,   # 音调 (尝试调高到 1.2 看看是否改善)
    )

    try:
        # 初始化
        await tts.initialize()
        logger.info("TTS初始化成功")

        # 测试文本
        test_texts = [
            "你好，我是语音合成测试。",
            "今天天气真不错！",
            "语音识别和语音合成是人工智能的重要应用领域。",
            "Hello, this is a test for TTS.",
        ]

        for i, text in enumerate(test_texts, 1):
            logger.info(f"\n--- 测试 {i}: {text} ---")

            # 合成语音
            result = await tts.synthesize(text)

            logger.info(f"合成结果:")
            logger.info(f"  音频格式: {result.format}")
            logger.info(f"  采样率: {result.sample_rate} Hz")
            logger.info(f"  音频大小: {len(result.audio_data)} bytes")
            logger.info(f"  时长: {result.duration:.2f} 秒" if result.duration else "  时长: N/A")

            # 保存音频文件
            output_file = project_root / "output" / f"tts_test_{i}.pcm"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "wb") as f:
                f.write(result.audio_data)

            logger.info(f"音频已保存到: {output_file}")

        logger.info("\n" + "=" * 60)
        logger.info("所有测试完成！")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
    finally:
        # 清理资源
        await tts.cleanup()
        logger.info("TTS资源已清理")


async def test_different_voices():
    """测试不同的音色和音调设置"""
    logger.info("=" * 60)
    logger.info("测试不同的音色和音调设置")
    logger.info("=" * 60)

    app_key = os.getenv("App_Key", "7997928033").strip()
    access_key = os.getenv("Access_Key", "MmAGzY3U3-H1dEmmEvZCV9sQpArwZh-6").strip()

    # 测试不同的音色类型
    voice_types = [
        "ICL_zh_male_nuanxintitie_tob",  # 暖心体贴
        "zh_female_qiaopinvsheng_mars_bigtts",  # 俏皮女声
        "ICL_zh_female_zhixingwenwan_tob",  # 知性温婉
    ]

    # 测试不同的音调
    pitch_ratios = [0.8, 1.0, 1.2, 1.5]

    test_text = "你好，请问我能帮你做什么？"

    for voice_type in voice_types:
        for pitch in pitch_ratios:
            logger.info(f"\n--- voice_type={voice_type}, pitch_ratio={pitch} ---")

            tts = HuoshanTTS(
                app_key=app_key,
                access_key=access_key,
                voice_type=voice_type,
                sample_rate=24000,  # 火山引擎PCM默认采样率是24000Hz
                pitch_ratio=pitch,
            )

            try:
                await tts.initialize()
                result = await tts.synthesize(test_text)

                # 保存文件
                filename = f"voice_{voice_type}_pitch_{pitch}.wav"
                output_file = project_root / "output" / filename
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with wave.open(str(output_file), 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(result.sample_rate)
                    wav_file.writeframes(result.audio_data)

                logger.info(f"已保存: {output_file.name}")

            except Exception as e:
                logger.error(f"合成失败: {e}")
            finally:
                await tts.cleanup()

    logger.info("\n所有测试完成！")


async def test_tts_with_wav_header():
    """测试生成带WAV头的音频文件"""
    logger.info("=" * 60)
    logger.info("测试生成带WAV头的音频文件")
    logger.info("=" * 60)

    app_key = os.getenv("App_Key", "7997928033").strip()
    access_key = os.getenv("Access_Key", "MmAGzY3U3-H1dEmmEvZCV9sQpArwZh-6").strip()
    voice_type = os.getenv("voice_type", "ICL_zh_male_nuanxintitie_tob").strip()

    tts = HuoshanTTS(
        app_key=app_key,
        access_key=access_key,
        voice_type=voice_type,
        sample_rate=24000,  # 火山引擎PCM默认采样率是24000Hz
        encoding="pcm",
    )

    try:
        await tts.initialize()

        text = "这是一个带WAV头文件的测试。"
        logger.info(f"合成文本: {text}")

        result = await tts.synthesize(text)

        # 创建WAV文件
        import wave
        import struct

        output_file = project_root / "output" / "tts_test_with_header.wav"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(output_file), 'wb') as wav_file:
            wav_file.setnchannels(1)  # 单声道
            wav_file.setsampwidth(2)  # 16位采样
            wav_file.setframerate(result.sample_rate)
            wav_file.writeframes(result.audio_data)

        logger.info(f"WAV文件已保存到: {output_file}")

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
    finally:
        await tts.cleanup()


async def main():
    """主函数"""
    # 运行基本测试
    await test_tts_synthesize()

    # 运行带WAV头的测试
    await test_tts_with_wav_header()

    # 如果需要测试不同音色，注释取消下面这行
    # await test_different_voices()


if __name__ == "__main__":
    asyncio.run(main())
