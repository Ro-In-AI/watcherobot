# MVP-W v1.5.0

**发布日期**: 2026-03-15

MVP-W v1.5.0 是首个开源发布版本，包含完整的语音交互和舵机控制功能。

## 版本亮点

- 端到端语音交互（按键触发 → ASR → LLM → TTS）
- ESP-SR 离线唤醒词检测 ("Hi 乐鑫")
- VAD 静音自动停止
- PNG 动画显示（24帧表情）
- WebSocket 双向通信
- UDP 服务发现
- 双轴舵机云台控制（MCU + BLE）

## 固件文件

### S3 主控固件 (ESP32-S3)

| 文件 | 地址 | 大小 | 说明 |
|------|------|------|------|
| `firmware/bootloader.bin` | 0x0 | 21KB | ESP-IDF 引导程序 |
| `firmware/partition-table.bin` | 0x8000 | 3KB | 分区表 |
| `firmware/MVP-W-S3.bin` | 0x10000 | 1.89MB | 应用固件 |
| `firmware/srmodels.bin` | 0x410000 | 285KB | 唤醒词模型 |
| `firmware/storage.bin` | 0x460000 | 10.5MB | PNG 动画资源 |

### MCU 舵机控制固件 (ESP32)

| 文件 | 地址 | 大小 | 说明 |
|------|------|------|------|
| `firmware/mcu/bootloader.bin` | 0x0 | 26KB | ESP-IDF 引导程序 |
| `firmware/mcu/partition-table.bin` | 0x8000 | 3KB | 分区表 |
| `firmware/mcu/MVP-W-MCU.bin` | 0x10000 | 810KB | 应用固件 (BLE + 舵机) |

## 系统要求

### 硬件

| 组件 | 芯片 | 说明 |
|------|------|------|
| **S3 主控** | ESP32-S3 | 16MB Flash + 8MB PSRAM |
| **MCU 舵机** | ESP32 | 4MB Flash，双轴云台控制 |
| 麦克风 | I2S DMIC | 16kHz 采样 |
| 扬声器 | I2S | 24kHz 播放 |
| 显示屏 | LCD QSPI | 可选 |
| 舵机 | PWM x2 | GPIO 12 (X轴), GPIO 15 (Y轴) |

### 软件

- Python 3.8+
- esptool 4.6+ (`pip install esptool`)

## 烧录步骤

### S3 主控固件

#### Windows
```powershell
# 安装 esptool
pip install esptool

# 进入固件目录
cd releases\v1.5.0

# 完整烧录（默认 115200 波特率，约 3 分钟）
.\flash.ps1 -Port COM3

# 或仅更新应用
.\flash.ps1 -Port COM3 -AppOnly
```

#### Linux/macOS
```bash
# 安装 esptool
pip install esptool

# 进入固件目录
cd releases/v1.5.0

# 添加执行权限
chmod +x flash.sh

# 完整烧录
./flash.sh /dev/ttyUSB0
```

### MCU 舵机固件

#### Windows
```powershell
# 进入固件目录
cd releases\v1.5.0

# 烧录 MCU 固件（约 1 分钟）
.\flash_mcu.ps1 -Port COM4
```

#### Linux/macOS
```bash
# 进入固件目录
cd releases/v1.5.0

# 烧录 MCU 固件
./flash_mcu.sh /dev/ttyUSB1
```

### 手动烧录

**S3 固件**:
```bash
python -m esptool --chip esp32s3 --port COM3 --baud 115200 \
    write_flash 0x0 firmware/bootloader.bin \
    0x8000 firmware/partition-table.bin \
    0x10000 firmware/MVP-W-S3.bin \
    0x410000 firmware/srmodels.bin \
    0x460000 firmware/storage.bin
```

**MCU 固件**:
```bash
python -m esptool --chip esp32 --port COM4 --baud 115200 \
    write_flash 0x0 firmware/mcu/bootloader.bin \
    0x8000 firmware/mcu/partition-table.bin \
    0x10000 firmware/mcu/MVP-W-MCU.bin
```

## 配置

### WiFi 配置

**当前版本 WiFi 为硬编码**：
- SSID: `TEST`
- 密码: `12345678`

