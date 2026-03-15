# TTS 模块上下文

> **最后更新**: 2026-03-04
> **主要实现**: HuoshanTTS (火山引擎语音合成)

## 模块概述

TTS (Text-to-Speech) 模块负责将文本转换为语音音频。当前使用火山引擎（字节跳动）实时语音合成服务。

## 文件结构

```
src/modules/tts/
├── __init__.py
├── base.py              # TTSProvider 抽象基类
└── huoshan_tts.py       # HuoshanTTS 实现
```

## 核心类

### TTSProvider (抽象基类)

**文件**: [src/modules/tts/base.py](../../src/modules/tts/base.py)

定义了 TTS 提供商的统一接口：

```python
class TTSProvider(ABC):
    @abstractmethod
    async def initialize(self): ...

    @abstractmethod
    async def synthesize(self, text: str) -> TTSResult: ...

    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncIterator[TTSResult]: ...

    @abstractmethod
    async def cleanup(self): ...
```

### HuoshanTTS

**文件**: [src/modules/tts/huoshan_tts.py](../../src/modules/tts/huoshan_tts.py)

#### 初始化参数

```python
HuoshanTTS(
    app_key: str,                              # App Key（必填）
    access_key: str,                           # Access Key（必填）
    voice_type: str = "ICL_zh_male_nuanxintitie_tob",  # 声音类型
    host: str = "openspeech.bytedance.com",
    api_url: str = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary",
    sample_rate: int = 24000,                  # 采样率（默认24000Hz）
    encoding: str = "pcm",                     # 音频编码
    speed_ratio: float = 1.0,                  # 语速比例
    volume_ratio: float = 1.0,                 # 音量比例
    pitch_ratio: float = 1.0,                  # 音调比例
)
```

#### 重要参数说明

**采样率**:
- 火山引擎 PCM 默认采样率是 **24000 Hz**（不是常见的 16000 Hz）
- 如需其他采样率，需要在服务端转换

**声音类型**:

| 声音类型 | 描述 |
|----------|------|
| `zh_female_qiaopinvsheng_mars_bigtts` | 俏皮女声 |
| `zh_female_wenroushunv_mars_bigtts` | 温柔女声 |
| `ICL_zh_female_zhixingwenwan_tob` | 知性温婉 |
| `ICL_zh_male_nuanxintitie_tob` | 暖心体贴（默认） |
| `ICL_zh_female_huopodiaoman_tob` | 活泼刁蛮 |
| `ICL_zh_female_aomanjiaosheng_tob` | 傲慢娇声 |
| `ICL_zh_female_jiaohannvwang_tob` | 娇憨女王 |
| `ICL_zh_female_bingjiaomengmei_tob` | 病娇萌妹 |
| `ICL_zh_female_nuanxinxuejie_tob` | 暖心学姐 |
| `zh_female_linjianvhai_moon_bigtts` | 邻家女孩 |
| `zh_female_wenrouxiaoya_moon_bigtts` | 温柔小雅 |
| `ICL_zh_male_hanhoudunshi_tob` | 憨厚敦实 |
| `ICL_zh_male_youmoshushu_tob` | 幽默叔叔 |
| `ICL_zh_male_guzhibingjiao_tob` | 固执病娇 |
| `ICL_zh_male_yourogongzi_tob` | 幽柔公子 |
| `ICL_zh_male_tiexinnanyou_tob` | 贴心男友 |

#### 动态配置方法

```python
# 设置音色
tts.set_voice_type("zh_female_wenroushunv_mars_bigtts")

# 设置语速 (0.5-2.0)
tts.set_speed_ratio(1.2)

# 设置音量 (0.1-10.0)
tts.set_volume_ratio(1.5)

# 设置音调 (0.5-2.0)
tts.set_pitch_ratio(1.1)
```

#### 工作流程

```
1. initialize()           → 初始化 TTS 引擎
2. synthesize(text)       → 一次性合成完整文本
   或
   synthesize_stream(text) → 流式合成（按句子分批）

3. cleanup()              → 清理资源（程序退出时）
```

#### 关键实现细节

**WebSocket 二进制协议**：

火山引擎使用自定义二进制协议，消息格式：

```
+--------+--------+--------+--------+----------------+------------------+
| 协议版本 | 头大小  | 消息类型 | 序列化  | 保留字段  | 头扩展(可选)     |
| (4bit) | (4bit) | (4bit) | (4bit) | (4bit) | (4bit) | (变长)          |
+--------+--------+--------+--------+--------+--------+------------------+
| 负载长度 (4 bytes, big endian)                                  |
+--------------------------------------------------------------+
| 负载 (gzip 压缩的 JSON)                                        |
+--------------------------------------------------------------+
```

默认消息头：`\x11\x10\x11\x00`
- 协议版本: 1
- 头大小: 1
- 消息类型: 1 (请求)
- 序列化: 1 (JSON)
- 压缩: 1 (gzip)

**消息类型**：

