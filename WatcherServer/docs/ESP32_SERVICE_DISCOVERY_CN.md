# ESP32 服务发现方案调研报告

> **创建日期**: 2026-03-04
> **文档类型**: 技术调研
> **状态**: 待评审

---

## 一、背景与需求

### 1.1 背景

Watcher Server 通过局域网向 ESP32 提供 WebSocket 服务。当前 ESP32 使用硬编码 IP 方式连接服务器，存在以下问题：

| 问题场景 | 影响 |
|----------|------|
| 网关不支持固定 IP | 路由器重启后 IP 变化，ESP32 无法连接 |
| 切换网络环境 | 家里/公司不同网络，需要重新编码 IP |
| 多设备部署 | 每个 ESP32 需要单独配置 IP |

### 1.2 需求目标

实现 ESP32 自动发现局域网内的 Watcher Server，无需硬编码 IP 地址。

**核心功能**：
1. ESP32 启动后自动发现服务器
2. 服务器响应自身 IP 和端口
3. ESP32 自动建立 WebSocket 连接

---

## 二、技术方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **UDP 广播** | 简单直接、跨平台、延迟低、易调试 | 需要自己处理设备管理 | ⭐⭐⭐⭐⭐ |
| **mDNS** | 系统级支持、标准化、Apple/Android 原生支持 | ESP32 端稍复杂，依赖更多 | ⭐⭐⭐ |

**推荐方案**: UDP 广播 - 更适合当前项目，实现简单且跨平台兼容性好。

---

## 三、技术架构设计

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         局域网 (LAN)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────────┐                    ┌─────────────────┐    │
│   │     ESP32       │                    │  Watcher Server │    │
│   │                 │                    │   (Python)      │    │
│   │  ┌───────────┐  │   ① UDP Broadcast  │  ┌───────────┐  │    │
│   │  │ UDP Client│  │ ─────────────────>│  │ UDP Server│  │    │
│   │  └───────────┘  │   {"cmd":"DISCOVER"}│  └───────────┘  │    │
│   │                 │                    │                 │    │
│   │  ┌───────────┐  │   ② UDP Unicast    │  ┌───────────┐  │    │
│   │  │           │  │ <───────────────── │  │ Parse &   │  │    │
│   │  │           │  │   {"ip":"...",    │  │ Respond   │  │    │
│   │  │           │  │    "port":8765}    │  │           │  │    │
│   │  └───────────┘  │                    │  └───────────┘  │    │
│   │                 │                    │                 │    │
│   │  ┌───────────┐  │   ③ WebSocket Connect                 │    │
│   │  │WebSocket  │  │ ─────────────────────────────────────> │    │
│   │  │  Client   │  │                    │                 │    │
│   │  └───────────┘  │   ④ Connected!     │                 │    │
│   └─────────────────┘ ─────────────────────────────────────> │    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 发现流程

```
┌──────────┐                              ┌─────────────────┐
│  ESP32   │                              │ Watcher Server  │
└────┬─────┘                              └────────┬────────┘
     │                                             │
     │  ① 启动，连接 WiFi                           │
     │ ─────────────────────────────────────────> │
     │                                             │
     │  ② UDP Broadcast:                           │
     │     {"cmd":"DISCOVER",                      │
     │      "device_id":"esp32-001",               │
     │      "mac":"AA:BB:CC:DD:EE:FF"}             │
     │ ─────────────────────────────────────────> │
     │                                             │
     │                          ③ 解析，准备响应    │
     │<──────────────────────────────────────── ─ │
     │     {"cmd":"ANNOUNCE",                      │
     │      "ip":"192.168.1.100",                  │
     │      "port":8765,                           │
     │      "version":"1.0.0"}                     │
     │                                             │
     │  ④ 解析 IP 和端口                           │
     │                                             │
     │  ⑤ WebSocket 连接到 192.168.1.100:8765     │
     │ ─────────────────────────────────────────> │
     │                                             │
     │  ⑥ 连接成功，开始通信                        │
     │<─────────────────────────────────────────> │
```

### 3.3 消息格式

**发现请求（ESP32 → Server）:**
```json
{
  "cmd": "DISCOVER",
  "device_id": "esp32-001",
  "mac": "AA:BB:CC:DD:EE:FF"
}
```

**服务响应（Server → ESP32）:**
```json
{
  "cmd": "ANNOUNCE",
  "ip": "192.168.1.100",
  "port": 8765,
  "version": "1.0.0"
}
```

---

## 四、ESP32 端实现

