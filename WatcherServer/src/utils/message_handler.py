"""WebSocket 消息处理器"""
import json
import re
from typing import Any
import websockets

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MessageHandler:
    """WebSocket 消息发送处理器"""

    # 消息类型
    class MsgType:
        ASR_RESULT = "asr_result"   # ASR 识别结果
        BOT_REPLY = "bot_reply"     # Bot 回复
        ERROR = "error"            # 系统错误
        STATUS = "status"          # 状态消息
        SERVO = "servo"            # 舵机控制
        TTS_END = "tts_end"        # TTS 音频结束
        SERVO_STATES = "servo_states"  # 可用舵机状态列表
        OPENCLAW_LOG = "openclaw_log"  # OpenClaw 实时日志

    # 错误码
    class Code:
        SUCCESS = 0        # 成功
        ERROR = 1          # 错误

    def __init__(self, websocket: websockets.WebSocketServerProtocol):
        """初始化消息处理器

        Args:
            websocket: WebSocket 连接对象
        """
        self.websocket = websocket

    @staticmethod
    def clean_text_for_tts(text: str) -> str:
        """清理文本中的 Markdown 符号和 emoji，适合 TTS 朗读

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        # 移除 Emoji - 使用字符类别而非范围，避免误伤中文
        # 移除各种常见的 emoji 字符
        emoji_chars = [
            '😊', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃',
            '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙',
            '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔',
            '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥',
            '😌', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮',
            '🤧', '🥵', '🥶', '🥴', '😵', '🤯', '🤠', '🥳', '🥸', '😎',
            '🤓', '🧐', '😕', '😟', '🙁', '☹️', '😮', '😯', '😲', '😳',
            '🥺', '😦', '😧', '😨', '😰', '😥', '😢', '😭', '😱', '😖',
            '😣', '😞', '😓', '😩', '😫', '🥱', '😤', '😡', '😠', '🤬',
            '😈', '👿', '💀', '☠️', '💩', '🤡', '👹', '👺', '👻', '👽',
            '👾', '🤖', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿',
            '😾', '🙈', '🙉', '🙊', '💋', '💌', '💘', '💝', '💖', '💗',
            '💓', '💞', '💕', '💟', '❣️', '💔', '❤', '🧡', '💛', '💚',
            '💙', '💜', '🤎', '🖤', '🤍', '💯', '💢', '💥', '💫', '💦',
            '💨', '🕳', '💣', '💬', '👁️‍🗨️', '🗨️', '🗯️', '💭', '💤',
            '🚀', '🚁', '🚂', '🚃', '🚄', '🚅', '🚆', '🚇', '🚈', '🚉',
            '🚊', '🚝', '🚞', '🚋', '🚌', '🚍', '🚎', '🚐', '🚑', '🚒',
            '🚓', '🚔', '🚕', '🚖', '🚗', '🚘', '🚙', '🛻', '🚚', '🚛',
            '🚜', '🏎️', '🏍️', '🛵', '🦽', '🦼', '🛺', '🚲', '🛴', '🛹',
            '🛼', '🚏', '🛣️', '🛤️', '🛢️', '⛽', '🚨', '🚥', '🚦',
            '🛑', '🚧', '⚓', '⛵', '🛶', '🚤', '🛳️', '⛴️', '🛥️', '🚢',
            '⚡', '⛄', '⛅', '⛈️', '🌤️', '⛱️', '🌥️', '☁️', '🌦️', '🌧️',
            '⛈️', '🌩️', '🌨️', '❄️', '☃️', '⛄', '🌬️', '💨', '💧', '💦',
            '☔', '☂️', '🌊', '⭐', '🌟', '💫', '✨', '🔥', '💥', '☀️',
            '🌤️', '☁️', '🌥️', '🌦️', '🌧️', '⛈️', '🌩️', '🌨️', '🌪️',
            '🌈', '🌂', '☂️', '⚡', '❄️', '☃️', '🌬️', '🎉', '🎊', '🎈',
            '🎁', '🏆', '🥇', '🥈', '🥉', '🎯', '🎳', '🎮', '🎰', '🧩',
            '♟️', '🎭', '🎨', '🎬', '🎤', '🎧', '🎼', '🎹', '🥁', '🪘',
            '🎷', '🎺', '🪗', '🎸', '🪕', '🎻', '🪈', '🎲', '♠️', '♣️',
            '♥️', '♦️', '🃏', '🎴', '🀄', '�🀄', '🏮', '🪔', '📣', '📢',
            '💬', '💭', '🗯️', '♠️', '♣️', '♥️', '♦️', '🗣️', '👤', '👥',
            '🗣️', '👋', '🤚', '🖐️', '✋', '🖖', '👌', '🤌', '🤏', '✌️',
            '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️',
            '👍', '👎', '✊', '👊', '🤛', '🤜', '👏', '🙌', '👐', '🤲',
            '🤝', '🙏', '✍️', '💅', '🤳', '💪', '🦾', '🦿', '🦵', '🦶',
            '👂', '🦻', '👃', '🧠', '🫀', '🫁', '🦷', '🦴', '👀', '👁️',
            '👅', '👄', '👶', '🧒', '👦', '👧', '🧑', '👱', '👨', '🧔',
            '👩', '🧓', '👴', '👵', '🙍', '🙎', '🙅', '🙆', '💁', '🙋',
            '🧏', '🙇', '🤦', '🤷', '👮', '🕵️', '💂', '🥷', '👷', '🤴',
            '👸', '👳', '👲', '🧕', '🤵', '👰', '🤰', '🤱', '👼', '🎅',
            '🤶', '🦸', '🦹', '🧙', '🧚', '🧛', '🧜', '🧝', '🧞', '🧟',
            '💆', '💇', '🚶', '🧍', '🧎', '🏃', '💃', '🕺', '🕴️', '👯',
            '🧖', '🧗', '🤸', '🏌️', '🏇', '⛷️', '🏂', '🏋️', '🤼', '🤽',
            '🤾', '🤺', '⛹️', '🏊', '🚣', '🧘', '🏄', '🏇', '🧗', '🛀',
            '🛌', '👭', '👫', '👬', '💏', '💑', '👪', '👨‍👩‍👦', '👨‍👩‍👧',
            '👨‍👩‍👧‍👦', '👨‍👩‍👦‍👦', '👨‍👩‍👧‍👧', '👨‍👩‍👧‍👦', '👨‍👩‍👧‍👧', '👨‍👩‍👦',
            '👨‍👩‍👧', '👨‍👩‍👧‍👦', '👨‍👩‍👦‍👦', '👨‍👩‍👧‍👧', '👨‍👩‍👦‍👦', '👨‍👩‍👧‍👧',
            '🗣️', '👤', '👥', '🗣️', '👣', '🌆', '🌇', '🌆', '🏙️', '🌃',
            '🌌', '🌠', '🌅', '🌄', '🏔️', '⛰️', '🌋', '🗻', '🏕️', '🏖️',
            '🏜️', '🏝️', '🏞️', '🏟️', '🏛️', '🏗️', '🧱', '🪨', '🪵', '🛖',
            '🏘️', '🏚️', '🏠', '🏡', '🏢', '🏣', '🏤', '🏥', '🏦', '🏨',
            '🏩', '🏪', '🏫', '🏬', '🏭', '🏯', '🏰', '💒', '🗼', '🗽',
            '⛪', '🕌', '🛕', '🕍', '⛩️', '🕋', '⛲', '⛺', '🌁', '🌃',
            '🏙️', '🌄', '🌅', '🌆', '🌇', '🌉', '♨️', '🎠', '🎡', '🎢',
            '💈', '🎪', '🚂', '🚃', '🚄', '🚅', '🚆', '🚇', '🚈', '🚉',
            '🚊', '🚝', '🚞', '🚋', '🚌', '🚍', '🚎', '🚐', '🚑', '🚒',
            '🚓', '🚔', '🚕', '🚖', '🚗', '🚘', '🚙', '🛻', '🚚', '🚛',
            '🚜', '🏎️', '🏍️', '🛵', '🦽', '🦼', '🛺', '🚲', '🛴', '🛹',
            '🛼', '🚏', '🛣️', '🛤️', '🛢️', '⛽', '🚨', '🚥', '🚦',
            '🛑', '🚧', '⚓', '⛵', '🛶', '🚤', '🛳️', '⛴️', '🛥️', '🚢',
            '🚤', '🛥️', '🛳️', '⛴️', '⚓', '⛽', '🚧', '🛑', '🚦', '🚥',
        ]

        for emoji in emoji_chars:
            text = text.replace(emoji, '')

        # 移除 Markdown 标题符号 (# ## ###)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

        # 移除加粗符号 (**text** -> text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

        # 移除斜体符号 (*text* -> text)，但要避免移除 ** 中的 *
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)

        # 先移除代码块 ``` ```，包括内容（必须在行内代码之前！）
        # 多次应用以处理多个代码块
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'```[\s\S]*?```', '', text)

        # 移除可能残留的三引号（未闭合的）
        text = re.sub(r'```[^`]*$', '', text, flags=re.MULTILINE)  # 开头的 ```
        text = re.sub(r'^```[^`]*', '', text, flags=re.MULTILINE)  # 结尾的 ```

        # 移除行内代码 (`code` -> code) - 必须在代码块之后处理
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # 移除残留的反引号（单独的反引号或连续的反引号，不是单词的一部分）
        # 移除连续的反引号 `` ``` 等
        text = re.sub(r'`{2,}', '', text)
        # 移除单独的反引号（前后是空白或行首行尾）
        text = re.sub(r'(?<!\S)`(?!\S)', '', text)

        # 清理代码块移除后留下的多余空行（2个以上换行变成1个）
        text = re.sub(r'\n\s*\n+', '\n', text)

        # 移除 Markdown 链接 [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # 移除列表符号
        text = re.sub(r'^[\s]*[-*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)

        # 移除分隔线 (---)
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)

        # 移除多余的空白字符
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格变成一个
        text = re.sub(r'\n{3,}', '\n\n', text)  # 多个换行变成两个

        text = text.strip()

        # 如果清理后为空，返回一个空格而不是空字符串
        # 避免 TTS 无法合成
        if not text:
            return " "

        return text

    async def send(
        self,
        msg_type: str,
        data: Any = None,
        code: int = 0,
    ) -> bool:
        """发送消息

        Args:
            msg_type: 消息类型
            data: 消息数据
            code: 错误码，0 表示成功

        Returns:
            bool: 发送是否成功
        """
        message = {
            "type": msg_type,
            "code": code,
            "data": data if data is not None else "",
        }

        try:
            await self.websocket.send(json.dumps(message, ensure_ascii=False))
            logger.debug(f"消息发送成功: type={msg_type}, code={code}")
            return True
        except Exception as e:
            logger.error(f"消息发送失败: type={msg_type}, error={e}")
            return False

    async def send_asr_result(self, text: str) -> bool:
        """发送 ASR 识别结果

        Args:
            text: 识别文本

        Returns:
            bool: 发送是否成功
        """
        return await self.send(self.MsgType.ASR_RESULT, text, self.Code.SUCCESS)

    async def send_bot_reply(self, text: str) -> bool:
        """发送 Bot 回复

        Args:
            text: 回复文本

        Returns:
            bool: 发送是否成功
        """
        return await self.send(self.MsgType.BOT_REPLY, text, self.Code.SUCCESS)

    async def send_error(self, error_msg: str) -> bool:
        """发送错误消息

        Args:
            error_msg: 错误信息

        Returns:
            bool: 发送是否成功
        """
        return await self.send(self.MsgType.ERROR, error_msg, self.Code.ERROR)

    async def send_info(self, info: str) -> bool:
        """发送状态信息

        Args:
            info: 信息内容

        Returns:
            bool: 发送是否成功
        """
        return await self.send(self.MsgType.STATUS, info, self.Code.SUCCESS)

    async def send_servo(self, data: dict = None) -> bool:
        """发送舵机控制指令

        Args:
            data: 舵机数据字典，支持两种格式:
                - 旧格式: {"x": angle} 或 {"y": angle}
                - 新格式: {"id": "x"/"y", "Angle": angle, "time": interval}

        Returns:
            bool: 发送是否成功
        """
        if not data:
            logger.warning("send_servo: data 为空")
            return False

        # 支持新格式: {"id": "x", "Angle": 90, "time": 0.033}
        if "id" in data and "Angle" in data:
            servo_data = {
                "id": data.get("id", ""),
                "Angle": max(0, min(180, int(data.get("Angle", 90)))),
                "time": data.get("time", 0)
            }
        # 支持旧格式: {"x": angle} 或 {"y": angle}
        elif "x" in data or "y" in data:
            servo_data = {}
            if "x" in data:
                servo_data["x"] = max(0, min(180, int(data.get("x", 90))))
            if "y" in data:
                servo_data["y"] = max(0, min(180, int(data.get("y", 90))))
            if not servo_data:
                logger.warning("send_servo: x 和 y 都无效")
                return False
        else:
            logger.warning(f"send_servo: 未知数据格式 {data}")
            return False

        return await self.send(self.MsgType.SERVO, servo_data, self.Code.SUCCESS)

    async def send_tts_end(self) -> bool:
        """发送 TTS 音频结束标记

        Returns:
            bool: 发送是否成功
        """
        return await self.send(self.MsgType.TTS_END, "ok", self.Code.SUCCESS)

    async def send_servo_states(self, states: list[str]) -> bool:
        """发送可用舵机状态列表

        Args:
            states: 可用的舵机状态名称列表

        Returns:
            bool: 发送是否成功
        """
        return await self.send(self.MsgType.SERVO_STATES, {"states": states}, self.Code.SUCCESS)

    async def send_openclaw_log(self, content: str, status: str = None) -> bool:
        """发送 OpenClaw 实时日志

        Args:
            content: 日志内容
            status: 当前执行状态 (thinking/processing)

        Returns:
            bool: 发送是否成功
        """
        data = {"content": content}
        if status:
            data["status"] = status
        return await self.send(self.MsgType.OPENCLAW_LOG, data, self.Code.SUCCESS)
