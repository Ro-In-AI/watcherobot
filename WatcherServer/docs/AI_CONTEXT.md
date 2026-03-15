[English](AI_CONTEXT.md) | [中文](AI_CONTEXT_CN.md)

# Watcher Server - AI Context Documentation

> **Last Updated**: 2026-03-04
> **Project Status**: Active Development

## Project Overview

**Watcher Server** is a WebSocket-based voice dialogue server that provides voice interaction capabilities for smart hardware (such as robots). The server receives client audio streams, performs real-time speech recognition (ASR), calls AI dialogue services, and returns synthesized speech (TTS) audio and servo control commands.

### Core Features

1. **Real-time Speech Recognition (ASR)** - Supports Aliyun real-time speech recognition
2. **AI Dialogue** - AI dialogue via OpenClaw local CLI
3. **Speech Synthesis (TTS)** - Supports Huoshan Engine TTS
4. **Servo Control** - Reads JSON animation files and sends servo angle data along timeline
5. **Status Synchronization** - Real-time synchronization of AI thinking status, servo animation status, etc.

### Tech Stack

- **Language**: Python 3.10+
- **Async Framework**: asyncio
- **WebSocket**: websockets
- **Configuration Management**: pydantic-settings
- **Logging System**: loguru
- **Environment Management**: Conda

---

## Project Structure

```
watcher-server/
├── main.py                          # Service entry point
├── requirements.txt                 # Python dependencies
├── environment.yml                  # Conda environment configuration
├── .env.example                     # Environment variable template
├── src/
│   ├── config/
│   │   └── env.py                   # Environment variable configuration (Pydantic)
│   ├── core/
│   │   ├── websocket_server.py      # WebSocket server
│   │   └── thread_pool.py           # Thread pool management
│   ├── modules/
│   │   ├── asr/                     # Speech recognition module
│   │   │   ├── base.py              # ASR abstract base class
│   │   │   ├── aliyun_asr.py        # Aliyun ASR implementation
│   │   │   └── factory.py           # ASR factory
│   │   ├── openclaw/                # AI dialogue module
│   │   │   ├── base.py              # OpenClaw abstract base class
│   │   │   └── local_claw.py        # Local CLI implementation
│   │   ├── tts/                     # Speech synthesis module
│   │   │   ├── base.py              # TTS abstract base class
│   │   │   └── huoshan_tts.py       # Huoshan Engine TTS implementation
│   │   └── servo/                   # Servo control module
│   │       └── controller.py        # Servo animation controller
│   ├── utils/
│   │   ├── logger.py                # Logging system
│   │   ├── message_handler.py       # Message sending handler
│   │   └── message_receiver.py      # Message receiving handler
│   ├── assets/
│   │   └── JSON/                    # Servo animation JSON file directory
│   └── models/                      # Data models
├── config/
│   └── openclaw_prompt.txt          # OpenClaw prompt configuration
├── docs/
│   ├── AI_CONTEXT.md                # This document
│   ├── context/                     # Module context directory
│   ├── websocket_message_protocol.md # WebSocket message protocol
│   └── ALIYUN_ASR.md                # Aliyun ASR documentation
├── logs/                            # Log output directory
└── tests/                           # Test directory
```

---

## Quick Start

### Environment Requirements

- Python 3.10+
- Conda/Miniconda

### Start the Service

```bash
# 1. Activate environment
conda activate watcher-server

# 2. Configure .env file (copy .env.example and fill in actual config)
cp .env.example .env

# 3. Start service
python main.py
```

### Environment Variable Configuration

**Required Configuration Items**:

```bash
# WebSocket service
WS_HOST=0.0.0.0
WS_PORT=8765

# Aliyun ASR (recommended to use AK/SK)
ALIYUN_AK_ID=your_access_key_id
ALIYUN_AK_SECRET=your_access_key_secret
ALIYUN_APPKEY=your_appkey

# OpenClaw (local CLI mode)
OPENCLAW_AGENT=main

# Huoshan TTS (optional)
HUOSHAN_APP_KEY=your_app_key
HUOSHAN_ACCESS_KEY=your_access_key
```

