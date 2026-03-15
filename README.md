| Supported Targets | ESP32 |
| ----------------- | ----- |

<div align="center">

# WatcherRobot Body

**ESP32 BLE 遥控机器人固件**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![ESP-IDF](https://img.shields.io/badge/ESP--IDF-v5.2+-green.svg)](https://docs.espressif.com/projects/esp-idf/)
[![Platform](https://img.shields.io/badge/platform-ESP32-orange.svg)](https://www.espressif.com/en/products/socs/esp32)

</div>

基于 ESP32 的 BLE 遥控机器人项目，支持通过蓝牙远程控制两个 PWM 舵机，具有平滑移动和预设动作功能。后续可扩展 UART 与其他 MCU 通信。

## 项目架构

```
main/
├── app_main.c              # 应用入口
├── command/                # 命令解析层
│   ├── command.h
│   └── command.c
├── servo/                  # 舵机控制层
│   ├── servo.h
│   └── servo.c
├── action/                 # 动作管理层
│   ├── action.h
│   └── action.c
├── ble/                    # BLE 通信层
│   ├── ble.h
│   └── ble.c
└── CMakeLists.txt
```

### 分层说明

| 模块 | 功能 |
|------|------|
| **command** | 统一解析 BLE/UART 指令 |
| **servo** | PWM 舵机控制 (GPIO 12, 15)，平滑跟踪+摇杆模式 |
| **action** | 预设动作序列管理 |
| **ble** | BLE GATT 通信服务 |
| **uart** | UART 通信 (预留，后续扩展) |

## GATT 服务配置

| UUID | 名称 | 描述 |
|------|------|------|
| 0x00FF | Service UUID | 主服务 |
| 0xFF01 | SERVO_CTRL | 舵机控制特征 (读写) |
| 0xFF02 | ACTION_CTRL | 动作控制特征 (读写) |
| 0xFF03 | STATUS | 状态推送特征 (Notify) |

## BLE 命令协议

### 模式1：平滑跟踪（转盘/滑块控制）

```
SET_SERVO:0:90      # 设置X轴到90度（平滑跟踪，固定速度）
SET_SERVO:1:120     # 设置Y轴到120度
```

**格式**: `SET_SERVO:<舵机ID>:<角度>`

**特点**：
- 第4个参数为0或省略
- 每15ms移动1°，速度固定约67°/s
- APP可任意频率发送，舵机自动向最新目标平滑移动
- 适合转盘、滑块控制

### 模式2：时间控制（指定时间到达）

```
SET_SERVO:0:90:500   # 500ms内到达90度
SET_SERVO:1:120:1000 # 1000ms内到达120度
```

**格式**: `SET_SERVO:<舵机ID>:<角度>:<时间ms>`

**特点**：
- 第4个参数为移动时间（50ms - 5000ms）
- 速度动态计算：每步角度 = 总角度差 / (时间/15ms)
- 适合动作表演（wave 2秒，greet 1秒）

### 模式3：摇杆模式（持续移动）

```
SERVO_MOVE:0:1    # 舵机0正向持续移动
SERVO_MOVE:0:-1   # 舵机0反向持续移动
SERVO_MOVE:1:1    # 舵机1正向持续移动
SERVO_MOVE:0:0    # 停止舵机0移动
SERVO_MOVE:1:0    # 停止舵机1移动
```

**格式**：`SERVO_MOVE:<舵机ID>:<方向>` (方向: 1=正, -1=反, 0=停)

### 动作控制

```
PLAY_ACTION:0      # 播放预设动作0 (wave)
PLAY_ACTION:1      # 播放预设动作1 (greet)
```

## 预设动作

| ID | 名称 | 描述 |
|----|------|------|
| 0 | wave | 挥手动作 |
| 1 | greet | 问候动作 |

## 硬件配置

- **舵机数量**: 2 个
- **舵机 GPIO**: GPIO 12 (X轴), GPIO 15 (Y轴)
- **X轴角度范围**: 30° ~ 150°
- **Y轴角度范围**: 95° ~ 150°
- **PWM 频率**: 50Hz (20ms 周期)
- **脉宽范围**: 0.5ms - 2.5ms (对应 0-180°)

## 运动控制参数

### 平滑跟踪模式

| 参数 | 值 | 说明 |
|------|-----|------|
| 跟踪周期 | 15ms | 每15ms更新一次舵机位置 |
| 步长 | 1° | 每次移动的角度 |
| 响应速度 | ~67°/s | 1°/15ms × 1000ms |

### 时间控制模式

| 参数 | 值 | 说明 |
|------|-----|------|
| 最小时间 | 50ms | 避免舵机死区 |
| 最大时间 | 5000ms | 避免等待过长 |
| 速度计算 | 动态 | 每步角度 = 总差值 / (时间/15ms) |

## MTU 配置

- **本地 MTU**: 512 字节（在 `ble.c` 中设置，建议连接后手动请求 MTU 512）
- **特征值最大长度**: 500 字节

如需修改 MTU，在 `main/ble/ble.c` 中找到：
```c
esp_ble_gatt_set_local_mtu(512);
```

## 构建命令

```bash
# 设置目标芯片
idf.py set-target esp32

# 编译
idf.py build

# 烧录和监控
idf.py -p PORT flash monitor
```

## 技术栈

- ESP-IDF 5.x
- BLE GATT Server
- LEDC PWM
- FreeRTOS

## 后续扩展

- **UART 通信**: 与其他 MCU 通信
- **更多舵机**: 扩展到 4+ 舵机
- **动作录制**: 录制自定义动作

---

## 快速开始指南

### 1. 连接蓝牙

设备名称: **ESP_ROBOT**

使用手机 App (如 nRF Connect, LightBlue) 或电脑 BLE 工具扫描并连接。

### 2. GATT 服务结构

| 服务/特征 | UUID | 说明 |
|-----------|------|------|
| 主服务 | 0x00FF | |
| SERVO_CTRL (写) | 0xFF01 | 写入舵机指令 |
| ACTION_CTRL (写) | 0xFF02 | 写入动作指令 |
| STATUS (通知) | 0xFF03 | 接收状态反馈 |

### 3. 控制命令

#### 模式1：平滑跟踪（转盘/滑块控制）

写入特征值 **0xFF01**：

```
# 设置X轴(舵机0)到90度
SET_SERVO:0:90

# 设置Y轴(舵机1)到120度
SET_SERVO:1:120
```

格式: `SET_SERVO:<舵机ID>:<角度>`

**工作原理**：
- 速度固定约67°/s（每15ms移动1°）
- 即使APP频繁发送命令，舵机也会平滑向最新目标移动
- 适合转盘、滑块等需要丝滑控制的场景

#### 模式2：时间控制（指定时间到达）

写入特征值 **0xFF01**：

```
# 500ms内到达90度
SET_SERVO:0:90:500

# 1000ms内到达120度
SET_SERVO:1:120:1000
```

格式: `SET_SERVO:<舵机ID>:<角度>:<时间ms>`

**工作原理**：
- 时间范围：50ms - 5000ms
- 速度动态计算，保证在指定时间内到达
- 适合动作表演

#### 模式3：摇杆（持续移动）

写入特征值 **0xFF01**：

```
# 舵机0正向持续移动
SERVO_MOVE:0:1

# 舵机0反向持续移动
SERVO_MOVE:0:-1

# 停止舵机0移动
SERVO_MOVE:0:0
```

#### 播放预设动作

写入特征值 **0xFF01**：

```
# 播放动作0 (wave)
PLAY_ACTION:0

# 播放动作1 (greet)
PLAY_ACTION:1
```

### 4. 示例

使用 nRF Connect App:
1. 扫描连接 "ESP_ROBOT"
2. 点击服务右侧的七星图标（Discover Services）
3. 找到 "SERVO CTRL" 特征 (UUID: 0xFF01)
4. 点击右上角菜单，选择 **"Write Request"**（不是 Write Without Response）
5. 输入命令：`SET_SERVO:1:110`
6. 在底部文本框输入后点击发送按钮

**注意**：必须使用 "Write Request"，否则数据会被截断。

---

## 📦 Releases

Pre-built binaries are available in the [release/](release/) folder:

| File | Address |
|------|---------|
| `bootloader.bin` | 0x0000 |
| `partition-table.bin` | 0x8000 |
| `WatcherRobotBody.bin` | 0x10000 |

See [release/README.md](release/README.md) for flashing instructions.

---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
