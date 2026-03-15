"""Watcher Server 主入口"""
import asyncio
import signal

from src.config import settings
from src.core.websocket_server import WebSocketServer
from src.core.thread_pool import shutdown_thread_pool
from src.utils.logger import setup_logger, get_logger


# 配置日志
setup_logger()
logger = get_logger(__name__)


class WatcherServer:
    """Watcher Server 主服务"""

    def __init__(self):
        """初始化服务"""
        self.ws_server: WebSocketServer = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """初始化所有模块"""
        logger.info("开始初始化Watcher Server...")

        # 初始化ASR提供商
        asr_provider = self._create_asr_provider()
        if asr_provider:
            await asr_provider.initialize()
            logger.info("ASR提供商初始化成功")
        else:
            logger.warning("未配置ASR提供商或创建失败")

        # TODO: 初始化OpenClaw提供商
        # openclaw_provider = self._create_openclaw_provider()
        # await openclaw_provider.initialize()

        # TODO: 初始化TTS提供商
        # tts_provider = self._create_tts_provider()
        # await tts_provider.initialize()

        # 创建WebSocket服务器
        self.ws_server = WebSocketServer(
            host=settings.ws_host,
            port=settings.ws_port,
            asr_provider=asr_provider,
            openclaw_provider=None,  # openclaw_provider,
            tts_provider=None,  # tts_provider,
        )

        logger.info("Watcher Server初始化完成")

    async def start(self):
        """启动服务"""
        logger.info("启动Watcher Server...")
        await self.ws_server.start()

    async def stop(self):
        """停止服务"""
        logger.info("停止Watcher Server...")
        if self.ws_server:
            await self.ws_server.stop()

        # 清理ASR资源
        if self.ws_server and self.ws_server.asr_provider:
            await self.ws_server.asr_provider.cleanup()
            logger.info("ASR资源已清理")

        # 关闭线程池
        shutdown_thread_pool()

        logger.info("Watcher Server已停止")

    def _create_asr_provider(self):
        """创建ASR提供商实例"""
        from src.modules.asr.factory import ASRFactory

        try:
            return ASRFactory.create_provider()
        except Exception as e:
            logger.error(f"创建ASR提供商失败: {e}", exc_info=True)
            return None

    def _create_openclaw_provider(self):
        """创建OpenClaw提供商实例

        TODO: 根据配置创建具体的OpenClaw实现
        """
        pass

    def _create_tts_provider(self):
        """创建TTS提供商实例

        TODO: 根据配置创建具体的TTS实现
        """
        pass


async def main():
    """主函数"""
    server = WatcherServer()

    # 设置信号处理
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("收到退出信号，正在优雅关闭...")
        server._shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # 初始化并启动服务
        await server.initialize()
        await server.start()
    except asyncio.CancelledError:
        logger.info("任务被取消")
    finally:
        # 清理资源
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
