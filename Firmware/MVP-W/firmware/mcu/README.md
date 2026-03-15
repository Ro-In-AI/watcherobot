| Supported Targets | ESP32 |
| ----------------- | ----- |

<div align="center">

# MVP-W MCU Firmware

**ESP32 舵机控制 + BLE 固件**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![ESP-IDF](https://img.shields.io/badge/ESP--IDF-v5.2+-green.svg)](https://docs.espressif.com/projects/esp-idf/)
[![Platform](https://img.shields.io/badge/platform-ESP32-orange.svg)](https://www.espressif.com/en/products/socs/esp32)

</div>

MVP-W MCU 固件，用于控制双轴舵机云台。支持 BLE 蓝牙控制和 UART 串口通信（与 S3 主控通信）。

## 功能特性

- **双轴舵机控制** - GPIO 12 (X轴) + GPIO 15 (Y轴)
- **BLE GATT 服务** - 手机蓝牙远程控制
- **UART 通信** - 与 S3 主控双向通信
- **平滑移动** - 三种控制模式
- **预设动作** - 内置挥手、问候等动作

## 项目架构

```
main/
├── app_main.c              # 应用入口
├── command/                # 命令解析层 (BLE/UART 统一)
├── servo/                  # 舵机控制层
├── action/                 # 动作管理层
├── ble/                    # BLE 通信层
├── uart/                   # UART 通信层 (与 S3 通信)
└── CMakeLists.txt
```

### 分层说明

| 模块 | 功能 |
|------|------|
| **command** | 统一解析 BLE/UART 指令 |
| **servo** | PWM 舵机控制，平滑跟踪+摇杆模式 |
| **action** | 预设动作序列管理 |
| **ble** | BLE GATT 通信服务 |
| **uart** | UART 通信 (与 S3 主控通信) |

## 快速开始

### 烧录固件

**前置条件**：安装 esptool
```bash
pip install esptool
```

**Windows**:
```powershell
# 进入固件目录
cd firmware/mcu

# 烧录（自动检测串口）
.\flash.ps1

# 或指定串口
.\flash.ps1 -Port COM4
```

**Linux/macOS**:
```bash
# 进入固件目录
cd firmware/mcu

# 添加执行权限
chmod +x flash.sh

# 烧录
./flash.sh /dev/ttyUSB0
```

### 从源码构建

**前置条件**：ESP-IDF v5.2+

**Windows** (ESP-IDF PowerShell):
```powershell
# 激活 ESP-IDF 环境
C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1

# 构建
.\build_release.ps1

# 烧录
.\flash.ps1 -Port COM4
```

**Linux/macOS**:
```bash
# 激活 ESP-IDF 环境
source $HOME/esp/esp-idf/export.sh

# 构建
./build_release.sh

# 烧录
./flash.sh /dev/ttyUSB0
```

## GATT 服务配置

| UUID | 名称 | 描述 |
|------|------|------|
| 0x00FF | Service UUID | 主服务 |
| 0xFF01 | SERVO_CTRL | 舵机控制特征 (读写) |
| 0xFF02 | ACTION_CTRL | 动作控制特征 (读写) |
| 0xFF03 | STATUS | 状态推送特征 (Notify) |

设备名称: **ESP_ROBOT**

## 控制命令

### 模式1：平滑跟踪（转盘/滑块控制）

```
SET_SERVO:0:90      # 设置X轴到90度
SET_SERVO:1:120     # 设置Y轴到120度
```

- 速度固定约 67°/s
- 适合转盘、滑块控制

### 模式2：时间控制（指定时间到达）

```
SET_SERVO:0:90:500   # 500ms内到达90度
SET_SERVO:1:120:1000 # 1000ms内到达120度
```

- 时间范围：50ms - 5000ms
- 适合动作表演

### 模式3：摇杆模式（持续移动）

```
SERVO_MOVE:0:1    # 舵机0正向移动
SERVO_MOVE:0:-1   # 舵机0反向移动
SERVO_MOVE:0:0    # 停止舵机0
```

### 动作控制

```
PLAY_ACTION:0      # 挥手动作
PLAY_ACTION:1      # 问候动作
```

### 队列控制

```
QUEUE_ADD:0:90:500   # 添加舵机0到90度的延时任务
QUEUE_CLEAR          # 清空队列
```

## 预设动作

| ID | 名称 | 描述 |
|----|------|------|
| 0 | wave | 挥手动作 |
| 1 | greet | 问候动作 |

## 硬件配置

| 参数 | 值 |
|------|-----|
| 芯片 | ESP32 |
| 舵机数量 | 2 |
| X轴 GPIO | GPIO 12 |
| Y轴 GPIO | GPIO 15 |
| X轴角度范围 | 30° ~ 150° |
| Y轴角度范围 | 95° ~ 150° |
| PWM 频率 | 50Hz |
| UART 波特率 | 115200 |

## UART 通信

MCU 通过 UART 与 S3 主控通信：

| 参数 | 值 |
|------|-----|
| TX | GPIO 4 |
| RX | GPIO 5 |
| 波特率 | 115200 |
| 数据位 | 8 |
| 停止位 | 1 |

S3 发送命令格式与 BLE 相同，MCU 会通过 `command` 模块统一处理。

## 固件文件

| 文件 | 地址 | 说明 |
|------|------|------|
| `bootloader.bin` | 0x0 | ESP-IDF 引导程序 |
| `partition-table.bin` | 0x8000 | 分区表 |
| `MVP-W-MCU.bin` | 0x10000 | 应用固件 |

## 故障排除

### 烧录失败

1. **找不到设备**
   - 检查 USB 连接
   - 安装 CH340/CP2102 驱动

2. **连接失败**
   - 确保设备处于下载模式（按住 BOOT → 按 RST → 松开 BOOT）
   - 尝试降低波特率：`.\flash.ps1 -Port COM4 -Baud 115200`

3. **esptool 未找到**
   ```powershell
   pip install esptool
   ```

### BLE 连接问题

- 设备名称：ESP_ROBOT
- 使用 nRF Connect 或 LightBlue 扫描
- 必须使用 "Write Request" 模式发送命令

## 技术栈

- ESP-IDF 5.x
- BLE GATT Server
- LEDC PWM
- FreeRTOS

## 相关链接

- [MVP-W 主项目](../../CLAUDE.md)
- [S3 固件](../s3/)
- [UART 协议文档](docs/UART_PROTOCOL.md)
- [更新日志](CHANGELOG.md)
