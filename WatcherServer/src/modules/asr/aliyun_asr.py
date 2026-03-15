"""阿里云实时语音识别实现"""
import asyncio
import json
import threading
import time
from typing import Optional
from queue import Queue

try:
    import nls
    NLS_AVAILABLE = True
except ImportError:
    NLS_AVAILABLE = False

# 阿里云 SDK 用于获取 Token
try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
    ALIYUN_SDK_AVAILABLE = True
except ImportError:
    ALIYUN_SDK_AVAILABLE = False

from src.modules.asr.base import ASRProvider, ASRResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_aliyun_token(ak_id: str, ak_secret: str) -> Optional[tuple[str, int]]:
    """使用阿里云SDK获取Token

    Args:
        ak_id: AccessKeyId
        ak_secret: AccessKeySecret

    Returns:
        (token, expire_time) 或 None
    """
    if not ALIYUN_SDK_AVAILABLE:
        logger.error("阿里云SDK未安装，请运行: pip install aliyun-python-sdk-core")
        return None

    try:
        client = AcsClient(ak_id, ak_secret, "cn-shanghai")

        request = CommonRequest()
        request.set_method('POST')
        request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
        request.set_version('2019-02-28')
        request.set_action_name('CreateToken')

        response = client.do_action_with_exception(request)
        result = json.loads(response)

        if 'Token' in result and 'Id' in result['Token']:
            token = result['Token']['Id']
            expire_time = result['Token']['ExpireTime']
            logger.info(f"成功获取阿里云Token，过期时间: {expire_time}")
            return (token, expire_time)
        else:
            logger.error(f"获取Token失败，响应: {result}")
            return None

    except Exception as e:
        logger.error(f"获取阿里云Token异常: {e}")
        return None