---

## Core Module Description

### 1. WebSocket Server ([websocket_server.py](../src/core/websocket_server.py))

- Handle client connections
- Audio stream reception and processing
- Message routing (ASR, OpenClaw, TTS, servo)
- Servo animation control integration

**Detailed Context**: [docs/context/websocket_context.md](context/websocket_context.md)

### 2. ASR Module ([modules/asr/](../src/modules/asr/))

- **Base Class**: `ASRProvider` - Defines unified interface
- **Implementation**: `AliyunASR` - Aliyun real-time speech recognition
- **Authentication**: Supports AK/SK auto Token retrieval
- **Features**:
  - SDK runs in background thread
  - Async interface wrapper
  - Automatic Token refresh
  - Sentence accumulation recognition

**Detailed Context**: [docs/context/asr_context.md](context/asr_context.md)

### 3. OpenClaw Module ([modules/openclaw/](../src/modules/openclaw/))

- **Base Class**: `OpenClawProvider` - Defines unified interface
- **Implementation**: `LocalOpenClawProvider` - Local CLI mode
- **Features**:
  - Call via `openclaw agent` command
  - Status polling mechanism (thinking/processing/completed)
  - Status change callback support

**Detailed Context**: [docs/context/openclaw_context.md](context/openclaw_context.md)

### 4. TTS Module ([modules/tts/](../src/modules/tts/))

- **Base Class**: `TTSProvider` - Defines unified interface
- **Implementation**: `HuoshanTTS` - Huoshan Engine speech synthesis
- **Features**:
  - Streaming synthesis
  - Multiple voice types
  - PCM format output

**Detailed Context**: [docs/context/tts_context.md](context/tts_context.md)

### 5. Servo Control Module ([modules/servo/](../src/modules/servo/))

- **Controller**: `ServoController`
- **Features**:
  - Load animations from JSON files
  - Loop playback mode
  - Exclusive playback mode (one-time, uninterruptible)
  - X/Y axis independent timeline sending
- **Animation Format**: JSON, containing `fps`, `animated_objects` (keyframe data)

**Detailed Context**: [docs/context/servo_context.md](context/servo_context.md)

---

## Message Protocol

WebSocket messages use unified JSON format:

```json
{
  "type": "message type",
  "code": 0,
  "data": "message data"
}
```

### Server → Client

| Type | Description | Data Format |
|------|-------------|-------------|
| `asr_result` | ASR recognition result | Recognized text |
| `bot_reply` | AI reply | Reply text |
| `status` | Status message | Status description |
| `servo` | Servo control | `{"x": 90}` or `{"y": 45}` |
| `tts_end` | TTS audio end | "ok" |
| `error` | Error message | Error description |

### Client → Server

| Type | Description | Format |
|------|-------------|--------|
| Binary | Audio data | PCM format |
| "over" | End marker | String |
| `{"type": "servo", ...}` | Servo control | See below |

**Servo Control Message**:
```json
// Loop playback
{"type": "servo", "action": "start", "state": "speech_nod"}
{"type": "servo", "action": "stop"}

// Exclusive playback (one-time)
{"type": "state", "data": "speech_nod"}
```

Detailed protocol documentation: [docs/websocket_message_protocol.md](websocket_message_protocol.md)

---

## Configuration Description

### Environment Variables (.env)

All configuration is managed by the `Settings` class in `src/config/env.py`, using Pydantic to automatically load from `.env` file.

**Configuration Categories**:

1. **WebSocket Configuration** (`ws_*`)
2. **ASR Configuration** (`asr_*`, `aliyun_*`)
3. **OpenClaw Configuration** (`openclaw_*`)
4. **TTS Configuration** (`tts_*`, `huoshan_*`)
5. **Servo Configuration** (`servo_*`)
6. **Thread Pool Configuration** (`thread_pool_*`)
7. **Log Configuration** (`log_*`)

