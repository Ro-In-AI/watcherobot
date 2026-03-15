# WebSocket 服务器上下文

> **最后更新**: 2026-03-04
> **主要实现**: WebSocketServer

## 模块概述

WebSocket 服务器是 Watcher Server 的核心组件，负责：
1. 处理客户端连接
2. 接收音频流并进行语音识别
3. 调用 AI 对话服务
4. 返回 TTS 音频
5. 同步舵机控制指令
6. 管理多个客户端连接

## 文件结构

```
src/core/
├── __init__.py
└── websocket_server.py      # WebSocketServer 实现
```

## 核心类

### WebSocketServer

**文件**: [src/core/websocket_server.py](../../src/core/websocket_server.py)

#### 初始化参数

```python
WebSocketServer(
    host: str = "0.0.0.0",              # 服务地址
    port: int = 8765,                   # 服务端口
    asr_provider: ASRProvider = None,   # ASR 提供商
    openclaw_provider: OpenClawProvider = None,  # OpenClaw 提供商
    tts_provider: TTSProvider = None,   # TTS 提供商
)
```

#### 工作流程

```
1. start()                    → 启动服务器
2. _initialize_providers()    → 初始化所有服务提供商
3. handle_client()            → 处理客户端连接
4. _process_audio_stream()    → 处理音频流
5. stop()                     → 停止服务器
```

#### 音频处理流程

```
客户端音频流 (二进制)
    ↓
ASR.process_audio()
    ↓
客户端发送 "over"
    ↓
ASR.stop() + get_final_result()
    ↓
返回 ASR 结果给客户端
    ↓
OpenClaw.chat() 获取 AI 回复
    ↓
返回 AI 回复给客户端
    ↓
TTS.synthesize_stream() 流式合成
    ↓
发送 TTS 音频 (二进制)
    ↓
发送 tts_end 标记
    ↓
ASR.reset() 重置状态
```

### 关键组件

#### MessageHandler

**文件**: [src/utils/message_handler.py](../../src/utils/message_handler.py)

负责发送消息给客户端：

```python
class MessageHandler:
    async def send_asr_result(self, text: str)
    async def send_bot_reply(self, text: str)
    async def send_error(self, error_msg: str)
    async def send_info(self, info: str)
    async def send_servo(self, x: int = None, y: int = None)
    async def send_tts_end(self)
    async def send_servo_states(self, states: list[str])

    @staticmethod
    def clean_text_for_tts(text: str) -> str
```

#### MessageReceiver

**文件**: [src/utils/message_receiver.py](../../src/utils/message_receiver.py)

负责接收和处理客户端消息（用于舵机控制等）。

#### ServoController

**文件**: [src/modules/servo/controller.py](../../src/modules/servo/controller.py)

负责舵机动画控制（详见 [舵机模块上下文](servo_context.md)）。

## 消息处理

### 客户端消息类型

**二进制消息**：音频数据（PCM 格式）

**文本消息**：

| 类型 | 格式 | 处理方式 |
|------|------|----------|
| `"over"` | 字符串 | 结束音频识别 |
| `{"type": "servo", ...}` | JSON | 舵机控制 |
| `{"type": "state", ...}` | JSON | 独占播放舵机动画 |

### 舵机控制消息

**循环播放**：
```json
{"type": "servo", "action": "start", "state": "speech_nod", "broadcast": false}
{"type": "servo", "action": "stop"}
{"type": "servo", "action": "set_tts_servo", "state": "watcher_animation"}
```

**独占播放**：
```json
{"type": "state", "data": "speech_nod"}
```

### 服务端消息类型

| 类型 | 说明 | data 格式 |
|------|------|-----------|
| `asr_result` | ASR 识别结果 | 识别文本 |
| `bot_reply` | AI 回复 | 回复文本 |
| `status` | 状态消息 | 状态描述 |
| `servo` | 舵机控制 | `{"x": 90}` 或 `{"y": 45}` |
| `tts_end` | TTS 音频结束 | "ok" |
| `servo_states` | 可用舵机状态 | `{"states": [...]}` |
| `error` | 错误消息 | 错误描述 |

## 配置

### 环境变量

```bash
# WebSocket 服务配置
WS_HOST=0.0.0.0
WS_PORT=8765
WS_MAX_SIZE=10485760  # 10MB
```

### 舵机相关配置

```python
# TTS 播放时使用的舵机动画状态（前端可控制）
self.tts_servo_state = "watcher_animation"

# 可用舵机状态列表
servo_states = self.servo_controller.get_available_states()
```

## 连接管理

### 多客户端支持

