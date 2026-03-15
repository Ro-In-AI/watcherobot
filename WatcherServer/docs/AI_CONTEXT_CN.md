[English](AI_CONTEXT.md) | [中文](AI_CONTEXT_CN.md)

# Watcher Server - AI 上下文文档

> **最后更新**: 2026-03-04
> **项目状态**: 活跃开发中

## 项目概述

**Watcher Server** 是一个基于 WebSocket 的语音对话服务器，为智能硬件（如机器人）提供语音交互能力。服务器接收客户端音频流，进行实时语音识别（ASR），调用 AI 对话服务，并返回语音合成（TTS）音频和舵机控制指令。

### 核心功能

1. **实时语音识别 (ASR)** - 支持阿里云实时语音识别
2. **AI 对话** - 通过 OpenClaw 本地 CLI 进行 AI 对话
3. **语音合成 (TTS)** - 支持火山引擎 TTS
4. **舵机控制** - 读取 JSON 动画文件并按时间轴发送舵机角度数据
5. **状态同步** - 实时同步 AI 思考状态、舵机动画状态等

### 技术栈

- **语言**: Python 3.10+
- **异步框架**: asyncio
- **WebSocket**: websockets
- **配置管理**: pydantic-settings
- **日志系统**: loguru
- **环境管理**: Conda

---

## 项目结构

```
watcher-server/
├── main.py                          # 服务入口
├── requirements.txt                 # Python 依赖
├── environment.yml                  # Conda 环境配置
├── .env.example                     # 环境变量模板
├── src/
│   ├── config/
│   │   └── env.py                   # 环境变量配置（Pydantic）
│   ├── core/
│   │   ├── websocket_server.py      # WebSocket 服务器
│   │   └── thread_pool.py           # 线程池管理
│   ├── modules/
│   │   ├── asr/                     # 语音识别模块
│   │   │   ├── base.py              # ASR 抽象基类
│   │   │   ├── aliyun_asr.py        # 阿里云 ASR 实现
│   │   │   └── factory.py           # ASR 工厂
│   │   ├── openclaw/                # AI 对话模块
│   │   │   ├── base.py              # OpenClaw 抽象基类
│   │   │   └── local_claw.py        # 本地 CLI 实现
│   │   ├── tts/                     # 语音合成模块
│   │   │   ├── base.py              # TTS 抽象基类
│   │   │   └── huoshan_tts.py       # 火山引擎 TTS 实现
│   │   └── servo/                   # 舵机控制模块
│   │       └── controller.py        # 舵机动画控制器
│   ├── utils/
│   │   ├── logger.py                # 日志系统
│   │   ├── message_handler.py       # 消息发送处理器
│   │   └── message_receiver.py      # 消息接收处理器
│   ├── assets/
│   │   └── JSON/                    # 舵机动画 JSON 文件目录
│   └── models/                      # 数据模型
├── config/
│   └── openclaw_prompt.txt          # OpenClaw 提示词配置
├── docs/
│   ├── AI_CONTEXT.md                # 本文档
│   ├── context/                     # 模块上下文目录
│   ├── websocket_message_protocol.md # WebSocket 消息协议
│   └── ALIYUN_ASR.md                # 阿里云 ASR 文档
├── logs/                            # 日志输出目录
└── tests/                           # 测试目录
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Conda/Miniconda

### 启动服务

```bash
# 1. 激活环境
conda activate watcher-server

# 2. 配置 .env 文件（复制 .env.example 并填入实际配置）
cp .env.example .env

# 3. 启动服务
python main.py
```

### 环境变量配置

**必须配置的项**：

```bash
# WebSocket 服务
WS_HOST=0.0.0.0
WS_PORT=8765

# 阿里云 ASR（推荐使用 AK/SK 方式）
ALIYUN_AK_ID=your_access_key_id
ALIYUN_AK_SECRET=your_access_key_secret
ALIYUN_APPKEY=your_appkey

# OpenClaw（本地 CLI 模式）
OPENCLAW_AGENT=main