**使用前请确保**：
1. 创建手机热点：SSID 为 `TEST`，密码 `12345678`
2. 或修改源码 `firmware/s3/main/wifi_client.c` 中的 `WIFI_SSID` 和 `WIFI_PASS` 后重新编译
3. 电脑服务器和 ESP32 必须在同一 WiFi 网络下

### 云端服务器

设备默认通过 UDP 服务发现自动寻找云端服务器。

启动云端服务器：
```bash
cd watcher-server
pip install -r requirements.txt
python src/main.py
```

### MCU 舵机控制

MCU 支持两种控制方式：

**1. BLE 蓝牙控制**
- 设备名称: `ESP_ROBOT`
- 使用 nRF Connect 或 LightBlue 连接
- 写入命令到特征 UUID `0xFF01`

**2. UART 串口控制**
- S3 主控通过 UART 发送命令
- 波特率: 115200
- 格式与 BLE 命令相同

**控制命令**:
```
SET_SERVO:0:90        # X轴到90度
SET_SERVO:1:120       # Y轴到120度
SET_SERVO:0:90:500    # 500ms内到达90度
SERVO_MOVE:0:1        # X轴正向持续移动
PLAY_ACTION:0         # 播放挥手动作
```

## 验证

### S3 主控

1. **启动检查**
   - 按 RST 重启
   - 串口监视器（115200 8N1）应显示启动日志
   - 显示屏应显示启动动画

2. **唤醒词检测**
   - 说 "Hi 乐鑫"
   - 设备应响应并开始录音

3. **语音交互**
   - 长按按键 0.5s 开始录音
   - 松开按键结束录音
   - 等待 AI 回复

### MCU 舵机

1. **启动检查**
   - 串口监视器应显示 "BLE + UART Robot initialized"

2. **BLE 连接**
   - 手机扫描 "ESP_ROBOT" 并连接
   - 发送 `SET_SERVO:0:90` 测试舵机

3. **UART 通信**
   - 连接 S3 和 MCU 的 UART
   - S3 发送舵机命令，MCU 执行

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      MVP-W 系统                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐      UART      ┌─────────────────┐│
│  │   S3 主控        │◄────────────►│   MCU 舵机       ││
│  │  (ESP32-S3)     │   115200      │   (ESP32)       ││
│  │                 │               │                 ││
│  │  - 语音交互     │               │  - 舵机控制     ││
│  │  - 显示动画     │               │  - BLE 服务     ││
│  │  - WebSocket    │               │  - 动作系统     ││
│  └────────┬────────┘               └─────────────────┘│
│           │ WiFi                                        │
│           ▼                                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │              云端服务器 (Python)                 │   │
│  │  - ASR (阿里云)                                 │   │
│  │  - LLM (Claude API)                            │   │
│  │  - TTS (火山引擎)                              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 已知问题

- Opus 编解码未实现（使用 PCM 直传）
- 摄像头功能未集成
- OTA 升级未实现

## 变更日志

### v1.5.0 (2026-03-15)

**新增功能**
- 完整语音交互流程
- ESP-SR 唤醒词检测
- VAD 静音检测
- PNG 动画显示
- UDP 服务发现
- MCU 舵机控制 (BLE + UART)
- 预设动作系统

**修复**
- 修复 TTS 后唤醒词不恢复的问题
- 修复 PNG 动画花屏/白屏问题
- 修复 WiFi DMA 与 SPI 冲突问题

## 故障排除

### 烧录失败

**问题**: `Failed to connect`
**解决**:
- 确保设备处于下载模式（按住 BOOT → 按 RST → 松开 BOOT）
- 更换 USB 线/端口

### 唤醒词无响应

**问题**: 说 "Hi 乐鑫" 无反应
**解决**:
- 检查麦克风连接
- 确保 `srmodels.bin` 正确烧录

### 舵机不响应

**问题**: MCU 舵机不动
**解决**:
- 检查舵机电源（需要 5V 外部供电）
- 检查 UART 连接（TX/RX 是否交叉）
- 确认 BLE 连接成功

## 反馈

如有问题，请在项目 Issues 中反馈。
