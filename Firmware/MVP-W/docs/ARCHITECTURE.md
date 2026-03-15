# MVP-W Architecture | MVP-W 架构文档

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Overview

**MVP-W** (Minimum Viable Product - Watcher) is an ESP32-S3 based AI assistant robot with edge-cloud hybrid architecture.

```
┌─────────────────────┐      WebSocket      ┌─────────────────────┐
│   Watcher (Edge)    │◄──────────────────►│   Cloud (PC)        │
│   ESP32-S3          │   ws://IP:8766     │   Python Server     │
├─────────────────────┤                    ├─────────────────────┤
│ • Voice Capture     │                    │ • ASR (Aliyun)      │
│ • Voice Playback    │                    │ • LLM (Claude)      │
│ • Display & Emoji   │                    │ • TTS (Volcengine)  │
│ • Wake Word Detect  │                    │ • Agent Orchestration│
│ • UART → MCU        │                    └─────────────────────┘
└─────────┬───────────┘
          │ UART 115200
          ▼
┌─────────────────────┐
│  MCU (Body)         │
│  ESP32 Servo Control│
│  • X/Y Axis Gimbal  │
│  • LED Indicator    │
└─────────────────────┘
```

### Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| Voice Trigger | ✅ | Wake word "Hi Espressif" + Button press |
| WebSocket | ✅ | Bidirectional audio stream |
| TTS Playback | ✅ | 24kHz PCM direct output |
| Servo Control | ✅ | UART to MCU |
| Display | ✅ | LVGL UI + PNG animation |
| Service Discovery | ✅ | UDP broadcast |

### Hardware Architecture

#### ESP32-S3 (Watcher) GPIO

| GPIO | Function | Note |
|------|----------|------|
| 10-12, 15-16 | I2S Audio | Mic + Speaker |
| 4-6 | LCD SPI | Display |
| 19-20 | UART0 | → MCU (flash disconnect needed) |
| 38-39 | Touch I2C | Touchscreen |
| 41-42 | Encoder | Knob button |

#### ESP32 (MCU) GPIO

| GPIO | Function |
|------|----------|
| 16-17 | UART (↔ S3) |
| 12 | Servo X (PWM) |
| 13 | Servo Y (PWM) |

### Communication Protocol

See [COMMUNICATION_PROTOCOL.md](./COMMUNICATION_PROTOCOL.md) for details.

**Quick Reference:**

| Direction | Format | Sample Rate |
|-----------|--------|-------------|
| Device → Cloud | Raw PCM | 16kHz, 16-bit, mono |
| Cloud → Device | Raw PCM | 24kHz, 16-bit, mono |

### Project Structure

```
MVP-W/
├── firmware/
│   ├── s3/                    # ESP32-S3 main controller
│   │   ├── main/              # Source code
│   │   ├── components/        # SDK components
│   │   └── spiffs/            # Animation assets
│   └── mcu/                   # ESP32 servo controller
├── docs/                      # Documentation
└── CLAUDE.md                  # AI assistant context
```

### Quick Start

#### 1. Build S3 Firmware

```powershell
# Activate ESP-IDF environment
C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1

cd firmware/s3
idf.py set-target esp32s3
idf.py build
idf.py -p COM3 flash monitor
```

#### 2. Build MCU Firmware

```powershell
cd firmware/mcu
idf.py set-target esp32
idf.py -p COM4 flash monitor
```

#### 3. Start Cloud Server

```bash
cd watcher-server
pip install -r requirements.txt
python src/main.py
```

### Key Files

| Module | File | Description |
|--------|------|-------------|
| Entry | `firmware/s3/main/app_main.c` | System init |
| WebSocket | `firmware/s3/main/ws_client.c` | Communication core |
| Voice | `firmware/s3/main/button_voice.c` | Voice state machine |
| Wake Word | `firmware/s3/main/hal_wake_word.c` | ESP-SR detection |
| Servo | `firmware/mcu/main/servo_control.c` | PWM control |

---

<a name="中文"></a>
## 中文

### 概述

**MVP-W**（最小可行产品 - Watcher）是基于 ESP32-S3 的 AI 助手机器人，采用边缘-云端混合架构。

### 核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 语音触发 | ✅ | 唤醒词 "你好小智" + 按键 |
| WebSocket | ✅ | 双向音频流 |
| TTS 播放 | ✅ | 24kHz PCM 直出 |
| 舵机控制 | ✅ | UART 转发 MCU |
| 显示屏 | ✅ | LVGL UI + PNG 动画 |
| 服务发现 | ✅ | UDP 广播 |

### 硬件架构

#### ESP32-S3 (主控) GPIO

| GPIO | 功能 | 说明 |
|------|------|------|
| 10-12, 15-16 | I2S 音频 | 麦克风 + 喇叭 |
| 4-6 | LCD SPI | 显示屏 |
| 19-20 | UART0 | → MCU (烧录时需断开) |
| 38-39 | 触摸 I2C | 触摸屏 |
| 41-42 | 编码器 | 旋钮按键 |

#### ESP32 (MCU) GPIO

| GPIO | 功能 |
|------|------|
| 16-17 | UART (↔ S3) |
| 12 | 舵机 X (PWM) |
| 13 | 舵机 Y (PWM) |

### 通信协议

详见 [COMMUNICATION_PROTOCOL.md](./COMMUNICATION_PROTOCOL.md)。

**快速参考：**

| 方向 | 格式 | 采样率 |
|------|------|--------|
| 设备 → 云端 | Raw PCM | 16kHz, 16-bit, mono |
| 云端 → 设备 | Raw PCM | 24kHz, 16-bit, mono |

### 项目结构

```
MVP-W/
├── firmware/
│   ├── s3/                    # ESP32-S3 主控固件
│   │   ├── main/              # 源代码
│   │   ├── components/        # SDK 组件
│   │   └── spiffs/            # 动画资源
│   └── mcu/                   # ESP32 舵机控制固件
├── docs/                      # 文档
└── CLAUDE.md                  # AI 助手上下文
```

### 快速开始

#### 1. 编译 S3 固件

```powershell
# 激活 ESP-IDF 环境
C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1

cd firmware/s3
idf.py set-target esp32s3
idf.py build
idf.py -p COM3 flash monitor
```

#### 2. 编译 MCU 固件

```powershell
cd firmware/mcu
idf.py set-target esp32
idf.py -p COM4 flash monitor
```

#### 3. 启动云端服务器

```bash
cd watcher-server
pip install -r requirements.txt
python src/main.py
```

### 关键文件

| 模块 | 文件 | 说明 |
|------|------|------|
| 入口 | `firmware/s3/main/app_main.c` | 系统初始化 |
| WebSocket | `firmware/s3/main/ws_client.c` | 通信核心 |
| 语音 | `firmware/s3/main/button_voice.c` | 语音状态机 |
| 唤醒词 | `firmware/s3/main/hal_wake_word.c` | ESP-SR 检测 |
| 舵机 | `firmware/mcu/main/servo_control.c` | PWM 控制 |

---

## Related Documentation | 相关文档

- [Communication Protocol | 通信协议](./COMMUNICATION_PROTOCOL.md)
- [Build Instructions | 编译指南](../firmware/s3/BUILD_INSTRUCTIONS.md)

## License | 许可证

MIT License
