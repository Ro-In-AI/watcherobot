"""OpenClaw 本地 CLI 实现"""
import asyncio
import json
import time
from typing import List, Optional, Callable

from src.modules.openclaw.base import OpenClawProvider, ChatMessage, ChatResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LocalOpenClawProvider(OpenClawProvider):
    """OpenClaw 本地 CLI 实现"""

    # 状态类型
    class Status:
        IDLE = "idle"             # 空闲
        THINKING = "thinking"     # 思考中
        PROCESSING = "processing" # 处理中
        COMPLETED = "completed"   # 完成
        ERROR = "error"          # 错误

    def __init__(
        self,
        agent: str = "main",
        poll_interval: int = 3,
        on_status_change: Callable[[str, dict], None] = None
    ):
        """初始化

        Args:
            agent: Agent ID
            poll_interval: 状态轮询间隔（秒）
            on_status_change: 状态变化回调，参数: (status, extra_data)，可以是 sync 或 async 函数
        """
        super().__init__()
        self.agent = agent
        self.poll_interval = poll_interval
        self.on_status_change = on_status_change

    async def _call_status_callback(self, status: str, data: dict):
        """调用状态回调（处理 sync 和 async 两种情况）

        Args:
            status: 状态
            data: 数据
        """
        import inspect

        if self.on_status_change:
            try:
                # 检查是否是 async 函数
                if inspect.iscoroutinefunction(self.on_status_change):
                    # 是 async 函数，直接 await
                    await self.on_status_change(status, data)
                else:
                    # 同步函数直接调用
                    self.on_status_change(status, data)
            except Exception as e:
                logger.warning(f"状态回调调用失败: {e}")

    async def initialize(self):
        """初始化 OpenClaw 客户端

        检查 OpenClaw CLI 和 Gateway 是否可用
        """
        logger.info("初始化 OpenClaw 本地客户端...")

        # 检查 CLI 可用性
        try:
            proc = await asyncio.create_subprocess_exec(
                "openclaw", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode != 0:
                raise RuntimeError("OpenClaw CLI 不可用")

        except FileNotFoundError:
            raise RuntimeError("未找到 openclaw 命令，请确保已安装 OpenClaw")

        # 检查 Gateway 状态
        try:
            proc = await asyncio.create_subprocess_exec(
                "openclaw", "gateway", "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode()

            if "running" not in output.lower():
                raise RuntimeError("OpenClaw Gateway 未运行，请运行: openclaw gateway start")

        except Exception as e:
            raise RuntimeError(f"OpenClaw Gateway 检查失败: {e}")

        self._is_initialized = True
        logger.info("OpenClaw 本地客户端初始化完成")

    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """发送聊天请求

        Args:
            messages: 消息列表
            model: 模型名称（可选）
            **kwargs: 其他参数

        Returns:
            ChatResponse: 聊天响应
        """
        if not self._is_initialized:
            raise RuntimeError("OpenClaw 未初始化，请先调用 initialize()")

        # 提取最后一条用户消息
        user_message = None
        for msg in reversed(messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if not user_message:
            raise ValueError("User message not found")

        # Send status callback: start processing
        await self._call_status_callback(self.Status.THINKING, {"message": "Thinking..."})

        try:
            # 启动聊天任务
            result = await self._chat_with_status(user_message)
            logger.debug(f"CLI 返回完整数据: {result}")

            # 提取回复内容 - 兼容三种返回格式
            # 格式1: result.status == "ok" 且 result.result.payloads
            # 格式2: result.status == "ok" 且 result.payloads (没有 result 字段)
            # 格式3: 没有 status 字段，但有 payloads (如 {'payloads': [...], 'meta': {...}})
            content = ""
            usage = {}
            model = ""
            # 优先使用 result 字段，兼容没有 result 的情况
            result_data = result.get("result", result)
            payloads = result_data.get("payloads", [])
            # 如果没有 payloads，尝试从根层级获取（格式3）
            if not payloads and "payloads" in result:
                payloads = result.get("payloads", [])

            if payloads:
                content = payloads[0].get("text", "")

            # model 在 agentMeta 里面
            agent_meta = result_data.get("meta", {})
            if not agent_meta and "meta" in result:
                agent_meta = result.get("meta", {})
            agent_meta = agent_meta.get("agentMeta", {})
            usage = agent_meta.get("usage", {})
            model = agent_meta.get("model", "")

            # 发送状态回调：完成
            await self._call_status_callback(self.Status.COMPLETED, {"content": content[:100]})

            return ChatResponse(
                content=content,
                model=model or "unknown",
                finish_reason="stop",
                usage=usage
            )

        except Exception as e:
            # 发送状态回调：错误
            await self._call_status_callback(self.Status.ERROR, {"error": str(e)})
            raise

    async def _chat_with_status(self, message: str) -> dict:
        """带状态跟踪的聊天

        Args:
            message: 用户消息

        Returns:
            dict: 响应结果
        """
        start_time = time.time()
        last_updated = int(time.time() * 1000)

        # 启动聊天任务
        proc = await asyncio.create_subprocess_exec(
            "openclaw", "agent",
            "--agent", self.agent,
            "--message", message,
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        timeout = None  # 不设置超时，允许长时间运行
        last_status = None  # 记录上次发送的状态，避免重复发送

        # 等待进程启动
        await asyncio.sleep(0.5)

        # 轮询状态直到完成
        while True:
            # 检查超时（如果设置了超时）
            if timeout and time.time() - start_time > timeout:
                proc.kill()
                raise TimeoutError(f"聊天超时（{timeout}秒）")

            # 查询状态
            try:
                status = await self._get_session_status()
                if status:
                    age = status.get("age", 0)

                    # 根据 age 判断状态
                    if age < 5000:
                        current_status = self.Status.THINKING
                    else:
                        current_status = self.Status.PROCESSING

                    # Only send callback when status changes
                    if current_status != last_status:
                        last_status = current_status
                        await self._call_status_callback(
                            current_status,
                            {"message": "Processing...", "age": age}
                        )

            except Exception as e:
                logger.warning(f"轮询状态失败: {e}")

            await asyncio.sleep(self.poll_interval)

            # 检查进程是否已完成
            if proc.returncode is not None:
                break

        # 获取结果
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"OpenClaw 调用失败: {error_msg}")

        return json.loads(stdout)

    async def _get_session_status(self) -> dict:
        """获取 Session 状态

        Returns:
            dict: Session 状态
        """
        proc = await asyncio.create_subprocess_exec(
            "openclaw", "gateway", "call", "status",
            "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return {}

        result = json.loads(stdout)
        sessions = result.get("sessions", {}).get("recent", [])

        return sessions[0] if sessions else {}

    async def cleanup(self):
        """清理资源"""
        self._is_initialized = False
        logger.info("OpenClaw 本地客户端已清理")
