| Supported Targets | ESP32 | ESP32-C2 | ESP32-C3 | ESP32-C6 | ESP32-H2 | ESP32-S3 |
| ----------------- | ----- | -------- | -------- | -------- | -------- | -------- |

# BLE 遥控机器人 (WatcherRobotBody)

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
| **servo** | PWM 舵机控制 (GPIO 18, 19) |
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

```
SET_SERVO:0:90    # 设置X轴(舵机0)到90度
SET_SERVO:1:120    # 设置Y轴(舵机1)到120度
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
- **平滑移动**: 使用 FreeRTOS 任务实现渐变移动
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

#### 设置舵机角度

写入特征值 **0xFF01**：

```
# 设置X轴(舵机0)到90度
SET_SERVO:0:90

# 设置Y轴(舵机1)到120度
SET_SERVO:1:120
```

格式: `SET_SERVO:<舵机ID>:<角度>`

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