```python
# 连接集合
self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()

# 新连接
self.connected_clients.add(websocket)

# 连接关闭
self.connected_clients.discard(websocket)
```

### 舵机数据广播

```python
async def _broadcast_servo(self, x: int = None, y: int = None):
    """广播舵机数据到所有已连接的客户端"""
    message = {"type": "servo", "code": 0, "data": servo_data}

    for client in self.connected_clients:
        try:
            await client.send(json.dumps(message))
        except Exception as e:
            failed_clients.add(client)

    # 移除失败的客户端
    for client in failed_clients:
        self.connected_clients.discard(client)
```

## 使用示例

### 基本使用

```python
# main.py
from src.core.websocket_server import WebSocketServer
from src.modules.asr.aliyun_asr import AliyunASR
from src.modules.openclaw.local_claw import LocalOpenClawProvider
from src.modules.tts.huoshan_tts import HuoshanTTS

# 创建服务提供商
asr_provider = AliyunASR(...)
openclaw_provider = LocalOpenClawProvider(...)
tts_provider = HuoshanTTS(...)

# 创建 WebSocket 服务器
server = WebSocketServer(
    host="0.0.0.0",
    port=8765,
    asr_provider=asr_provider,
    openclaw_provider=openclaw_provider,
    tts_provider=tts_provider,
)

# 启动服务器
await server.start()
```

### 客户端连接流程

```javascript
// 1. 连接服务器
const ws = new WebSocket('ws://localhost:8765');

// 2. 发送音频数据
async function sendAudio(audioData) {
    ws.send(audioData);  // 二进制数据
}

// 3. 发送结束标记
ws.send('over');

// 4. 接收识别结果
ws.onmessage = (event) => {
    if (typeof event.data === 'string') {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
            case 'asr_result':
                console.log('识别结果:', msg.data);
                break;
            case 'bot_reply':
                console.log('AI 回复:', msg.data);
                break;
            case 'servo':
                handleServoData(msg.data);
                break;
            case 'tts_end':
                console.log('TTS 完成');
                break;
        }
    } else {
        // 二进制数据 = TTS 音频
        playAudio(event.data);
    }
};
```

## OpenClaw 集成

### 状态回调

```python
# 创建 OpenClaw 客户端（带状态回调）
async def on_status_change(status: str, data: dict):
    await msg_handler.send_info(f"[{status}] {data.get('message', '')}")

openclaw_client = LocalOpenClawProvider(
    on_status_change=on_status_change
)
await openclaw_client.initialize()
```

### 提示词加载

```python
# 从配置文件加载提示词
tts_prompt = settings.get_openclaw_prompt()

# 发送聊天请求
response = await openclaw_client.chat([
    ChatMessage(role="system", content=tts_prompt),
    ChatMessage(role="user", content=recognized_text)
])
```

## TTS 集成

### 文本清理

```python
# 清理 Markdown 符号
text_to_speak = MessageHandler.clean_text_for_tts(bot_reply_text)
```

### 流式合成 + 舵机同步

```python
async for tts_result in self.tts_provider.synthesize_stream(text_to_speak):
    # 首个音频块时启动舵机动画
    if first_chunk:
        await self.servo_controller.start(self.tts_servo_state, loop=True)
        first_chunk = False

    # 发送音频数据
    await websocket.send(tts_result.audio_data)

# 停止舵机动画
await self.servo_controller.stop()
await msg_handler.send_tts_end()
```

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| ASR 未配置 | asr_provider 为 None | 检查 main.py 配置 |
| ASR 初始化失败 | Token 无效或网络问题 | 检查 ASR 配置 |
| OpenClaw 初始化失败 | CLI 或 Gateway 未运行 | `openclaw gateway start` |
| TTS 初始化失败 | App Key 无效 | 检查 TTS 配置 |

### 错误处理示例

```python
try:
    await self.asr_provider.initialize()
except Exception as e:
    logger.error(f"ASR 初始化失败: {e}")
    await msg_handler.send_error(f"ASR 初始化失败 - {str(e)}")
    return
```

## 清理资源

```python
# finally 块中清理
finally:
    # 清理 OpenClaw 客户端
    if openclaw_client:
        await openclaw_client.cleanup()

    # 重置 ASR 状态
    await self.asr_provider.reset()
```

## 最近修改记录

- **2026-03-04**: 添加舵机状态广播功能
- **2026-03-04**: 支持 TTS 舵机动画状态动态设置
- **2026-03-04**: 改进错误处理和日志

---

**注意**: 修改此模块后，请更新本文档的"最近修改记录"部分。