### OpenClaw Prompt Configuration

Prompts are stored in `config/openclaw_prompt.txt`, format:

```
TTS_PROMPT=Please reply in concise plain text...
```

Prompts are automatically loaded and passed to OpenClaw as system messages.

---

## Development Standards

### Adding a New ASR Provider

1. Create new file under `src/modules/asr/`
2. Inherit from `ASRProvider` base class
3. Implement abstract methods:
   - `initialize()` - Initialize
   - `process_audio()` - Process audio
   - `reset()` - Reset state
   - `cleanup()` - Cleanup resources

**Optional Implementation** (based on specific needs):
- `stop()` - Stop recognition session
- `get_final_result()` - Get final recognition result

### Adding a New TTS Provider

1. Create new file under `src/modules/tts/`
2. Inherit from `TTSProvider` base class
3. Implement abstract methods:
   - `initialize()` - Initialize
   - `synthesize()` - Synthesize speech
   - `synthesize_stream()` - Streaming synthesis
   - `cleanup()` - Cleanup resources

### Logging Standards

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Info log")
logger.debug("Debug log")
logger.warning("Warning log")
logger.error("Error log", exc_info=True)  # Add exc_info for exceptions
```

---

## FAQ

### Q: ASR Connection Failed

**Possible Causes**:
1. Token expired or invalid
2. AK/SK configuration error
3. Network cannot access Aliyun gateway

**Solutions**:
- Use AK/SK method, system will automatically refresh Token
- Check `ALIYUN_AK_ID` and `ALIYUN_AK_SECRET` in `.env`
- Confirm AppKey is configured in Aliyun console

### Q: OpenClaw Call Failed

**Possible Causes**:
1. OpenClaw CLI not installed
2. Gateway not started
3. Agent ID configuration error

**Solutions**:
```bash
# Check CLI
openclaw --version

# Start Gateway
openclaw gateway start

# Check Gateway status
openclaw gateway status
```

### Q: Servo Animation Not Playing

**Possible Causes**:
1. JSON file format error
2. File path configuration error
3. Frame rate (fps) setting mismatch

**Solutions**:
- Check `servo_json_dir` configuration
- Confirm JSON file contains `fps` and `animated_objects`
- Check animation loading info in logs

---

## Important File Paths

| File/Directory | Purpose |
|----------------|---------|
| [main.py](../main.py) | Service entry point, initializes all modules |
| [src/config/env.py](../src/config/env.py) | Environment variable configuration definition |
| [src/core/websocket_server.py](../src/core/websocket_server.py) | WebSocket server core logic |
| [src/modules/asr/aliyun_asr.py](../src/modules/asr/aliyun_asr.py) | Aliyun ASR implementation |
| [src/modules/openclaw/local_claw.py](../src/modules/openclaw/local_claw.py) | OpenClaw local CLI implementation |
| [src/modules/tts/huoshan_tts.py](../src/modules/tts/huoshan_tts.py) | Huoshan Engine TTS implementation |
| [src/modules/servo/controller.py](../src/modules/servo/controller.py) | Servo animation controller |
| [src/utils/message_handler.py](../src/utils/message_handler.py) | Message sending handler |
| [config/openclaw_prompt.txt](../config/openclaw_prompt.txt) | OpenClaw prompt configuration |
| [.env.example](../.env.example) | Environment variable configuration template |

---

## Related Documentation

- [WebSocket Message Protocol](websocket_message_protocol.md)
- [Aliyun ASR Usage Guide](ALIYUN_ASR.md)
- [Development Documentation](../DEVELOPMENT.md)
- [README](../README.md)

---

**Note**: This document is maintained by AI. After modifying related modules, please update the corresponding module context document.