class AliyunASR(ASRProvider):
    """阿里云实时语音识别"""

    def __init__(
        self,
        appkey: str,
        token: str = "",
        url: str = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1",
        sample_rate: int = 16000,
        channels: int = 1,
        enable_intermediate_result: bool = True,
        enable_punctuation_prediction: bool = True,
        enable_inverse_text_normalization: bool = True,
        language: str = "zh-CN",
        # 新增：AK/SK 方式获取 Token
        ak_id: str = "",
        ak_secret: str = "",
    ):
        super().__init__()

        if not NLS_AVAILABLE:
            raise ImportError(
                "阿里云SDK未安装，请运行: pip install alibabacloud-nls-python-sdk"
            )

        self.appkey = appkey
        self.url = url
        self.sample_rate = sample_rate
        self.channels = channels
        self.enable_intermediate_result = enable_intermediate_result
        self.enable_punctuation_prediction = enable_punctuation_prediction
        self.enable_inverse_text_normalization = enable_inverse_text_normalization
        self.language = language

        # AK/SK 方式获取 Token
        self.ak_id = ak_id
        self.ak_secret = ak_secret
        self._token = token  # 内部 token 存储
        self._token_expire_time = 0  # Token 过期时间戳
        self._token_refresh_buffer = 300  # 提前 5 分钟刷新 Token

        # 如果提供了 AK/SK，优先使用
        if ak_id and ak_secret:
            self._refresh_token()
        elif token:
            # 兼容旧的直接传入 token 方式
            self._token = token
            self._token_expire_time = 0  # 不知道过期时间，不自动刷新

        # 识别器实例
        self._transcriber: Optional[nls.NlsSpeechTranscriber] = None

        # 后台线程（持续运行 transcriber.start()）
        self._session_thread: Optional[threading.Thread] = None

        # 结果队列和事件
        self._result_queue: Queue = Queue()
        self._result_event: threading.Event = threading.Event()
        self._current_text: str = ""
        self._is_started: bool = False

        # 启动会话事件：等待 SDK 内部 __start_flag 设置完成后才 set
        # 见 __transcription_started：先触发 on_start 回调，再设置 __start_flag
        # 所以我们在 on_start 回调里 sleep 一小段后再 set，确保 __start_flag 已就绪
        self._session_ready_event: threading.Event = threading.Event()
        self._start_success: bool = False

        # 连接失败重试控制
        self._last_connect_failure_time: float = 0
        self._connect_retry_delay: float = 2.0

        # 发送速率限制
        self._last_send_time: float = 0
        self._min_send_interval: float = 0.15

        # 回调参数
        self._callback_args: list = []

        # 日志输出
        auth_mode = "AK/SK" if (ak_id and ak_secret) else "Token"
        logger.info(
            f"阿里云ASR初始化: appkey={appkey[:8]}..., "
            f"sample_rate={sample_rate}, channels={channels}, language={language}, "
            f"auth={auth_mode}"
        )
        logger.info("提示: 语言模型需要在阿里云控制台的AppKey项目中配置")

    def _refresh_token(self) -> bool:
        """刷新 Token（使用 AK/SK）

        Returns:
            bool: 刷新是否成功
        """
        if not self.ak_id or not self.ak_secret:
            logger.warning("未配置 AK/SK，无法刷新 Token")
            return False

        result = get_aliyun_token(self.ak_id, self.ak_secret)
        if result:
            self._token, self._token_expire_time = result
            logger.info(f"Token 刷新成功，过期时间: {self._token_expire_time}")
            return True
        else:
            logger.error("Token 刷新失败")
            return False

    def _get_valid_token(self) -> Optional[str]:
        """获取有效的 Token（如果需要则自动刷新）

        Returns:
            有效的 Token 或 None
        """
        current_time = time.time()

        # 检查是否需要刷新 Token
        # 1. 没有 token
        # 2. 知道过期时间且快过期了（提前 5 分钟）
        if not self._token:
            if not self._refresh_token():
                return None
        elif self._token_expire_time > 0:
            if current_time > (self._token_expire_time - self._token_refresh_buffer):
                logger.info("Token 即将过期，尝试刷新...")
                if not self._refresh_token():
                    # 刷新失败但旧 token 还能用
                    pass

        return self._token

    async def initialize(self):
        """初始化ASR引擎"""
        if self._is_initialized:
            logger.warning("阿里云ASR已经初始化")
            return

        logger.info("初始化阿里云ASR引擎...")
        self._is_initialized = True
        logger.info("阿里云ASR引擎初始化完成")

    def _create_transcriber(self) -> nls.NlsSpeechTranscriber:
        """创建语音识别器实例"""
        # 获取有效 Token（自动刷新）
        token = self._get_valid_token()
        if not token:
            raise RuntimeError("无法获取有效的阿里云 Token")

        return nls.NlsSpeechTranscriber(
            url=self.url,
            token=token,
            appkey=self.appkey,
            on_start=self._on_start,
            on_sentence_begin=self._on_sentence_begin,
            on_sentence_end=self._on_sentence_end,
            on_result_changed=self._on_result_changed,
            on_completed=self._on_completed,
            on_error=self._on_error,
            on_close=self._on_close,
            callback_args=self._callback_args,
        )

    def _on_start(self, message: str, *args):
        """识别开始回调。

        重要：SDK 内部在调用本回调之后才会设置 __start_flag = True（见 __transcription_started）。
        如果我们在这里立刻 set _session_ready_event，主线程可能会在 __start_flag 尚未置位前
        调用 send_audio，导致 send_audio 内部判断 __start_flag==False 直接 return（返回 None）。
        因此这里用一个短暂的 sleep，等 SDK 完成 __start_flag 的设置后再通知主线程。
        """
        try:
            data = json.loads(message) if isinstance(message, str) else message
            logger.info(f"阿里云ASR识别会话开始: {data.get('name', 'unknown')}")
        except Exception:
            logger.info("阿里云ASR识别会话开始")

        self._is_started = True
        self._start_success = True
        self._last_connect_failure_time = 0

        # 等待 SDK 在本回调返回后将 __start_flag 置为 True
        # SDK 源码: on_start(message) → __start_flag = True（紧接在回调之后）
        # 短暂 sleep 确保时序正确，之后 send_audio 才能成功
        time.sleep(0.05)
        self._session_ready_event.set()

    def _on_sentence_begin(self, message: str, *args):
        logger.debug(f"ASR on_sentence_begin: {message}")

    def _on_sentence_end(self, message: str, *args):
        """句子结束回调 - 累积所有句子的识别结果"""
        logger.debug(f"ASR on_sentence_end: {message}")
        try:
            data = json.loads(message) if isinstance(message, str) else message
            # result 在 payload 里面
            payload = data.get("payload", {})
            result = payload.get("result", "")
            if result:
                # 累积所有句子的识别结果到 _current_text
                if self._current_text:
                    self._current_text += result
                else:
                    self._current_text = result
                logger.debug(f"句子识别完成: {result}")
        except Exception as e:
            logger.warning(f"解析句子结束消息失败: {e}")

    def _on_result_changed(self, message: str, *args):
        """中间结果回调 - 只记录日志，不更新 _current_text

        当启用中间结果时，中间结果会不断变化。
        最终结果应该从 SentenceEnd 事件中累积获取，避免重复。
        """
        logger.debug(f"ASR on_result_changed: {message}")
        try:
            data = json.loads(message) if isinstance(message, str) else message
            payload = data.get("payload", {})
            result = payload.get("result", "")
            if result:
                # 只记录日志，不更新 _current_text
                # 最终结果从 SentenceEnd 事件中获取，避免中间结果和句子结果重复
                logger.debug(f"中间识别结果: {result}")
        except Exception as e:
            logger.warning(f"解析中间结果失败: {e}")

    def _on_completed(self, message: str, *args):
        logger.debug(f"ASR on_completed: {message}")
        try:
            # 使用累积的文本，而不是从消息中解析
            # TranscriptionCompleted 事件本身不包含文本，文本在 SentenceEnd 事件中累积
            text = self._current_text

            self._result_queue.put({
                "text": text,
                "is_final": True,
                "status": "completed"
            })
            self._result_event.set()
            logger.debug(f"识别完成: {text}")

        except Exception as e:
            logger.error(f"解析完成结果失败: {e}", exc_info=True)

    def _on_error(self, message: str, *args):
        logger.error(f"ASR on_error: {message}")
        try:
            data = json.loads(message) if isinstance(message, str) else message
            error_msg = data.get("message", "Unknown error")
            status_text = data.get("status_text", "")

            if "TOO_MANY_REQUESTS" in status_text or "40000005" in str(data.get("status", "")):
                logger.warning("检测到QPS限制错误，增加重试延迟")
                self._connect_retry_delay = min(self._connect_retry_delay * 2, 30)

            self._result_queue.put({
                "text": "",
                "is_final": True,
                "status": "error",
                "error": error_msg
            })
            self._result_event.set()

        except Exception as e:
            logger.error(f"解析错误消息失败: {e}")

        self._start_success = False
        self._is_started = False
        self._last_connect_failure_time = time.time()
        if not self._session_ready_event.is_set():
            self._session_ready_event.set()

    def _on_close(self, *args):
        logger.info(f"ASR on_close: args={args}")
        self._is_started = False

    async def _start_session(self) -> bool:
        """在独立后台线程启动识别会话，异步等待 _on_start 回调确认连接就绪。

        SDK 的 transcriber.start() 是阻塞调用，会一直阻塞到会话完全结束，
        因此必须在独立后台线程中运行，主协程只等待 _session_ready_event。
        """
        self._session_ready_event.clear()
        self._start_success = False
        self._is_started = False

        def _run():
            try:
                self._transcriber = self._create_transcriber()
                self._transcriber.start(
                    aformat="pcm",
                    sample_rate=self.sample_rate,
                    ch=self.channels,
                    enable_intermediate_result=self.enable_intermediate_result,
                    enable_punctuation_prediction=self.enable_punctuation_prediction,
                    enable_inverse_text_normalization=self.enable_inverse_text_normalization,
                    timeout=10,
                )
                logger.debug("阿里云ASR后台线程：start() 已返回，会话结束")
            except Exception as e:
                logger.error(f"阿里云ASR后台线程异常: {e}", exc_info=True)
                self._start_success = False
                self._is_started = False
                self._last_connect_failure_time = time.time()
                if not self._session_ready_event.is_set():
                    self._session_ready_event.set()

        self._session_thread = threading.Thread(target=_run, daemon=True, name="AliyunASR-Session")
        self._session_thread.start()

        # 只等 _session_ready_event，不等线程结束
        loop = asyncio.get_event_loop()
        ready = await loop.run_in_executor(
            None,
            lambda: self._session_ready_event.wait(timeout=10)
        )

        if not ready:
            logger.error("等待阿里云ASR会话就绪超时（10s内未收到服务端确认）")
            self._start_success = False
            self._last_connect_failure_time = time.time()
            return False

        if self._start_success:
            logger.info("阿里云ASR会话启动成功，可以开始发送音频")
        else:
            logger.error("阿里云ASR会话启动失败（收到错误回调）")

        return self._start_success

    async def process_audio(self, audio_data: bytes) -> ASRResult:
        """处理音频数据"""
        if not self._is_initialized:
            raise RuntimeError("ASR未初始化，请先调用initialize()")

        if not self._is_started or self._transcriber is None:
            success = await self._start_session()
            if not success:
                return ASRResult(
                    text="",
                    confidence=0.0,
                    is_final=True,
                    timestamp=time.time()
                )

        # 速率限制
        current_time = time.time()
        time_since_last_send = current_time - self._last_send_time
        if time_since_last_send < self._min_send_interval:
            await asyncio.sleep(self._min_send_interval - time_since_last_send)

        # 发送音频：SDK 的 send_audio 成功时返回 None（无返回值），失败时抛异常或直接 return
        # 因此用 try/except 判断，而不是判断返回值是否为 True
        def _send_audio():
            try:
                if not self._transcriber:
                    logger.error("发送音频失败：transcriber 为 None")
                    return False

                # 检查 SDK 内部状态
                if hasattr(self._transcriber, '_NlsSpeechTranscriber__start_flag'):
                    if not self._transcriber._NlsSpeechTranscriber__start_flag:
                        logger.warning("SDK __start_flag 为 False，可能还未就绪")
                        return False

                result = self._transcriber.send_audio(audio_data)
                return True
            except Exception as e:
                logger.error(f"发送音频数据异常: {e}", exc_info=True)
                return False

        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, _send_audio)

        if success:
            self._last_send_time = time.time()
        else:
            logger.error("发送音频数据失败")
            return ASRResult(
                text="",
                confidence=0.0,
                is_final=False,
                timestamp=time.time()
            )

        return ASRResult(
            text=self._current_text,
            confidence=0.9,
            is_final=False,
            timestamp=time.time()
        )

    async def get_final_result(self) -> ASRResult:
        """获取最终识别结果（在调用stop()后使用）"""

        def _wait_result():
            try:
                if not self._result_event.wait(timeout=10):
                    logger.warning("等待识别结果超时")
                    return {"text": "", "is_final": True, "status": "timeout"}
                if not self._result_queue.empty():
                    return self._result_queue.get()
                return {"text": self._current_text, "is_final": True, "status": "completed"}
            except Exception as e:
                logger.error(f"获取最终结果失败: {e}", exc_info=True)
                return {"text": "", "is_final": True, "status": "error", "error": str(e)}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _wait_result)

        return ASRResult(
            text=result.get("text", ""),
            confidence=0.9 if result.get("status") == "completed" else 0.0,
            is_final=True,
            timestamp=time.time()
        )

    async def reset(self):
        """重置ASR状态，用于新的会话"""
        if self._is_started:
            await self.stop()

        self._current_text = ""
        self._is_started = False
        self._start_success = False
        self._result_event.clear()
        self._session_ready_event.clear()
        self._last_connect_failure_time = 0
        self._connect_retry_delay = 2.0
        self._last_send_time = 0
        self._session_thread = None

        while not self._result_queue.empty():
            try:
                self._result_queue.get_nowait()
            except Exception:
                break

        logger.debug("阿里云ASR状态已重置")

    async def stop(self):
        """停止当前识别会话"""
        if not self._is_started or self._transcriber is None:
            return

        def _stop():
            try:
                result = self._transcriber.stop(timeout=10)
                logger.info(f"阿里云ASR会话停止: {result}")
                return result
            except Exception as e:
                logger.error(f"停止阿里云ASR会话异常: {e}", exc_info=True)
                return False

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _stop)

        self._is_started = False

        if self._session_thread and self._session_thread.is_alive():
            await loop.run_in_executor(None, lambda: self._session_thread.join(timeout=5))

    async def cleanup(self):
        """清理资源"""
        logger.info("清理阿里云ASR资源...")

        await self.stop()

        if self._transcriber:
            def _shutdown():
                try:
                    self._transcriber.shutdown()
                    logger.info("阿里云ASR识别器已关闭")
                except Exception as e:
                    logger.error(f"关闭识别器失败: {e}")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _shutdown)
            self._transcriber = None

        self._session_thread = None
        self._is_initialized = False
        logger.info("阿里云ASR资源清理完成")
