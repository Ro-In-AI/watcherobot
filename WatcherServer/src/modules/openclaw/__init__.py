"""OpenClaw模块 - AI对话"""
import shutil
from typing import Callable, Optional

from .base import OpenClawProvider, ChatMessage, ChatResponse
from .local_claw import LocalOpenClawProvider

# 尝试导入 TMUX 实现
try:
    from .tmux_claw import TmuxOpenClawProvider
    _TMUX_AVAILABLE = True
except ImportError:
    TmuxOpenClawProvider = None
    _TMUX_AVAILABLE = False


def is_tmux_available() -> bool:
    """检测系统是否支持 tmux

    Returns:
        bool: tmux 是否可用
    """
    if not _TMUX_AVAILABLE:
        return False
    return shutil.which("tmux") is not None


def create_openclaw_provider(
    agent: str = "main",
    poll_interval: int = 3,
    log_poll_interval: int = 2,
    prefer_tmux: bool = True,
    on_status_change: Optional[Callable[[str, dict], None]] = None,
    on_log: Optional[Callable[[str, str], None]] = None,
) -> OpenClawProvider:
    """创建 OpenClaw 提供商实例

    自动检测并选择合适的实现：
    - prefer_tmux=True 且 tmux 可用: TmuxOpenClawProvider
    - 其他情况: LocalOpenClawProvider

    Args:
        agent: Agent ID
        poll_interval: 状态轮询间隔（秒）
        log_poll_interval: 日志轮询间隔（秒），仅 TMUX 方式有效
        prefer_tmux: 是否优先使用 tmux 方式
        on_status_change: 状态变化回调
        on_log: 日志回调，参数: (log_content, current_status)，仅 TMUX 方式有效

    Returns:
        OpenClawProvider: OpenClaw 提供商实例
    """
    if prefer_tmux and is_tmux_available():
        logger = _get_logger()
        logger.info("使用 TMUX 方式连接 OpenClaw")
        return TmuxOpenClawProvider(
            agent=agent,
            poll_interval=poll_interval,
            log_poll_interval=log_poll_interval,
            on_status_change=on_status_change,
            on_log=on_log,
        )
    else:
        if prefer_tmux and not is_tmux_available():
            logger = _get_logger()
            logger.warning("tmux 不可用，回退到 CLI 方式")

        return LocalOpenClawProvider(
            agent=agent,
            poll_interval=poll_interval,
            on_status_change=on_status_change,
        )


def _get_logger():
    """获取日志记录器"""
    from src.utils.logger import get_logger
    return get_logger(__name__)


__all__ = [
    "OpenClawProvider",
    "ChatMessage",
    "ChatResponse",
    "LocalOpenClawProvider",
    "TmuxOpenClawProvider",
    "create_openclaw_provider",
    "is_tmux_available",
]