### 4.1 可行性分析

**结论：完全可行**

ESP32 原生支持 UDP 广播，相关库：
- `WiFiUDP.h` - Arduino 标准库（同步）
- `AsyncUDP.h` - 异步库（推荐，性能更好）

### 4.2 硬件要求

| 项目 | 要求 |
|------|------|
| ESP32 型号 | 全系列支持 |
| Arduino 版本 | >= 1.0.0 |
| 必需库 | AsyncUDP (通过 Arduino IDE 安装) |

### 4.3 ESP32 代码实现

```cpp
/**
 * ESP32 服务发现客户端
 *
 * 功能：
 * 1. 连接 WiFi 后自动广播发现请求
 * 2. 监听服务器响应
 * 3. 自动连接到发现的服务器
 */

#include <WiFi.h>
#include <AsyncUDP.h>

// ==================== 配置区域 ====================
const char* WIFI_SSID = "your_wifi";
const char* WIFI_PASSWORD = "your_password";

const int DISCOVERY_PORT = 37020;
const int DISCOVERY_INTERVAL = 5000;  // 发现间隔 5 秒
const int DISCOVERY_RETRY_COUNT = 3;  // 重复发送次数

const int DEFAULT_WS_PORT = 8765;
// ===================================================

// 全局变量
AsyncUDP udp;
String serverIP = "";
int serverPort = DEFAULT_WS_PORT;
bool discovered = false;

/**
 * WiFi 连接初始化
 */
void initWiFi() {
  Serial.println("正在连接 WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✓ WiFi 已连接");
  Serial.print("  IP 地址: ");
  Serial.println(WiFi.localIP());
  Serial.print("  MAC 地址: ");
  Serial.println(WiFi.macAddress());
}

/**
 * 发送发现广播
 */
void sendDiscovery() {
  String mac = WiFi.macAddress();
  String deviceId = "esp32-" + mac.substring(9, 11) + mac.substring(12, 14);

  // 构建发现消息
  String msg = "{\"cmd\":\"DISCOVER\",\"device_id\":\"" + deviceId +
               "\",\"mac\":\"" + mac + "\"}";

  // 广播到局域网
  udp.broadcastTo(msg.c_str(), DISCOVERY_PORT);

  Serial.println("📡 发送发现广播: " + msg);
}

/**
 * 连接到 WebSocket 服务器
 */
void connectToServer() {
  if (serverIP.isEmpty()) {
    Serial.println("⚠  服务器 IP 未设置，无法连接");
    return;
  }

  Serial.println("🔗 正在连接服务器...");
  Serial.print("  地址: ");
  Serial.print(serverIP);
  Serial.print(":");
  Serial.println(serverPort);

  // TODO: 使用你的 WebSocket 库连接
  // webSocket.begin(serverIP.c_str(), serverPort, "/");
  // webSocket.onEvent(webSocketEvent);
}

/**
 * UDP 数据包回调处理
 */
void onUDPPacket(AsyncUDPPacket packet) {
  String msg = (char*)packet.data();
  msg = msg.substring(0, packet.length());

  Serial.println("📥 收到 UDP 数据: " + msg);
  Serial.println("   来自: " + packet.remoteIP().toString());

  // 解析响应
  if (msg.indexOf("\"cmd\":\"ANNOUNCE\"") >= 0) {
    // 提取 IP
    int ipIdx = msg.indexOf("\"ip\":");
    if (ipIdx > 0) {
      int start = msg.indexOf("\"", ipIdx + 6) + 1;
      int end = msg.indexOf("\"", start);
      serverIP = msg.substring(start, end);
    }

    // 提取端口
    int portIdx = msg.indexOf("\"port\":");
    if (portIdx > 0) {
      int start = portIdx + 7;
      int end = msg.indexOf(",", start);
      if (end < 0) end = msg.indexOf("}", start);
      serverPort = msg.substring(start, end).toInt();
    }

    discovered = true;

    Serial.println("✓ 发现服务器!");
    Serial.print("  IP: ");
    Serial.println(serverIP);
    Serial.print("  端口: ");
    Serial.println(serverPort);

    // 连接到服务器
    connectToServer();
  }
}

/**
 * 发现任务（FreeRTOS）
 */
void discoveryTask(void* pvParameters) {
  int retryCount = 0;

  while (!discovered) {
    if (WiFi.status() == WL_CONNECTED) {
      // 重复发送以提高可靠性
      for (int i = 0; i < DISCOVERY_RETRY_COUNT; i++) {
        sendDiscovery();
        vTaskDelay(pdMS_TO_TICKS(500));  // 间隔 500ms
      }

      retryCount++;
      Serial.println("⏳ 等待服务器响应... (" + String(retryCount) + ")");

      // 等待下一个发现周期
      vTaskDelay(pdMS_TO_TICKS(DISCOVERY_INTERVAL));
    } else {
      // WiFi 断开，尝试重连
      Serial.println("⚠  WiFi 断开，尝试重连...");
      WiFi.reconnect();
      vTaskDelay(pdMS_TO_TICKS(5000));
    }
  }

  Serial.println("✓ 发现完成，任务结束");
  vTaskDelete(NULL);
}

/**
 * 设置函数
 */
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n========================================");
  Serial.println("   ESP32 服务发现客户端");
  Serial.println("========================================\n");

  // 初始化 WiFi
  initWiFi();

  // 启动 UDP 监听
  if (udp.listen(DISCOVERY_PORT)) {
    Serial.println("✓ UDP 监听已启动，端口: " + String(DISCOVERY_PORT));
    udp.onPacket(onUDPPacket);
  } else {
    Serial.println("✗ UDP 监听启动失败");
    return;
  }

  // 启动发现任务
  xTaskCreate(
    discoveryTask,      // 任务函数
    "Discovery",        // 任务名称
    4096,              // 堆栈大小
    NULL,              // 参数
    1,                 // 优先级
    NULL               // 任务句柄
  );

  Serial.println("✓ 服务发现已启动\n");
}

/**
 * 主循环
 */
void loop() {
  // WebSocket 事件处理
  // webSocket.loop();

  delay(100);
}
```

