# Wake Word Detection Guide (唤醒词检测指南)

## Overview

MVP-W 支持离线唤醒词检测，使用乐鑫 ESP-SR 框架。

### 支持的唤醒词

| 模型 | 唤醒词 | 说明 |
|------|--------|------|
| `nihaoxiaozhi` | 你好小智 | 默认模型 |
| `nihaoxiaowei` | 你好小微 | 可选 |
| Custom | 自定义拼音 | Multinet 模型 |

---

## Quick Start

### 1. 启用唤醒词功能

```bash
cd firmware/s3
idf.py menuconfig
```

导航到：
```
Component Config
  └── Wake Word Configuration
        └── [*] Enable Wake Word Detection
              └── Wake Word Model
                    └── (X) Ni Hao Xiao Zhi (你好小智)
```

### 2. 编译和烧录

```bash
# 首次编译会自动下载 ESP-SR 组件 (~50MB)
idf.py build

# 烧录
idf.py -p COM3 flash monitor
```

### 3. 验证

查看日志确认初始化成功：
```
I (1234) HAL_WAKE_WORD: Wake word detector initialized successfully
I (1235) HAL_WAKE_WORD: Model 0: wn9_nihaoxiaozhi_tts
I (1236) HAL_WAKE_WORD: Parsed 1 wake words
I (1237) HAL_WAKE_WORD:   [0] nihaoxiaozhi
I (1238) HAL_WAKE_WORD: Wake word detection started
```

---

## Configuration Options

### Kconfig 选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `CONFIG_ENABLE_WAKE_WORD` | n | 启用唤醒词检测 |
| `CONFIG_WAKE_WORD_NIHAOXIAOZHI` | y | 使用 "你好小智" 模型 |
| `CONFIG_WAKE_WORD_CUSTOM` | n | 使用自定义唤醒词 |
| `CONFIG_CUSTOM_WAKE_WORD_PHRASE` | "xiao wei xiao wei" | 自定义唤醒词拼音 |
| `CONFIG_WAKE_WORD_DETECTION_TIMEOUT_MS` | 5000 | 检测超时时间 |

### sdkconfig.defaults

```ini
# PSRAM 配置 (必需)
CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL=2048
CONFIG_SPIRAM_MALLOC_RESERVE_INTERNAL=98304

# ESP-SR 需要 PSRAM
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_OCT=y
```

---

## Architecture

### Audio Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      AUDIO DATA FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Microphone] ──I2S──► hal_audio_read() ──► g_pcm_buf           │
│                                              │                   │
│                                              ▼                   │
│                         ┌───────────────────────────────────┐   │
│                         │     voice_recorder_tick()         │   │
│                         │                                   │   │
│                         │  if (IDLE):                       │   │
│                         │    └─► hal_wake_word_feed()      │   │
│                         │         (本地检测，不发送)        │   │
│                         │                                   │   │
│                         │  if (RECORDING):                  │   │
│                         │    └─► ws_send_audio()           │   │
│                         │         (发送到云端)              │   │
│                         └───────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### State Machine

```
┌─────────┐  Wake Word / Button Press  ┌──────────────┐
│  IDLE   │───────────────────────────►│  RECORDING   │
│         │                            │              │
└─────────┘◄───────────────────────────┤              │
     ▲      Button Release / Timeout   └──────────────┘
```

---

## Files

| File | Purpose |
|------|---------|
| `main/hal_wake_word.h` | HAL 接口定义 |
| `main/hal_wake_word.c` | ESP-SR AFE 实现 |
| `main/button_voice.c` | 状态机集成 |
| `main/Kconfig.projbuild` | 配置选项 |
| `main/idf_component.yml` | ESP-SR 依赖 |

---

## Resource Usage

| 资源 | 消耗 |
|------|------|
| **PSRAM** | ~200KB (AFE buffers) |
| **Flash** | ~500KB (模型文件) |
| **CPU** | ~15% (检测时) |

---

## Troubleshooting

### 编译错误: ESP-SR 组件未找到

```bash
# 清理并重新构建
idf.py fullclean
idf.py reconfigure
idf.py build
```

### 运行时错误: 模型加载失败

检查 PSRAM 配置：
```bash
idf.py menuconfig
# -> Component Config -> ESP PSRAM
#    -> [*] Enable PSRAM
#    -> SPI RAM Mode (Octal PSRAM)
```

### 检测不灵敏

调整检测阈值（在 `button_voice.c` 中）：
```c
wake_word_config_t config = {
    .detection_threshold = 0.3f,  // 降低阈值更灵敏
    ...
};
```

---

## Testing

### Host 单元测试

```bash
cd firmware/s3/test_host
cmake -B build -G "MinGW Makefiles"
cmake --build build
./build/test_wake_word.exe
```

### 硬件测试

1. 烧录固件
2. 说 "你好小智"
3. 观察日志和屏幕反馈
4. 验证进入 RECORDING 状态

---

*Last Updated: 2026-03-03*