| 类型值 | 说明 |
|--------|------|
| `0xb` | 音频数据 |
| `0xc` | 前端消息 |
| `0xf` | 错误消息 |

**流式合成**：

文本按标点符号分句，每句单独合成：

```python
async def synthesize_stream(self, text: str) -> AsyncIterator[TTSResult]:
    sentences = self.split_text_by_sentences(text, max_length=200)
    for sentence in sentences:
        audio_data = await self._synthesize_text(sentence)
        yield TTSResult(audio_data=audio_data, ...)
```

**连接复用**：

WebSocket 连接在请求间保持，失败时自动重建：

```python
async def _ensure_connection(self):
    if self._ws is None or self._ws.state != State.OPEN:
        header = {"Authorization": f"Bearer; {self.access_key}"}
        self._ws = await websockets.connect(self.api_url, additional_headers=header)
```

## 配置

### 环境变量

```bash
# TTS 配置
TTS_PROVIDER=huoshan
TTS_SAMPLE_RATE=24000
TTS_CHANNELS=1

# 火山引擎 TTS 配置
HUOSHAN_APP_KEY=xxx              # App Key（必填）
HUOSHAN_ACCESS_KEY=xxx           # Access Key（必填）
HUOSHAN_VOICE_TYPE=ICL_zh_male_nuanxintitie_tob  # 声音类型
```

### 获取 App Key 和 Access Key

1. 访问 [火山引擎控制台](https://console.volcengine.com/speech/service)
2. 创建应用并获取 App Key 和 Access Key

## 使用示例

### 基本使用

```python
from src.modules.tts.huoshan_tts import HuoshanTTS

# 创建 TTS 实例
tts = HuoshanTTS(
    app_key="your_app_key",
    access_key="your_access_key",
    voice_type="ICL_zh_male_nuanxintitie_tob",
)

# 初始化
await tts.initialize()

# 一次性合成
result = await tts.synthesize("你好，世界")
audio_data = result.audio_data  # PCM 格式音频
sample_rate = result.sample_rate  # 24000

# 流式合成
async for chunk in tts.synthesize_stream("你好，这是一段较长的文本。"):
    audio_data = chunk.audio_data
    # 处理音频片段...

# 清理资源
await tts.cleanup()
```

### 在 WebSocket 服务中使用

```python
# websocket_server.py

# 清理 Markdown 符号
text_to_speak = clean_text_for_tts(bot_reply_text)

# 流式合成并发送
async for tts_result in tts_provider.synthesize_stream(text_to_speak):
    # 发送音频数据（二进制）
    await websocket.send(tts_result.audio_data)

# 发送结束标记
await msg_handler.send_tts_end()
```

## 音频格式

- **格式**: PCM（无压缩）
- **采样率**: 24000 Hz（火山引擎默认）
- **位深**: 16-bit
- **声道**: 单声道

### 音频播放

```javascript
// Web Audio API 播放
const audioContext = new AudioContext({ sampleRate: 24000 });
const audioBuffer = audioContext.createBuffer(1, audioData.length / 2, 24000);
const channelData = audioBuffer.getChannelData(0);

// 转换字节到 Float32
for (let i = 0; i < audioData.length / 2; i++) {
    const sample = (audioData[i * 2 + 1] << 8) | audioData[i * 2];
    channelData[i] = sample < 0 ? sample / 32768 : sample / 32767;
}

const source = audioContext.createBufferSource();
source.buffer = audioBuffer;
source.connect(audioContext.destination);
source.start();
```

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| 认证失败 | App Key 或 Access Key 错误 | 检查配置 |
| 音色不存在 | voice_type 配置错误 | 使用正确的声音类型 |
| WebSocket 连接失败 | 网络问题或服务不可用 | 检查网络连接 |
| 文本为空 | 输入空字符串 | 过滤空输入 |

### 错误消息解析

```python
elif message_type == self.MESSAGE_TYPE_ERROR:
    code = int.from_bytes(payload[:4], "big", signed=False)
    msg_size = int.from_bytes(payload[4:8], "big", signed=False)
    error_msg = payload[8:]

    if message_compression == 1:
        error_msg = gzip.decompress(error_msg)

    error_text = error_msg.decode("utf-8")
    raise RuntimeError(f"TTS错误: {error_text}")
```

## 依赖

```txt
websockets  # WebSocket 客户端
```

## 文本预处理

在发送到 TTS 前，建议清理 Markdown 符号：

```python
from src.utils.message_handler import MessageHandler

# 清理 Markdown 符号
clean_text = MessageHandler.clean_text_for_tts(text)
```

清理内容包括：
- 标题符号 (`#`)
- 加粗 (`**text**`)
- 斜体 (`*text*`)
- 行内代码 (` `` ` ``)
- 代码块
- 列表符号
- 分隔线

## 最近修改记录

- **2026-03-04**: 初始版本，实现火山引擎 TTS

---

**注意**: 修改此模块后，请更新本文档的"最近修改记录"部分。