### 4.4 ESP32 安装依赖

在 Arduino IDE 中安装 `AsyncUDP` 库：

1. 打开 Arduino IDE
2. 点击 `工具` → `管理库`
3. 搜索 `AsyncUDP`
4. 点击安装

---

## 五、Python 服务器端实现

### 5.1 文件结构

```
watcher-server/
├── src/
│   ├── modules/
│   │   └── discovery/
│   │       ├── __init__.py
│   │       └── discovery_server.py    # UDP 发现服务器
│   └── core/
│       └── websocket_server.py         # 集成发现服务
```

### 5.2 发现服务器实现

```python
# src/modules/discovery/__init__.py
"""服务发现模块"""

from .discovery_server import DiscoveryServer

__all__ = ["DiscoveryServer"]
```

```python
# src/modules/discovery/discovery_server.py
"""UDP 服务发现服务器

功能：
1. 监听 ESP32 的发现请求
2. 响应服务器 IP 和 WebSocket 端口
3. 记录已发现的设备
"""

import asyncio
import json
import socket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DiscoveredDevice:
    """已发现的设备信息"""
    device_id: str
    mac: str
    last_seen: datetime
    ip: str = ""


class DiscoveryServer:
    """UDP 服务发现服务器

    监听局域网内的设备发现请求，并响应服务器信息
    """

    def __init__(self, port: int = None, ws_port: int = None):
        """初始化发现服务器

        Args:
            port: UDP 监听端口，默认从配置读取
            ws_port: WebSocket 服务端口，默认从配置读取
        """
        self.port = port or getattr(settings, 'discovery_port', 37020)
        self.ws_port = ws_port or settings.ws_port

        # UDP 传输层
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.protocol: Optional["DiscoveryProtocol"] = None

        # 本机 IP
        self._local_ip: str = "127.0.0.1"

        # 已发现的设备记录
        self._discovered_devices: Dict[str, DiscoveredDevice] = {}

        logger.info(f"发现服务器初始化: udp_port={self.port}, ws_port={self.ws_port}")

    async def get_local_ip(self) -> str:
        """获取本机局域网 IP 地址

        通过连接到外部地址来获取本地 IP

        Returns:
            str: 本机 IP 地址
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            # 连接到 Google DNS（不会实际发送数据）
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.warning(f"获取本机 IP 失败，使用默认值: {e}")
            return "127.0.0.1"

    async def start(self):
        """启动发现服务器"""
        self._local_ip = await self.get_local_ip()

        loop = asyncio.get_event_loop()

        # 创建 UDP endpoint
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self),
            local_addr=('0.0.0.0', self.port),
            reuse_address=True
        )

        logger.info(f"✓ 服务发现服务器已启动")
        logger.info(f"  监听地址: 0.0.0.0:{self.port}")
        logger.info(f"  本机 IP: {self._local_ip}")
        logger.info(f"  WebSocket 端口: {self.ws_port}")

    async def stop(self):
        """停止发现服务器"""
        if self.transport:
            self.transport.close()
            logger.info("服务发现服务器已停止")

    def create_response(self) -> bytes:
        """创建服务响应消息

        Returns:
            bytes: JSON 格式的响应消息
        """
        response = {
            "cmd": "ANNOUNCE",
            "ip": self._local_ip,
            "port": self.ws_port,
            "version": "1.0.0",
            "server": "watcher-server"
        }
        return json.dumps(response, ensure_ascii=False).encode('utf-8')

    def register_device(self, device_id: str, mac: str, ip: str):
        """注册发现的设备

        Args:
            device_id: 设备 ID
            mac: MAC 地址
            ip: 设备 IP
        """
        self._discovered_devices[device_id] = DiscoveredDevice(
            device_id=device_id,
            mac=mac,
            last_seen=datetime.now(),
            ip=ip
        )
        logger.info(f"注册设备: {device_id} ({ip})")

    def get_discovered_devices(self) -> list:
        """获取已发现的设备列表

        Returns:
            list: 设备信息列表
        """
        return [
            {
                "device_id": dev.device_id,
                "mac": dev.mac,
                "ip": dev.ip,
                "last_seen": dev.last_seen.isoformat()
            }
            for dev in self._discovered_devices.values()
        ]


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """UDP 协议处理器

    处理接收到的 UDP 数据包
    """

    def __init__(self, server: DiscoveryServer):
        """初始化协议处理器

        Args:
            server: 发现服务器实例
        """
        self.server = server
        self.logger = get_logger(__name__)

    def connection_made(self, transport):
        """连接建立时的回调"""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple):
        """接收到 UDP 数据包

        Args:
            data: 接收到的数据
            addr: 发送方地址 (ip, port)
        """
        try:
            # 解析 JSON 消息
            message = json.loads(data.decode('utf-8'))

            # 检查是否为发现请求
            if message.get('cmd') == 'DISCOVER':
                self._handle_discovery(message, addr)
            else:
                self.logger.debug(f"未知命令: {message.get('cmd')}")

        except json.JSONDecodeError as e:
            self.logger.warning(f"无效的 JSON 数据: {data[:100]}...")
        except Exception as e:
            self.logger.error(f"处理数据包失败: {e}", exc_info=True)

    def _handle_discovery(self, message: dict, addr: tuple):
        """处理发现请求

        Args:
            message: 解析后的消息
            addr: 发送方地址 (ip, port)
        """
        device_id = message.get('device_id', 'unknown')
        mac = message.get('mac', '')

        self.logger.info(f"📡 收到发现请求: device_id={device_id}, mac={mac}, from={addr[0]}")

        # 注册设备
        self.server.register_device(device_id, mac, addr[0])

        # 发送响应（单播到设备 IP，避免广播风暴）
        response = self.server.create_response()
        self.transport.sendto(response, addr)

        self.logger.debug(f"📤 发送服务响应到 {addr[0]}:{addr[1]}")

    def error_received(self, exc):
        """接收错误时的回调"""
        self.logger.error(f"UDP 错误: {exc}")
```

