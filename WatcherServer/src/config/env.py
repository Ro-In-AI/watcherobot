"""环境变量配置"""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file_path() -> str:
    """获取.env文件路径"""
    # 从项目根目录查找.env文件
    current = Path(__file__).parent
    for _ in range(5):  # 最多向上5层
        env_file = current / ".env"
        if env_file.exists():
            return str(env_file)
        current = current.parent
    return ".env"  # 默认使用当前目录


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # WebSocket配置
    ws_host: str = Field(default="0.0.0.0", description="WebSocket服务地址")
    ws_port: int = Field(default=8765, description="WebSocket服务端口")
    ws_max_size: int = Field(default=10 * 1024 * 1024, description="WebSocket最大消息大小")

    # ASR配置
    asr_provider: str = Field(default="", description="ASR提供商")
    asr_sample_rate: int = Field(default=16000, description="ASR采样率")
    asr_channels: int = Field(default=1, description="ASR声道数")

    # 阿里云ASR配置
    aliyun_token: str = Field(default="", description="阿里云访问Token（临时Token，已废弃，请使用AK/SK）")
    aliyun_ak_id: str = Field(default="", description="阿里云AccessKeyId")
    aliyun_ak_secret: str = Field(default="", description="阿里云AccessKeySecret")
    aliyun_appkey: str = Field(default="", description="阿里云AppKey")
    aliyun_asr_url: str = Field(
        default="wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1",
        description="阿里云ASR网关URL"
    )
    aliyun_asr_enable_intermediate_result: bool = Field(
        default=True, description="是否返回中间结果"
    )
    aliyun_asr_enable_punctuation_prediction: bool = Field(
        default=True, description="是否进行标点预测"
    )
    aliyun_asr_enable_inverse_text_normalization: bool = Field(
        default=True, description="是否进行ITN转换"
    )

    # OpenClaw配置（本地CLI模式）
    openclaw_api_key: str = Field(default="", description="OpenClaw API密钥")
    openclaw_api_url: Optional[str] = Field(default=None, description="OpenClaw API地址")
    openclaw_model: str = Field(default="", description="OpenClaw模型名称")
    openclaw_agent: str = Field(default="main", description="OpenClaw Agent ID")
    openclaw_status_poll_interval: int = Field(default=3, description="OpenClaw状态轮询间隔（秒）")
    openclaw_prompt_file: str = Field(default="config/openclaw_prompt.txt", description="OpenClaw提示词文件路径")

    # LLM配置（用于精简思考内容）
    llm_provider: str = Field(default="ark", description="LLM提供商")
    llm_model: str = Field(default="deepseek-v3-2-251201", description="LLM模型名称")
    llm_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3", description="LLM API地址")
    llm_prompt_file: str = Field(default="config/llm_think_prompt.txt", description="LLM精简思考提示词文件路径")

    # TTS配置
    tts_provider: str = Field(default="", description="TTS提供商")
    tts_sample_rate: int = Field(default=16000, description="TTS采样率")
    tts_channels: int = Field(default=1, description="TTS声道数")

    # 火山引擎TTS配置
    huoshan_app_key: str = Field(default="", description="火山引擎App Key")
    huoshan_access_key: str = Field(default="", description="火山引擎Access Key")
    huoshan_voice_type: str = Field(default="", description="火山引擎声音类型")

    # 舵机配置
    servo_json_dir: str = Field(default="src/assets/JSON", description="舵机JSON动画文件目录")
    servo_frame_rate: int = Field(default=30, description="舵机帧率 (FPS)")

    # 服务发现配置
    discovery_enabled: bool = Field(default=True, description="是否启用服务发现")
    discovery_port: int = Field(default=37020, description="UDP发现端口")

    # 线程池配置
    thread_pool_max_workers: int = Field(default=10, description="线程池最大工作线程数")
    thread_pool_min_workers: int = Field(default=2, description="线程池最小工作线程数")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_dir: str = Field(default="logs", description="日志目录")
    log_max_bytes: int = Field(default=10 * 1024 * 1024, description="单个日志文件最大大小")
    log_backup_count: int = Field(default=5, description="日志备份数量")

    @property
    def log_path(self) -> Path:
        """日志目录路径"""
        return Path(self.log_dir)

    def get_openclaw_prompt(self) -> str:
        """加载 OpenClaw 提示词（带缓存）

        Returns:
            str: 提示词内容，如果加载失败返回默认提示词
        """
        # 如果已有缓存的值，直接返回
        if hasattr(self, '_cached_openclaw_prompt'):
            return self._cached_openclaw_prompt

        default_prompt = "请用简洁的纯文本回复，不要使用 Markdown 格式（如 #、**、*、` 等符号），不要使用列表，直接用自然段落回复。回复内容将用于语音合成。"
        config_prefix = "TTS_PROMPT="

        try:
            # 尝试从项目根目录查找配置文件
            current = Path(__file__).parent.parent.parent
            prompt_file = None

            for _ in range(5):
                candidate = current / self.openclaw_prompt_file
                if candidate.exists():
                    prompt_file = candidate
                    break
                current = current.parent

            if prompt_file:
                content = prompt_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith(config_prefix):
                        self._cached_openclaw_prompt = line.split("=", 1)[1].strip()
                        return self._cached_openclaw_prompt

            self._cached_openclaw_prompt = default_prompt
            return default_prompt
        except Exception as e:
            from src.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"加载OpenClaw提示词失败，使用默认: {e}")
            self._cached_openclaw_prompt = default_prompt
            return default_prompt

    def get_llm_think_prompt(self) -> str:
        """加载 LLM 精简思考提示词（带缓存）

        Returns:
            str: 提示词内容，如果加载失败返回默认提示词
        """
        # 如果已有缓存的值，直接返回
        if hasattr(self, '_cached_llm_think_prompt'):
            return self._cached_llm_think_prompt

        default_prompt = """你是一个智能助手的思考过程精简器。你的任务是将长篇的思考内容精简为简短、自然的语音播报内容。

规则：
1. 精简后的内容要简短，适合语音播报（不超过30字）
2. 保持思考的核心意图
3. 使用第一人称，像在和主人对话
4. 不要使用Markdown格式
5. 不要添加额外解释，直接输出精简后的内容

思考内容：
{think_content}

精简后："""

        config_prefix = "LLM_THINK_PROMPT="

        try:
            # 尝试从项目根目录查找配置文件
            current = Path(__file__).parent.parent.parent
            prompt_file = None

            for _ in range(5):
                candidate = current / self.llm_prompt_file
                if candidate.exists():
                    prompt_file = candidate
                    break
                current = current.parent

            if prompt_file:
                content = prompt_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith(config_prefix):
                        self._cached_llm_think_prompt = line.split("=", 1)[1].strip()
                        return self._cached_llm_think_prompt

            self._cached_llm_think_prompt = default_prompt
            return default_prompt
        except Exception as e:
            from src.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"加载LLM精简思考提示词失败，使用默认: {e}")
            self._cached_llm_think_prompt = default_prompt
            return default_prompt


# 全局配置实例
settings = Settings()
