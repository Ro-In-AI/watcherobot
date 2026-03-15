"""火山引擎实时语音合成实现"""
import asyncio
import gzip
import json
import uuid
from typing import Optional, AsyncIterator

import websockets
from websockets.protocol import State

from src.modules.tts.base import TTSProvider, TTSResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HuoshanTTS(TTSProvider):
    """火山引擎实时语音合成"""

    # 消息类型常量
    MESSAGE_TYPE_AUDIO = 0xb
    MESSAGE_TYPE_FRONTEND = 0xc
    MESSAGE_TYPE_ERROR = 0xf

    def __init__(
        self,
        app_key: str,
        access_key: str,
        voice_type: str = "ICL_zh_male_nuanxintitie_tob",
        host: str = "openspeech.bytedance.com",
        api_url: str = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary",
        sample_rate: int = 24000,  # 注意：火山引擎PCM默认采样率是24000Hz！
        encoding: str = "pcm",
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        pitch_ratio: float = 1.0,
    ):
        """初始化火山引擎TTS

        Args:
            app_key: App Key
            access_key: Access Key
            voice_type: 声音类型
            host: 主机地址
            api_url: API URL
            sample_rate: 采样率
            encoding: 音频编码格式
            speed_ratio: 语速比例
            volume_ratio: 音量比例
            pitch_ratio: 音调比例
        """
        super().__init__()

        self.app_key = app_key
        self.access_key = access_key
        self.voice_type = voice_type
        self.host = host
        self.api_url = api_url
        self.sample_rate = sample_rate
        self.encoding = encoding
        self.speed_ratio = speed_ratio
        self.volume_ratio = volume_ratio
        self.pitch_ratio = pitch_ratio

        # WebSocket连接
        self._ws: Optional[websockets.WebSocketClientProtocol] = None

        # 默认消息头 (protocol_version=1, message_type=1, serialization=1, compression=1)
        self._default_header = bytearray(b'\x11\x10\x11\x00')

        # 请求JSON模板
        self._request_template = {
            "app": {
                "appid": self.app_key,
                "token": "access_token",
                "cluster": "volcano_tts"
            },
            "user": {
                "uid": "watcher_server"
            },
            "audio": {
                "voice_type": self.voice_type,
                "encoding": self.encoding,
                "speed_ratio": self.speed_ratio,
                "volume_ratio": self.volume_ratio,
                "pitch_ratio": self.pitch_ratio,
            },
            "request": {
                "reqid": "",
                "text": "",
                "text_type": "plain",
                "operation": "submit"
            }
        }

        logger.info(
            f"火山引擎TTS初始化: app_key={app_key[:8] if app_key else ''}... "
            f"voice_type={voice_type} sample_rate={sample_rate}"
        )

    def set_voice_type(self, voice_type: str):
        """设置音色类型

        Args:
            voice_type: 音色类型
        """
        self.voice_type = voice_type
        logger.info(f"音色已设置为: {voice_type}")

    def set_speed_ratio(self, speed_ratio: float):
        """设置语速

        Args:
            speed_ratio: 语速比例 (0.5-2.0)
        """
        self.speed_ratio = speed_ratio

    def set_volume_ratio(self, volume_ratio: float):
        """设置音量

        Args:
            volume_ratio: 音量比例 (0.1-10.0)
        """
        self.volume_ratio = volume_ratio

    def set_pitch_ratio(self, pitch_ratio: float):
        """设置音调

        Args:
            pitch_ratio: 音调比例 (0.5-2.0)
        """
        self.pitch_ratio = pitch_ratio

    async def close_connection(self):
        """关闭WebSocket连接（下次请求时会自动重建）"""
        if self._ws:
            await self._ws.close()
            self._ws = None
            logger.info("TTS WebSocket连接已关闭")

    async def initialize(self):
        """初始化TTS引擎"""
        if self._is_initialized:
            logger.warning("火山引擎TTS已经初始化")
            return

        logger.info("初始化火山引擎TTS引擎...")
        self._is_initialized = True
        logger.info("火山引擎TTS引擎初始化完成")

    async def synthesize(self, text: str) -> TTSResult:
        """合成语音

        Args:
            text: 要合成的文本

        Returns:
            TTS合成结果
        """
        if not self._is_initialized:
            raise RuntimeError("TTS未初始化，请先调用initialize()")

        logger.info(f"开始TTS合成: {text[:50]}...")

        # 连接WebSocket
        await self._ensure_connection()

        # 发送请求并获取音频
        audio_data = await self._synthesize_text(text)

        # 计算音频时长（PCM格式：采样率 * 位深(2字节) * 通道数 * 秒数）
        duration = len(audio_data) / (self.sample_rate * 2) if self.encoding == "pcm" else None

        logger.info(f"TTS合成完成: audio_size={len(audio_data)} bytes, duration={duration}s")

        return TTSResult(
            audio_data=audio_data,
            format=self.encoding,
            sample_rate=self.sample_rate,
            duration=duration
        )

    async def synthesize_stream(self, text: str) -> AsyncIterator[TTSResult]:
        """流式合成语音，按句子分批合成并返回

        Args:
            text: 要合成的文本

        Yields:
            TTSResult: 每个句子的音频片段
        """
        if not self._is_initialized:
            raise RuntimeError("TTS未初始化，请先调用initialize()")

        # 按标点分句
        sentences = self.split_text_by_sentences(text, max_length=200)
        logger.info(f"文本已拆分为 {len(sentences)} 个句子")

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            logger.debug(f"流式合成第 {i+1}/{len(sentences)} 句: {sentence[:30]}...")

            # 确保连接有效
            await self._ensure_connection()

            # 合成当前句子
            audio_data = await self._synthesize_text(sentence)

            if audio_data:
                duration = len(audio_data) / (self.sample_rate * 2) if self.encoding == "pcm" else None
                logger.debug(f"第 {i+1} 句合成完成: audio_size={len(audio_data)} bytes")

                yield TTSResult(
                    audio_data=audio_data,
                    format=self.encoding,
                    sample_rate=self.sample_rate,
                    duration=duration
                )

    async def _ensure_connection(self):
        """确保WebSocket连接有效"""
        if self._ws is None or self._ws.state != State.OPEN:
            logger.info("创建火山引擎TTS WebSocket连接...")
            header = {"Authorization": f"Bearer; {self.access_key}"}
            self._ws = await websockets.connect(
                self.api_url,
                additional_headers=header,
                ping_interval=None
            )
            logger.info("火山引擎TTS WebSocket连接已建立")

    async def _synthesize_text(self, text: str) -> bytes:
        """发送文本请求并获取音频数据"""
        # 构建请求 - 每次都使用最新的配置
        request_json = {
            "app": {
                "appid": self.app_key,
                "token": "access_token",
                "cluster": "volcano_tts"
            },
            "user": {
                "uid": "watcher_server"
            },
            "audio": {
                "voice_type": self.voice_type,
                "encoding": self.encoding,
                "speed_ratio": self.speed_ratio,
                "volume_ratio": self.volume_ratio,
                "pitch_ratio": self.pitch_ratio,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "submit"
            }
        }

        logger.debug(f"TTS请求配置: voice_type={self.voice_type}, speed={self.speed_ratio}, volume={self.volume_ratio}, pitch={self.pitch_ratio}")

        # 序列化和压缩
        payload_bytes = json.dumps(request_json).encode('utf-8')
        payload_bytes = gzip.compress(payload_bytes)

        # 构建完整请求
        full_request = bytearray(self._default_header)
        full_request.extend(len(payload_bytes).to_bytes(4, 'big'))
        full_request.extend(payload_bytes)

        # 发送请求
        await self._ws.send(full_request)

        # 接收响应
        audio_chunks = []

        while True:
            response = await self._ws.recv()
            done, audio_data = await self._parse_response(response)

            if audio_data:
                audio_chunks.append(audio_data)

            if done:
                break

        # 合并音频数据
        return b''.join(audio_chunks)

    async def _parse_response(self, response: bytes) -> tuple[bool, Optional[bytes]]:
        """解析服务器响应

        Returns:
            (is_done, audio_data): 是否完成, 音频数据
        """
        # 解析响应头部
        protocol_version = response[0] >> 4
        header_size = response[0] & 0x0f
        message_type = response[1] >> 4
        message_type_specific_flags = response[1] & 0x0f
        serialization_method = response[2] >> 4
        message_compression = response[2] & 0x0f
        reserved = response[3]
        header_extensions = response[4:header_size * 4]
        payload = response[header_size * 4:]

        if message_type == self.MESSAGE_TYPE_AUDIO:
            # 音频数据
            if message_type_specific_flags == 0:
                # 无序列号作为ACK
                return False, None

            sequence_number = int.from_bytes(payload[:4], "big", signed=True)
            audio_payload = payload[8:]  # 跳过序列号(4字节)和负载大小(4字节)

            is_done = sequence_number < 0
            return is_done, audio_payload

        elif message_type == self.MESSAGE_TYPE_ERROR:
            # 错误消息
            code = int.from_bytes(payload[:4], "big", signed=False)
            msg_size = int.from_bytes(payload[4:8], "big", signed=False)
            error_msg = payload[8:]

            if message_compression == 1:
                error_msg = gzip.decompress(error_msg)

            error_text = error_msg.decode("utf-8")
            logger.error(f"火山引擎TTS错误: code={code}, message={error_text}")
            raise RuntimeError(f"TTS错误: {error_text}")

        elif message_type == self.MESSAGE_TYPE_FRONTEND:
            # 前端消息
            msg_size = int.from_bytes(payload[:4], "big", signed=False)
            frontend_msg = payload[4:]
            if message_compression == 1:
                frontend_msg = gzip.decompress(frontend_msg)
            logger.debug(f"前端消息: {frontend_msg.decode('utf-8')}")
            return False, None

        else:
            logger.warning(f"未知的消息类型: {message_type}")
            return True, None

    async def cleanup(self):
        """清理资源"""
        logger.info("清理火山引擎TTS资源...")

        if self._ws:
            await self._ws.close()
            self._ws = None

        self._is_initialized = False
        logger.info("火山引擎TTS资源清理完成")