### 5.3 集成到 WebSocket 服务器

```python
# src/core/websocket_server.py 添加以下内容

from src.modules.discovery import DiscoveryServer

class WebSocketServer:
    """WebSocket 服务器（集成服务发现）"""

    def __init__(self):
        # ... 原有代码 ...

        # 服务发现服务器
        self.discovery_server: Optional[DiscoveryServer] = None

    async def start(self):
        """启动服务器"""
        # ... 原有启动代码 ...

        # 启动发现服务器
        discovery_enabled = getattr(settings, 'discovery_enabled', True)
        if discovery_enabled:
            self.discovery_server = DiscoveryServer()
            await self.discovery_server.start()

    async def cleanup(self):
        """清理资源"""
        # 停止发现服务器
        if self.discovery_server:
            await self.discovery_server.stop()

        # ... 原有清理代码 ...
```

### 5.4 配置文件更新

```python
# src/config/env.py 添加以下配置

class Settings(BaseSettings):
    # ... 原有配置 ...

    # ========== 服务发现配置 ==========
    discovery_enabled: bool = Field(
        default=True,
        description="是否启用服务发现"
    )
    discovery_port: int = Field(
        default=37020,
        description="UDP 发现端口"
    )
```

### 5.5 环境变量配置

```bash
# .env 文件添加

# 服务发现配置
DISCOVERY_ENABLED=true
DISCOVERY_PORT=37020
```

