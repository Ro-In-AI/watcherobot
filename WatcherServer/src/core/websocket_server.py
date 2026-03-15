"""WebSocket 服务器 - 核心处理流程"""
import asyncio
import json
from typing import Optional, Set
import websockets

from src.config import settings
from src.utils.logger import get_logger
from src.utils.message_handler import MessageHandler
from src.modules.asr.base import ASRProvider
from src.modules.openclaw.base import OpenClawProvider, ChatMessage
from src.modules.tts.base import TTSProvider
from src.modules.servo.controller import ServoController
from src.modules.discovery.discovery_server import DiscoveryServer

logger = get_logger(__name__)


class WebSocketServer:
    """WebSocket 服务器"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        asr_provider: ASRProvider = None,
        openclaw_provider: OpenClawProvider = None,
        tts_provider: TTSProvider = None,
    ):
        self.host = host or settings.ws_host
        self.port = port or settings.ws_port
        self.asr_provider = asr_provider
        self.openclaw_provider = openclaw_provider
        self.tts_provider = tts_provider

        # 连接管理
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()

        # 服务器实例
        self.server: Optional[websockets.WebSocketServer] = None

        # 舵机控制器（全局共享）
        self.servo_controller = ServoController()

        # 服务发现服务器
        self.discovery_server: Optional[DiscoveryServer] = None

        logger.info(f"WebSocket服务器初始化: {self.host}:{self.port}")

    # ==================== 核心流程 ====================

    async def start(self):
        """启动服务器"""
        logger.info(f"启动WebSocket服务器: ws://{self.host}:{self.port}")

        # 预初始化所有模块
        await self._initialize_providers()

        # 加载舵机动画
        await self.servo_controller.load_animations()
        logger.info(f"可用舵机状态: {self.servo_controller.get_available_states()}")

        # 启动服务发现服务器
        if settings.discovery_enabled:
            self.discovery_server = DiscoveryServer(ws_port=self.port)
            await self.discovery_server.start()

        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            max_size=settings.ws_max_size,
        ) as server:
            self.server = server
            logger.info("WebSocket服务器启动成功")
            await asyncio.Future()

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """处理客户端连接"""
        client_id = id(websocket)
        logger.info(f"新客户端连接: {client_id}")
        self.connected_clients.add(websocket)

        # 创建会话处理器
        session = AudioSessionHandler(
            websocket=websocket,
            asr_provider=self.asr_provider,
            openclaw_provider=self.openclaw_provider,
            tts_provider=self.tts_provider,
            servo_controller=self.servo_controller,
            connected_clients=self.connected_clients,
        )

        try:
            await session.run()
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"客户端断开连接: {client_id}")
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 时发生错误: {e}", exc_info=True)
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"客户端连接关闭: {client_id}")

    # ==================== 初始化 ====================

    async def _initialize_providers(self):
        """初始化所有服务提供商"""
        logger.info("开始初始化所有服务提供商...")

        for name, provider in [
            ("ASR", self.asr_provider),
            ("OpenClaw", self.openclaw_provider),
            ("TTS", self.tts_provider),
        ]:
            if provider:
                try:
                    await provider.initialize()
                    logger.info(f"{name} 初始化完成")
                except Exception as e:
                    logger.error(f"{name} 初始化失败: {e}")

        logger.info("所有服务提供商初始化完成")

    async def stop(self):
        """停止服务器"""
        logger.info("正在停止WebSocket服务器...")

        # 停止服务发现服务器
        if self.discovery_server:
            await self.discovery_server.stop()

        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("WebSocket服务器已停止")

    def get_connected_count(self) -> int:
        return len(self.connected_clients)


class AudioSessionHandler:
    """音频会话处理器 - 处理单个客户端的完整会话流程"""

    def __init__(
        self,
        websocket: websockets.WebSocketServerProtocol,
        asr_provider: ASRProvider,
        openclaw_provider: OpenClawProvider,
        tts_provider: TTSProvider,
        servo_controller: ServoController,
        connected_clients: Set[websockets.WebSocketServerProtocol],
    ):
        self.ws = websocket
        self.msg_handler = MessageHandler(websocket)
        self.asr = asr_provider
        self.openclaw = openclaw_provider
        self.tts = tts_provider
        self.servo = servo_controller
        self.connected_clients = connected_clients

        # 状态标志
        self.openclaw_enabled = openclaw_provider and openclaw_provider.is_initialized
        self.tts_enabled = tts_provider and tts_provider.is_initialized

        # TTS 播放时使用的舵机动画状态
        self.tts_servo_state = "watcher_animation"

    async def run(self):
        """运行会话主循环"""
        # 初始化 ASR
        await self._ensure_asr_ready()

        # 发送可用舵机状态列表
        await self._send_servo_states()

        # 接收消息循环
        async for message in self.ws:
            msg_type = type(message).__name__
            logger.debug(f"收到消息: type={msg_type}, is_bytes={isinstance(message, bytes)}, is_str={isinstance(message, str)}")
            if isinstance(message, bytes):
                logger.debug(f"音频数据大小: {len(message)} bytes")
                await self._handle_audio(message)
            elif isinstance(message, str):
                logger.debug(f"文本消息内容: {message}")
                await self._handle_text(message)
            else:
                logger.warning(f"未知消息类型: {msg_type}")

    # ==================== 消息处理 ====================

    async def _handle_audio(self, audio_data: bytes):
        """处理音频数据"""
        try:
            await self.asr.process_audio(audio_data)
        except Exception as e:
            logger.error(f"ASR处理音频失败: {e}", exc_info=True)
            await self.msg_handler.send_error(f"ASR processing failed - {str(e)}")

    async def _handle_text(self, message: str):
        """处理文本消息"""
        logger.info(f"收到文本消息: {message}")

        # 1. 尝试解析 JSON 消息
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "servo":
                await self._handle_servo_message(data)
                return
        except json.JSONDecodeError:
            pass

        # 2. 处理 "over" 结束标记
        if message == "over":
            logger.info("收到 over 消息，准备结束会话")
            await self._handle_session_end()
            return

        # 3. 其他文本消息（忽略或日志）
        logger.debug(f"收到文本消息: {message}")

    # ==================== 舵机控制 ====================

    async def _handle_servo_message(self, data: dict):
        """处理舵机控制消息"""
        action = data.get("action")
        state = data.get("state")
        broadcast = data.get("broadcast", False)

        # 设置发送回调
        if broadcast:
            await self._setup_servo_broadcast_callback()
        else:
            await self._setup_servo_callback(self.msg_handler.send_servo)

        if action == "start" and state:
            play_once = data.get("play_once", False)
            if play_once:
                await self.servo.play_once(state)
                await self.msg_handler.send_info(f"Servo animation played once: {state}")
            else:
                await self.servo.start(state, loop=True)
                self.tts_servo_state = state
                await self.msg_handler.send_info(f"Servo animation started: {state}")

        elif action == "stop":
            await self.servo.stop()
            await self.msg_handler.send_info("Servo animation stopped")

        elif action == "set_tts_servo":
            if state and state in self.servo.get_available_states():
                self.tts_servo_state = state
                await self.msg_handler.send_info(f"TTS servo state set to: {state}")
            else:
                await self.msg_handler.send_error(f"Invalid servo state: {state}")

    async def _setup_servo_callback(self, send_func):
        """设置舵机发送回调（单客户端）"""
        async def send_servo(frames=None):
            if frames:
                for frame in frames:
                    await send_func(frame)
        self.servo.set_send_callback(send_servo)

    async def _setup_servo_broadcast_callback(self):
        """设置舵机广播回调（所有客户端）"""
        async def broadcast_servo(frames=None):
            if frames:
                await self._broadcast_servo(frames)
        self.servo.set_send_callback(broadcast_servo)

    async def _broadcast_servo(self, frames: list):
        """广播舵机数据帧到所有客户端"""
        for frame in frames:
            servo_data = {}
            frame_id = frame.get("id", "")
            angle = frame.get("Angle")

            if angle is not None:
                angle = max(0, min(180, int(angle)))
                servo_data["id"] = frame_id
                servo_data["Angle"] = angle
                servo_data["time"] = frame.get("time", 0)

            if not servo_data:
                continue

            message = {
                "type": "servo",
                "code": 0,
                "data": servo_data,
            }
            message_str = json.dumps(message, ensure_ascii=False)

            failed = set()
            for client in self.connected_clients:
                try:
                    await client.send(message_str)
                except Exception as e:
                    logger.error(f"广播失败: {e}")
                    failed.add(client)

            for client in failed:
                self.connected_clients.discard(client)

    # ==================== 会话结束处理 ====================

    async def _handle_session_end(self):
        """处理会话结束（收到 'over' 标记）"""
        logger.info("=" * 60)
        logger.info("开始处理会话结束")
        logger.info("=" * 60)

        # 1. 停止 ASR 获取结果
        try:
            logger.info("正在停止 ASR...")
            await self.asr.stop()
            logger.info("ASR 已停止，正在获取结果...")
            result = await self.asr.get_final_result()
            recognized_text = result.text
            logger.info(f"识别结果已获取: {recognized_text}")
        except Exception as e:
            logger.error(f"获取识别结果失败: {e}", exc_info=True)
            await self.msg_handler.send_error(f"Recognition failed - {str(e)}")
            return

        # 发送识别结果
        logger.info(f"发送识别结果: {recognized_text}")
        await self.msg_handler.send_asr_result(recognized_text)

        # 2. 调用 AI 对话
        bot_reply = None
        if self.openclaw_enabled and recognized_text:
            logger.info("开始调用 AI 对话...")
            bot_reply = await self._call_ai(recognized_text)

        # 3. TTS 语音合成
        text_to_speak = bot_reply or recognized_text
        if self.tts_enabled and text_to_speak:
            logger.info("开始 TTS 语音合成...")
            await self._synthesize_and_play(text_to_speak)

        # 4. 重置 ASR 准备下一次
        try:
            logger.info("重置 ASR 状态...")
            await self.asr.reset()
        except Exception as e:
            logger.error(f"重置ASR失败: {e}")

        logger.info("会话处理完成")

    async def _call_ai(self, text: str) -> Optional[str]:
        """调用 AI 对话服务"""
        try:
            logger.info("调用 AI 对话...")

            # 状态回调
            async def on_status_change(status: str, data: dict):
                await self.msg_handler.send_info(f"[{status}] {data.get('message', '')}")

            # 日志回调 (Session 方式)
            # log_type: thinking, tool_call, tool_result, text
            async def on_log(content: str, log_type: str):
                # 添加前缀标识
                prefix = {
                    'thinking': '🤔',
                    'tool_call': '🔧',
                    'tool_result': '📤',
                    'text': '💬'
                }.get(log_type, '')
                await self.msg_handler.send_openclaw_log(f"{prefix} {content}", log_type)

            # 使用工厂函数创建客户端（自动选择 CLI 或 TMUX 方式）
            from src.modules.openclaw import create_openclaw_provider
            openclaw_client = create_openclaw_provider(
                agent=settings.openclaw_agent,
                on_status_change=on_status_change,
                on_log=on_log,
            )
            await openclaw_client.initialize()

            # 获取提示词
            prompt = settings.get_openclaw_prompt()

            # 调用对话（添加 5 分钟超时）
            logger.info("开始等待 AI 回复...")
            try:
                response = await asyncio.wait_for(
                    openclaw_client.chat([
                        ChatMessage(role="system", content=prompt),
                        ChatMessage(role="user", content=text),
                    ]),
                    timeout=300.0  # 5 分钟超时
                )
            except asyncio.TimeoutError:
                logger.error("AI 对话超时（5分钟）")
                await self.msg_handler.send_error("AI chat timeout (5 minutes)")
                await openclaw_client.cleanup()
                return None

            await openclaw_client.cleanup()

            bot_reply = response.content
            await self.msg_handler.send_bot_reply(bot_reply)
            logger.debug(f"AI 回复: {bot_reply}")
            logger.info(f"AI 回复: {bot_reply[:50]}...")
            return bot_reply

        except Exception as e:
            logger.error(f"AI 对话失败: {e}", exc_info=True)
            await self.msg_handler.send_error(f"AI chat failed - {str(e)}")
            return None

    async def _synthesize_and_play(self, text: str):
        """TTS 语音合成并播放"""
        # 清理文本
        clean_text = self.msg_handler.clean_text_for_tts(text)
        logger.debug(f"TTS 原始文本: {text}")
        logger.debug(f"TTS 清理后文本: {clean_text}")
        logger.info(f"TTS 文本: {clean_text[:50]}...")

        # 设置发送回调
        async def send_servo(frames=None):
            if frames:
                for frame in frames:
                    servo_data = {
                        "id": frame.get("id", ""),
                        "Angle": frame.get("Angle"),
                        "time": frame.get("time", 0)
                    }
                    await self.msg_handler.send_servo(servo_data)
        self.servo.set_send_callback(send_servo)

        try:
            # 流式合成
            first_chunk = True
            async for tts_result in self.tts.synthesize_stream(clean_text):
                # 第一块音频时启动舵机动画
                if first_chunk:
                    await self.servo.start(self.tts_servo_state, loop=True)
                    first_chunk = False

                # 发送音频
                await self.ws.send(tts_result.audio_data)

            # 停止舵机动画
            await self.servo.stop()
            await self.msg_handler.send_tts_end()
            logger.info("TTS 播放完成")

        except Exception as e:
            logger.error(f"TTS 合成失败: {e}", exc_info=True)
            await self.msg_handler.send_error(f"TTS failed - {str(e)}")

    # ==================== 初始化辅助 ====================

    async def _ensure_asr_ready(self):
        """确保 ASR 已就绪"""
        if not self.asr:
            await self.msg_handler.send_error("ASR not configured")
            raise RuntimeError("ASR not configured")

        if not self.asr.is_initialized:
            try:
                await self.asr.initialize()
            except Exception as e:
                await self.msg_handler.send_error(f"ASR init failed - {str(e)}")
                raise

    async def _send_servo_states(self):
        """发送可用舵机状态列表"""
        states = self.servo.get_available_states()
        if states:
            await self.msg_handler.send_servo_states(states)
            logger.info(f"已发送舵机状态: {states}")