# 火山引擎 TTS（可选）
HUOSHAN_APP_KEY=your_app_key
HUOSHAN_ACCESS_KEY=your_access_key
```

---

## 核心模块说明

### 1. WebSocket 服务器 ([websocket_server.py](../src/core/websocket_server.py))

- 处理客户端连接
- 音频流接收和处理
- 消息路由（ASR、OpenClaw、TTS、舵机）
- 舵机动画控制集成

**详细上下文**: [docs/context/websocket_context.md](context/websocket_context.md)

### 2. ASR 模块 ([modules/asr/](../src/modules/asr/))

- **基类**: `ASRProvider` - 定义统一接口
- **实现**: `AliyunASR` - 阿里云实时语音识别
- **认证方式**: 支持 AK/SK 自动获取 Token
- **特点**:
  - 后台线程运行 SDK
  - 异步接口包装
  - 自动 Token 刷新
  - 句子累积识别

**详细上下文**: [docs/context/asr_context.md](context/asr_context.md)

### 3. OpenClaw 模块 ([modules/openclaw/](../src/modules/openclaw/))

- **基类**: `OpenClawProvider` - 定义统一接口
- **实现**: `LocalOpenClawProvider` - 本地 CLI 模式
- **特点**:
  - 通过 `openclaw agent` 命令调用
  - 状态轮询机制（thinking/processing/completed）
  - 状态变化回调支持

**详细上下文**: [docs/context/openclaw_context.md](context/openclaw_context.md)

### 4. TTS 模块 ([modules/tts/](../src/modules/tts/))

- **基类**: `TTSProvider` - 定义统一接口
- **实现**: `HuoshanTTS` - 火山引擎语音合成
- **特点**:
  - 流式合成
  - 多种声音类型
  - PCM 格式输出

**详细上下文**: [docs/context/tts_context.md](context/tts_context.md)

### 5. 舵机控制模块 ([modules/servo/](../src/modules/servo/))

- **控制器**: `ServoController`
- **功能**:
  - 从 JSON 文件加载动画
  - 循环播放模式
  - 独占播放模式（一次性，不可中断）
  - X/Y 轴独立时间轴发送
- **动画格式**: JSON，包含 `fps`、`animated_objects`（关键帧数据）

**详细上下文**: [docs/context/servo_context.md](context/servo_context.md)

---

## 消息协议

WebSocket 消息采用统一 JSON 格式：

```json
{
  "type": "消息类型",
  "code": 0,
  "data": "消息数据"
}
```

### 服务端 → 客户端

| 类型 | 说明 | data 格式 |
|------|------|-----------|
| `asr_result` | ASR 识别结果 | 识别文本 |
| `bot_reply` | AI 回复 | 回复文本 |
| `status` | 状态消息 | 状态描述 |
| `servo` | 舵机控制 | `{"x": 90}` 或 `{"y": 45}` |
| `tts_end` | TTS 音频结束 | "ok" |
| `error` | 错误消息 | 错误描述 |

### 客户端 → 服务端

| 类型 | 说明 | 格式 |
|------|------|------|
| 二进制 | 音频数据 | PCM 格式 |
| "over" | 结束标记 | 字符串 |
| `{"type": "servo", ...}` | 舵机控制 | 见下方 |

**舵机控制消息**：
```json
// 循环播放
{"type": "servo", "action": "start", "state": "speech_nod"}
{"type": "servo", "action": "stop"}