---

## 六、测试方案

### 6.1 ESP32 端测试

1. 烧录代码到 ESP32
2. 打开串口监视器（115200 波特率）
3. 观察日志输出：

```
========================================
   ESP32 服务发现客户端
========================================

✓ WiFi 已连接
  IP 地址: 192.168.1.50
  MAC 地址: AA:BB:CC:DD:EE:FF
✓ UDP 监听已启动，端口: 37020
✓ 服务发现已启动

📡 发送发现广播: {"cmd":"DISCOVER","device_id":"esp32-EF:FF","mac":"AA:BB:CC:DD:EE:FF"}
⏳ 等待服务器响应... (1)
📥 收到 UDP 数据: {"cmd":"ANNOUNCE","ip":"192.168.1.100","port":8765,"version":"1.0.0"}
   来自: 192.168.1.100
✓ 发现服务器!
  IP: 192.168.1.100
  端口: 8765
🔗 正在连接服务器...
  地址: 192.168.1.100:8765
✓ 发现完成，任务结束
```

### 6.2 服务器端测试

1. 启动 Watcher Server
2. 观察 Python 日志：

```
INFO - 发现服务器初始化: udp_port=37020, ws_port=8765
INFO - ✓ 服务发现服务器已启动
INFO -   监听地址: 0.0.0.0:37020
INFO -   本机 IP: 192.168.1.100
INFO -   WebSocket 端口: 8765

INFO - 📡 收到发现请求: device_id=esp32-EF:FF, mac=AA:BB:CC:DD:EE:FF, from=192.168.1.50
INFO - 注册设备: esp32-EF:FF (192.168.1.50)
INFO - 📤 发送服务响应到 192.168.1.50:xxxxx: {...}
```

### 6.3 Windows/macOS 客户端测试

在没有 ESP32 的情况下，可以用电脑模拟客户端进行测试。

#### 6.3.1 Windows 测试

**前置条件**：
- 确保 Windows 和服务器在同一局域网
- 确认服务器的局域网 IP 地址（服务器日志会显示）

**方法一：使用 Python 脚本**

1. 启动 Watcher Server，确认日志显示的本机 IP（如 `192.168.31.66`）

2. 在 Windows CMD 中运行：

```cmd
python -c "import socket,json; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1); s.sendto(json.dumps({'cmd':'DISCOVER'}).encode(),('192.168.31.255',37020)); print('已发送'); s.settimeout(3); print(s.recv(1024).decode())"
```

> 注意：将 `192.168.31.255` 替换为你的子网广播地址（将 IP 最后一位改为 255）

**方法二：PowerShell 一行命令**

```powershell
$client = New-Object System.Net.Sockets.UdpClient; $client.EnableBroadcast = $true; $endpoint = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Broadcast, 37020); $bytes = [System.Text.Encoding]::ASCII.GetBytes('{"cmd":"DISCOVER"}'); $client.Send($bytes, $bytes.Length, $endpoint) | Out-Null; $client.Receive($endpoint); [System.Text.Encoding]::ASCII.GetString($client.Receive($endpoint)) | Write-Output
```

**预期输出**：
```
已发送
{"cmd": "ANNOUNCE", "ip": "192.168.31.66", "port": 8765, "version": "1.0.0", "server": "watcher-server"}
```

#### 6.3.2 macOS 测试

**方法一：使用 Python**

```bash
python -c "
import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# 发送广播
broadcast_ip = '192.168.31.255'  # 替换为你的子网广播地址
msg = json.dumps({'cmd': 'DISCOVER'})
s.sendto(msg.encode(), (broadcast_ip, 37020))
print('已发送广播')

# 等待响应
s.settimeout(3)
try:
    data, addr = s.recvfrom(1024)
    print(f'收到响应 from {addr}:')
    print(data.decode())
except:
    print('超时')
s.close()
```

**方法二：使用 netcat 监听**

1. 在 macOS 上监听 UDP 端口：
```bash
nc -lu 37020
```

2. 从另一台电脑发送广播，应该能看到 `{"cmd":"DISCOVER"}`

#### 6.3.3 查找正确的广播地址

如果测试失败，可能是因为广播地址不正确。

**计算广播地址**：
- 假设服务器 IP 是 `192.168.31.66`
- 子网掩码通常是 `255.255.255.0`
- 广播地址 = `192.168.31.255`

