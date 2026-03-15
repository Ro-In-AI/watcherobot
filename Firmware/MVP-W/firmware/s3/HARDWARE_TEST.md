# MVP-W S3 硬件测试清单

## 测试环境

- 目标: ESP32-S3 (Watcher 硬件)
- 烧录命令: `idf.py -p COM3 flash monitor` (根据实际 COM 口调整)

---

## 测试项目

### 1. 启动测试 (TEST_BOOT)

**目的**: 验证固件能否正常启动

**步骤**:
1. 连接串口监视器
2. 按下 RST 复位按钮
3. 观察日志输出

**预期结果**:
```
I (xxx) MAIN: MVP-W S3 v1.0 starting
I (xxx) HAL_DISPLAY: Display initialized (stub)
I (xxx) HAL_UART: UART initialized (TX:19 RX:20 @ 115200)
I (xxx) HAL_AUDIO: Audio initialized
I (xxx) WIFI: Connecting to <SSID>...
I (xxx) WIFI: Connected
I (xxx) WS_CLIENT: WebSocket client initialized
I (xxx) MAIN: Ready
```

**状态**: [ ] 通过 [ ] 失败

---

### 2. UART 发送测试 (TEST_UART_TX)

**目的**: 验证 S3 → MCU UART 发送

**前置条件**:
- MCU 已烧录并运行
- S3 TX (GPIO 19) 连接 MCU RX (GPIO 16)
- S3 RX (GPIO 20) 连接 MCU TX (GPIO 17)
- GND 共地

**步骤**:
1. 在 S3 日志中观察 UART 初始化
2. 手动发送测试命令 (可通过串口输入或代码触发)
3. 在 MCU 日志中观察是否收到 `X:90\r\nY:90\r\n`

**预期结果**:
- S3: `I (xxx) HAL_UART: UART initialized (TX:19 RX:20 @ 115200)`
- MCU: 收到并解析舵机指令

**状态**: [ ] 通过 [ ] 失败

---

### 3. WiFi 连接测试 (TEST_WIFI)

**目的**: 验证 WiFi 连接功能

**前置条件**:
- 路由器已开启
- SSID/密码已在 `wifi_client.c` 中配置

**步骤**:
1. 观察启动日志
2. 检查是否获取到 IP 地址

**预期结果**:
```
I (xxx) WIFI: Connecting to <SSID>...
I (xxx) wifi:connected
I (xxx) WIFI: Got IP: 192.168.x.x
```

**状态**: [ ] 通过 [ ] 失败

---

### 4. WebSocket 连接测试 (TEST_WS)

**目的**: 验证 WebSocket 客户端连接

**前置条件**:
- WiFi 已连接
- 云端服务器运行在 `ws://192.168.1.100:8766`

**步骤**:
1. 启动云端 WebSocket 服务器
2. 观察 S3 连接日志

**预期结果**:
```
I (xxx) WS_CLIENT: WebSocket client initialized
I (xxx) WS_CLIENT: WebSocket connected
```

**状态**: [ ] 通过 [ ] 失败 (需要云端服务器)

---

### 5. I2S 音频测试 (TEST_AUDIO)

**目的**: 验证 I2S 麦克风/喇叭初始化

**步骤**:
1. 观察启动日志
2. 检查 I2S 初始化是否成功

**预期结果**:
```
I (xxx) HAL_AUDIO: Audio initialized
```

**注意**: 完整音频测试需要 Opus 编解码器和云端配合

**状态**: [ ] 通过 [ ] 失败

---

### 6. 显示屏测试 (TEST_DISPLAY)

**目的**: 验证显示屏通信

**当前状态**: HAL 是 Stub 实现，需要集成 LVGL

**预期结果**:
- 屏幕显示 "Starting..."
- 屏幕显示 "Connecting WiFi..."
- 屏幕显示 "Ready"

**状态**: [ ] 待实现 LVGL 集成

---

## 快速测试命令

### 手动 UART 测试

在 `app_main.c` 中添加测试代码：

```c
// After uart_bridge_init()
ESP_LOGI(TAG, "Testing UART TX...");
uart_bridge_send_servo(90, 90);
vTaskDelay(pdMS_TO_TICKS(1000));
uart_bridge_send_servo(90, 90);
```

### 串口命令测试 (可选)

添加串口命令处理：

```c
// In main loop
uint8_t buf[64];
int len = uart_read_bytes(UART_NUM_0, buf, sizeof(buf)-1, pdMS_TO_TICKS(100));
if (len > 0) {
    buf[len] = '\0';
    ESP_LOGI(TAG, "Received: %s", buf);
    // Parse and execute test commands
}
```

---

## 测试结果汇总

| 测试项 | 状态 | 备注 |
|--------|------|------|
| TEST_BOOT | | |
| TEST_UART_TX | | |
| TEST_WIFI | | |
| TEST_WS | | |
| TEST_AUDIO | | |
| TEST_DISPLAY | | |

---

## 常见问题

### Q: 烧录失败
A: 检查 GPIO 19/20 是否与 MCU 断开（烧录时需断开）

### Q: WiFi 连接失败
A: 检查 SSID/密码配置，确认路由器 2.4GHz 频段

### Q: UART 无输出
A: 检查波特率 (115200)，确认 TX/RX 接线正确

---

*文档版本: 1.0*
*创建日期: 2026-02-27*