// 独占播放（一次性）
{"type": "state", "data": "speech_nod"}
```

详细协议文档: [docs/websocket_message_protocol.md](websocket_message_protocol.md)

---

## 配置说明

### 环境变量 (.env)

所有配置通过 `src/config/env.py` 的 `Settings` 类管理，使用 Pydantic 自动从 `.env` 文件加载。

**配置分类**：

1. **WebSocket 配置** (`ws_*`)
2. **ASR 配置** (`asr_*`, `aliyun_*`)
3. **OpenClaw 配置** (`openclaw_*`)
4. **TTS 配置** (`tts_*`, `huoshan_*`)
5. **舵机配置** (`servo_*`)
6. **线程池配置** (`thread_pool_*`)
7. **日志配置** (`log_*`)

### OpenClaw 提示词配置

提示词存储在 `config/openclaw_prompt.txt`，格式：

```
TTS_PROMPT=请用简洁的纯文本回复...
```

提示词会自动加载并传递给 OpenClaw 作为 system 消息。

---

## 开发规范

### 添加新的 ASR Provider

1. 在 `src/modules/asr/` 创建新文件
2. 继承 `ASRProvider` 基类
3. 实现抽象方法：
   - `initialize()` - 初始化
   - `process_audio()` - 处理音频
   - `reset()` - 重置状态
   - `cleanup()` - 清理资源

**可选实现**（根据具体需求）：
- `stop()` - 停止识别会话
- `get_final_result()` - 获取最终识别结果

### 添加新的 TTS Provider

1. 在 `src/modules/tts/` 创建新文件
2. 继承 `TTSProvider` 基类
3. 实现抽象方法：
   - `initialize()` - 初始化
   - `synthesize()` - 合成语音
   - `synthesize_stream()` - 流式合成
   - `cleanup()` - 清理资源

### 日志规范

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("信息日志")
logger.debug("调试日志")
logger.warning("警告日志")
logger.error("错误日志", exc_info=True)  # 异常时加上 exc_info
```

---

## 常见问题

### Q: ASR 连接失败

**可能原因**：
1. Token 过期或无效
2. AK/SK 配置错误
3. 网络无法访问阿里云网关

**解决方法**：
- 使用 AK/SK 方式，系统会自动刷新 Token
- 检查 `.env` 中的 `ALIYUN_AK_ID` 和 `ALIYUN_AK_SECRET`
- 确认 AppKey 在阿里云控制台已配置

### Q: OpenClaw 调用失败

**可能原因**：
1. OpenClaw CLI 未安装
2. Gateway 未启动
3. Agent ID 配置错误

**解决方法**：
```bash
# 检查 CLI
openclaw --version

# 启动 Gateway
openclaw gateway start

# 检查 Gateway 状态
openclaw gateway status
```

### Q: 舵机动画不播放

**可能原因**：
1. JSON 文件格式错误
2. 文件路径配置错误
3. 帧率（fps）设置不匹配

**解决方法**：
- 检查 `servo_json_dir` 配置
- 确认 JSON 文件包含 `fps` 和 `animated_objects`
- 查看日志中的动画加载信息

---

## 重要文件路径

| 文件/目录 | 用途 |
|-----------|------|
| [main.py](../main.py) | 服务入口，初始化所有模块 |
| [src/config/env.py](../src/config/env.py) | 环境变量配置定义 |
| [src/core/websocket_server.py](../src/core/websocket_server.py) | WebSocket 服务器核心逻辑 |
| [src/modules/asr/aliyun_asr.py](../src/modules/asr/aliyun_asr.py) | 阿里云 ASR 实现 |
| [src/modules/openclaw/local_claw.py](../src/modules/openclaw/local_claw.py) | OpenClaw 本地 CLI 实现 |
| [src/modules/tts/huoshan_tts.py](../src/modules/tts/huoshan_tts.py) | 火山引擎 TTS 实现 |
| [src/modules/servo/controller.py](../src/modules/servo/controller.py) | 舵机动画控制器 |
| [src/utils/message_handler.py](../src/utils/message_handler.py) | 消息发送处理器 |
| [config/openclaw_prompt.txt](../config/openclaw_prompt.txt) | OpenClaw 提示词配置 |
| [.env.example](../.env.example) | 环境变量配置模板 |

---

## 相关文档

- [WebSocket 消息协议](websocket_message_protocol.md)
- [阿里云 ASR 使用说明](ALIYUN_ASR.md)
- [开发文档](../DEVELOPMENT.md)
- [README](../README.md)

---

**注意**: 本文档由 AI 维护，每次修改相关模块后，请更新对应的模块上下文文档。