**快速测试**：直接发送到服务器 IP（不使用广播）

```cmd
# Windows - 直接发送到服务器 IP
python -c "import socket,json; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.sendto(json.dumps({'cmd':'DISCOVER'}).encode(),('192.168.31.66',37020)); s.settimeout(3); print(s.recv(1024).decode())"
```

```bash
# macOS/Linux - 直接发送到服务器 IP
echo '{"cmd":"DISCOVER"}' | nc -u 192.168.31.66 37020
```

### 6.4 网络抓包验证

使用 Wireshark 抓包验证：

```
# 过滤器
udp.port == 37020

# 预期数据包
1. ESP32 → 255.255.255.255: {"cmd":"DISCOVER",...}
2. Server → ESP32: {"cmd":"ANNOUNCE",...}
```

---

## 七、优化建议

### 7.1 可靠性优化

| 优化项 | 方案 | 说明 |
|--------|------|------|
| 重复发送 | ESP32 启动后发送 3-5 次 | 间隔 500ms，提高成功率 |
| 超时处理 | 30 秒未发现则告警 | 避免无限等待 |
| 重连机制 | WebSocket 断开后重新发现 | 提高连接稳定性 |

### 7.2 安全性考虑

| 风险 | 防护措施 |
|------|----------|
| 中间人攻击 | 添加设备认证（共享密钥） |
| 未授权访问 | 设备白名单机制 |
| 信息泄露 | 敏感信息加密传输 |

### 7.3 功能扩展

1. **多服务器支持**: 响应可用服务器列表，让 ESP32 选择
2. **负载均衡**: 根据服务器负载分配连接
3. **心跳保活**: 定期确认设备在线状态
4. **远程配置**: 通过 UDP 广播更新 ESP32 配置

---

## 八、替代方案：mDNS

如果未来需要更标准化的解决方案，可以考虑 mDNS（Multicast DNS）：

### ESP32 端
```cpp
#include <ESPmDNS.h>

void setup() {
  // 启动 mDNS
  if (!MDNS.begin("watcher-esp32")) {
    Serial.println("mDNS 启动失败");
    return;
  }

  // 广播 WebSocket 服务
  MDNS.addService("websocket", "tcp", 8765);
}
```

### Python 端
```python
from zeroconf import ServiceBrowser, Zeroconf

class Listener:
    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        ip = socket.inet_ntoa(info.addresses[0])
        print(f"发现设备: {name} → {ip}:{info.port}")

zeroconf = Zeroconf()
browser = ServiceBrowser(zeroconf, "_websocket._tcp.local.", Listener())
```

---

## 九、实施计划

| 阶段 | 任务 | 预计工时 |
|------|------|----------|
| **Phase 1** | Python 服务器实现 | 2 小时 |
| **Phase 2** | ESP32 代码开发 | 3 小时 |
| **Phase 3** | 联调测试 | 2 小时 |
| **Phase 4** | 文档更新 | 1 小时 |
| **总计** | - | **8 小时** |

---

## 十、参考资源

### 文档与教程
- [ESP32 AsyncUDP Library](https://github.com/me-no-dev/AsyncUDP)
- [ESP32 mDNS Tutorial - Random Nerd Tutorials](https://randomnerdtutorials.com/esp32-mdns/)
- [Python AsyncIO UDP](https://docs.python.org/3/library/asyncio-stream.html)

### 相关标准
- RFC 6762 - Multicast DNS
- RFC 6763 - DNS-Based Service Discovery

---

## 附录：故障排查

### 问题 1: ESP32 无法接收到响应

**可能原因**：
1. 防火墙阻止 UDP 端口
2. ESP32 和服务器不在同一网段
3. 路由器禁用广播转发

**排查方法**：
```bash
# 检查防火墙
sudo ufw status

# 测试 UDP 端口
nc -lu 37020
```

### 问题 2: 服务器无法获取正确的局域网 IP

**解决方案**：
```python
# 方法 1：通过网卡枚举
import netifaces
for interface in netifaces.interfaces():
    if interface != 'lo':
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            ip = addrs[netifaces.AF_INET][0]['addr']
            if not ip.startswith('127.'):
                return ip
```

### 问题 3: 多个 ESP32 同时启动导致网络拥塞

**优化方案**：
```cpp
// 随机延迟启动，避免同时广播
void setup() {
  delay(random(0, 5000));  // 0-5 秒随机延迟
  // ... 其余代码
}
```

---

**文档版本**: v1.0
**最后更新**: 2026-03-04
