[English](ESP32_SERVICE_DISCOVERY.md) | [中文](ESP32_SERVICE_DISCOVERY_CN.md)

# ESP32 Service Discovery Research Report

> **Created**: 2026-03-04
> **Document Type**: Technical Research
> **Status**: Pending Review

---

## 1. Background and Requirements

### 1.1 Background

Watcher Server provides WebSocket services to ESP32 over LAN. Currently, ESP32 uses hardcoded IP to connect to the server, which has the following problems:

| Problem Scenario | Impact |
|-----------------|--------|
| Gateway doesn't support fixed IP | IP changes after router restart, ESP32 cannot connect |
| Switching network environments | Different networks at home/office require recompilation with new IP |
| Multi-device deployment | Each ESP32 requires separate IP configuration |

### 1.2 Requirements Goal

Implement automatic discovery of Watcher Server by ESP32 in LAN without hardcoded IP addresses.

**Core Functions**:
1. ESP32 automatically discovers server after startup
2. Server responds with its IP and port
3. ESP32 automatically establishes WebSocket connection

---

## 2. Technical Solution Comparison

| Solution | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **UDP Broadcast** | Simple, cross-platform, low latency, easy debugging | Need to handle device management yourself | ⭐⭐⭐⭐⭐ |
| **mDNS** | System-level support, standardized, native Apple/Android support | Slightly more complex on ESP32, more dependencies | ⭐⭐⭐ |

**Recommended Solution**: UDP Broadcast - More suitable for current project, simple implementation with good cross-platform compatibility.

---

## 3. Technical Architecture Design

### 3.1 Overall Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         LAN                                      │
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

### 3.2 Discovery Flow

```
┌──────────┐                              ┌─────────────────┐
│  ESP32   │                              │ Watcher Server  │
└────┬─────┘                              └────────┬────────┘
     │                                             │
     │  ① Start, connect WiFi                     │
     │ ─────────────────────────────────────────> │
     │                                             │
     │  ② UDP Broadcast:                          │
     │     {"cmd":"DISCOVER",                      │
     │      "device_id":"esp32-001",               │
     │      "mac":"AA:BB:CC:DD:EE:FF"}             │
     │ ─────────────────────────────────────────> │
     │                                             │
     │                          ③ Parse, prepare response
     │<──────────────────────────────────────── ─ │
     │     {"cmd":"ANNOUNCE",                      │
     │      "ip":"192.168.1.100",                  │
     │      "port":8765,                           │
     │      "version":"1.0.0"}                     │
     │                                             │
     │  ④ Parse IP and port                       │
     │                                             │
     │  ⑤ WebSocket connect to 192.168.1.100:8765 │
     │ ─────────────────────────────────────────> │
     │                                             │
     │  ⑥ Connection successful, start communication
     │<─────────────────────────────────────────> │
```

### 3.3 Message Format

**Discovery Request (ESP32 → Server):**
```json
{
  "cmd": "DISCOVER",
  "device_id": "esp32-001",
  "mac": "AA:BB:CC:DD:EE:FF"
}
```

**Service Response (Server → ESP32):**
```json
{
  "cmd": "ANNOUNCE",
  "ip": "192.168.1.100",
  "port": 8765,
  "version": "1.0.0"
}
```

---

## 4. ESP32 Implementation

### 4.1 Feasibility Analysis

**Conclusion: Fully Feasible**

ESP32 natively supports UDP broadcast, related libraries:
- `WiFiUDP.h` - Arduino standard library (synchronous)
- `AsyncUDP.h` - Async library (recommended, better performance)

### 4.2 Hardware Requirements

| Item | Requirement |
|------|-------------|
| ESP32 Model | Full series supported |
| Arduino Version | >= 1.0.0 |
| Required Library | AsyncUDP (installed via Arduino IDE) |

### 4.3 ESP32 Code Implementation

```cpp
/**
 * ESP32 Service Discovery Client
 *
 * Functions:
 * 1. Auto broadcast discovery request after WiFi connection
 * 2. Listen for server response
 * 3. Auto connect to discovered server
 */

#include <WiFi.h>
#include <AsyncUDP.h>

// ==================== Configuration ====================
const char* WIFI_SSID = "your_wifi";
const char* WIFI_PASSWORD = "your_password";

const int DISCOVERY_PORT = 37020;
const int DISCOVERY_INTERVAL = 5000;  // Discovery interval 5 seconds
const int DISCOVERY_RETRY_COUNT = 3;  // Retry count

const int DEFAULT_WS_PORT = 8765;
// ===================================================

// Global variables
AsyncUDP udp;
String serverIP = "";
int serverPort = DEFAULT_WS_PORT;
bool discovered = false;

/**
 * WiFi connection initialization
 */
void initWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("  IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("  MAC Address: ");
  Serial.println(WiFi.macAddress());
}

/**
 * Send discovery broadcast
 */
void sendDiscovery() {
  String mac = WiFi.macAddress();
  String deviceId = "esp32-" + mac.substring(9, 11) + mac.substring(12, 14);

  // Build discovery message
  String msg = "{\"cmd\":\"DISCOVER\",\"device_id\":\"" + deviceId +
               "\",\"mac\":\"" + mac + "\"}";

  // Broadcast to LAN
  udp.broadcastTo(msg.c_str(), DISCOVERY_PORT);

  Serial.println("Sent discovery broadcast: " + msg);
}

/**
 * Connect to WebSocket server
 */
void connectToServer() {
  if (serverIP.isEmpty()) {
    Serial.println("Server IP not set, cannot connect");
    return;
  }

  Serial.println("Connecting to server...");
  Serial.print("  Address: ");
  Serial.print(serverIP);
  Serial.print(":");
  Serial.println(serverPort);

  // TODO: Use your WebSocket library to connect
  // webSocket.begin(serverIP.c_str(), serverPort, "/");
  // webSocket.onEvent(webSocketEvent);
}

/**
 * UDP packet callback handler
 */
void onUDPPacket(AsyncUDPPacket packet) {
  String msg = (char*)packet.data();
  msg = msg.substring(0, packet.length());

  Serial.println("Received UDP data: " + msg);
  Serial.println("  From: " + packet.remoteIP().toString());

  // Parse response
  if (msg.indexOf("\"cmd\":\"ANNOUNCE\"") >= 0) {
    // Extract IP
    int ipIdx = msg.indexOf("\"ip\":");
    if (ipIdx > 0) {
      int start = msg.indexOf("\"", ipIdx + 6) + 1;
      int end = msg.indexOf("\"", start);
      serverIP = msg.substring(start, end);
    }

    // Extract port
    int portIdx = msg.indexOf("\"port\":");
    if (portIdx > 0) {
      int start = portIdx + 7;
      int end = msg.indexOf(",", start);
      if (end < 0) end = msg.indexOf("}", start);
      serverPort = msg.substring(start, end).toInt();
    }

    discovered = true;

    Serial.println("Server discovered!");
    Serial.print("  IP: ");
    Serial.println(serverIP);
    Serial.print("  Port: ");
    Serial.println(serverPort);

    // Connect to server
    connectToServer();
  }
}

/**
 * Discovery task (FreeRTOS)
 */
void discoveryTask(void* pvParameters) {
  int retryCount = 0;

  while (!discovered) {
    if (WiFi.status() == WL_CONNECTED) {
      // Retry to improve reliability
      for (int i = 0; i < DISCOVERY_RETRY_COUNT; i++) {
        sendDiscovery();
        vTaskDelay(pdMS_TO_TICKS(500));  // 500ms interval
      }

      retryCount++;
      Serial.println("Waiting for server response... (" + String(retryCount) + ")");

      // Wait for next discovery cycle
      vTaskDelay(pdMS_TO_TICKS(DISCOVERY_INTERVAL));
    } else {
      // WiFi disconnected, try reconnect
      Serial.println("WiFi disconnected, trying to reconnect...");
      WiFi.reconnect();
      vTaskDelay(pdMS_TO_TICKS(5000));
    }
  }

  Serial.println("Discovery complete, task ending");
  vTaskDelete(NULL);
}

/**
 * Setup function
 */
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n========================================");
  Serial.println("   ESP32 Service Discovery Client");
  Serial.println("========================================\n");

  // Initialize WiFi
  initWiFi();

  // Start UDP listener
  if (udp.listen(DISCOVERY_PORT)) {
    Serial.println("UDP listener started, port: " + String(DISCOVERY_PORT));
    udp.onPacket(onUDPPacket);
  } else {
    Serial.println("Failed to start UDP listener");
    return;
  }

  // Start discovery task
  xTaskCreate(
    discoveryTask,      // Task function
    "Discovery",        // Task name
    4096,              // Stack size
    NULL,              // Parameters
    1,                 // Priority
    NULL               // Task handle
  );

  Serial.println("Service discovery started\n");
}

/**
 * Main loop
 */
void loop() {
  // WebSocket event handling
  // webSocket.loop();

  delay(100);
}
```

### 4.4 ESP32 Install Dependencies

Install `AsyncUDP` library in Arduino IDE:

1. Open Arduino IDE
2. Click `Tools` → `Manage Libraries`
3. Search for `AsyncUDP`
4. Click Install

---

## 5. Python Server Implementation

### 5.1 File Structure

```
watcher-server/
├── src/
│   ├── modules/
│   │   └── discovery/
│   │       ├── __init__.py
│   │       └── discovery_server.py    # UDP discovery server
│   └── core/
│       └── websocket_server.py         # Integrate discovery service
```

### 5.2 Discovery Server Implementation

```python
# src/modules/discovery/__init__.py
"""Service discovery module"""

from .discovery_server import DiscoveryServer

__all__ = ["DiscoveryServer"]
```

```python
# src/modules/discovery/discovery_server.py
"""UDP Service Discovery Server

Functions:
1. Listen for ESP32 discovery requests
2. Respond with server IP and WebSocket port
3. Record discovered devices
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
    """Discovered device information"""
    device_id: str
    mac: str
    last_seen: datetime
    ip: str = ""


class DiscoveryServer:
    """UDP Service Discovery Server

    Listen for device discovery requests in LAN and respond with server information
    """

    def __init__(self, port: int = None, ws_port: int = None):
        """Initialize discovery server

        Args:
            port: UDP listening port, default from config
            ws_port: WebSocket service port, default from config
        """
        self.port = port or getattr(settings, 'discovery_port', 37020)
        self.ws_port = ws_port or settings.ws_port

        # UDP transport layer
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.protocol: Optional["DiscoveryProtocol"] = None

        # Local IP
        self._local_ip: str = "127.0.0.1"

        # Discovered devices record
        self._discovered_devices: Dict[str, DiscoveredDevice] = {}

        logger.info(f"Discovery server initialized: udp_port={self.port}, ws_port={self.ws_port}")

    async def get_local_ip(self) -> str:
        """Get local LAN IP address

        Get local IP by connecting to external address

        Returns:
            str: Local IP address
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            # Connect to Google DNS (won't actually send data)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.warning(f"Failed to get local IP, using default: {e}")
            return "127.0.0.1"

    async def start(self):
        """Start discovery server"""
        self._local_ip = await self.get_local_ip()

        loop = asyncio.get_event_loop()

        # Create UDP endpoint
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self),
            local_addr=('0.0.0.0', self.port),
            reuse_address=True
        )

        logger.info(f"Discovery server started")
        logger.info(f"  Listening address: 0.0.0.0:{self.port}")
        logger.info(f"  Local IP: {self._local_ip}")
        logger.info(f"  WebSocket port: {self.ws_port}")

    async def stop(self):
        """Stop discovery server"""
        if self.transport:
            self.transport.close()
            logger.info("Discovery server stopped")

    def create_response(self) -> bytes:
        """Create service response message

        Returns:
            bytes: JSON formatted response message
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
        """Register discovered device

        Args:
            device_id: Device ID
            mac: MAC address
            ip: Device IP
        """
        self._discovered_devices[device_id] = DiscoveredDevice(
            device_id=device_id,
            mac=mac,
            last_seen=datetime.now(),
            ip=ip
        )
        logger.info(f"Device registered: {device_id} ({ip})")

    def get_discovered_devices(self) -> list:
        """Get list of discovered devices

        Returns:
            list: Device information list
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
    """UDP Protocol Handler

    Handle received UDP packets
    """

    def __init__(self, server: DiscoveryServer):
        """Initialize protocol handler

        Args:
            server: Discovery server instance
        """
        self.server = server
        self.logger = get_logger(__name__)

    def connection_made(self, transport):
        """Callback when connection is established"""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple):
        """Receive UDP packet

        Args:
            data: Received data
            addr: Sender address (ip, port)
        """
        try:
            # Parse JSON message
            message = json.loads(data.decode('utf-8'))

            # Check if it's a discovery request
            if message.get('cmd') == 'DISCOVER':
                self._handle_discovery(message, addr)
            else:
                self.logger.debug(f"Unknown command: {message.get('cmd')}")

        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON data: {data[:100]}...")
        except Exception as e:
            self.logger.error(f"Failed to process packet: {e}", exc_info=True)

    def _handle_discovery(self, message: dict, addr: tuple):
        """Handle discovery request

        Args:
            message: Parsed message
            addr: Sender address (ip, port)
        """
        device_id = message.get('device_id', 'unknown')
        mac = message.get('mac', '')

        self.logger.info(f"Received discovery request: device_id={device_id}, mac={mac}, from={addr[0]}")

        # Register device
        self.server.register_device(device_id, mac, addr[0])

        # Send response (unicast to device IP to avoid broadcast storm)
        response = self.server.create_response()
        self.transport.sendto(response, addr)

        self.logger.debug(f"Sent service response to {addr[0]}:{addr[1]}")

    def error_received(self, exc):
        """Callback when error is received"""
        self.logger.error(f"UDP error: {exc}")
```

### 5.3 Integrate into WebSocket Server

```python
# src/core/websocket_server.py add the following

from src.modules.discovery import DiscoveryServer

class WebSocketServer:
    """WebSocket Server (with service discovery)"""

    def __init__(self):
        # ... existing code ...

        # Service discovery server
        self.discovery_server: Optional[DiscoveryServer] = None

    async def start(self):
        """Start server"""
        # ... existing startup code ...

        # Start discovery server
        discovery_enabled = getattr(settings, 'discovery_enabled', True)
        if discovery_enabled:
            self.discovery_server = DiscoveryServer()
            await self.discovery_server.start()

    async def cleanup(self):
        """Cleanup resources"""
        # Stop discovery server
        if self.discovery_server:
            await self.discovery_server.stop()

        # ... existing cleanup code ...
```

### 5.4 Update Configuration File

```python
# src/config/env.py add the following configuration

class Settings(BaseSettings):
    # ... existing config ...

    # ========== Service Discovery Config ==========
    discovery_enabled: bool = Field(
        default=True,
        description="Enable service discovery"
    )
    discovery_port: int = Field(
        default=37020,
        description="UDP discovery port"
    )
```

### 5.5 Environment Variable Configuration

```bash
# Add to .env file

# Service Discovery Configuration
DISCOVERY_ENABLED=true
DISCOVERY_PORT=37020
```

---

## 6. Testing Plan

### 6.1 ESP32 End Testing

1. Flash code to ESP32
2. Open serial monitor (115200 baud)
3. Observe log output:

```
========================================
   ESP32 Service Discovery Client
========================================

WiFi connected
  IP Address: 192.168.1.50
  MAC Address: AA:BB:CC:DD:EE:FF
UDP listener started, port: 37020
Service discovery started

Sent discovery broadcast: {"cmd":"DISCOVER","device_id":"esp32-EF:FF","mac":"AA:BB:CC:DD:EE:FF"}
Waiting for server response... (1)
Received UDP data: {"cmd":"ANNOUNCE","ip":"192.168.1.100","port":8765,"version":"1.0.0"}
   From: 192.168.1.100
Server discovered!
  IP: 192.168.1.100
  Port: 8765
Connecting to server...
  Address: 192.168.1.100:8765
Discovery complete, task ending
```

### 6.2 Server End Testing

1. Start Watcher Server
2. Observe Python logs:

```
INFO - Discovery server initialized: udp_port=37020, ws_port=8765
INFO - Discovery server started
INFO -   Listening address: 0.0.0.0:37020
INFO -   Local IP: 192.168.1.100
INFO -   WebSocket port: 8765

INFO - Received discovery request: device_id=esp32-EF:FF, mac=AA:BB:CC:DD:EE:FF, from=192.168.1.50
INFO - Device registered: esp32-EF:FF (192.168.1.50)
INFO - Sent service response to 192.168.1.50:xxxxx: {...}
```

### 6.3 Windows/macOS Client Testing

Without ESP32, you can simulate a client with your computer.

#### 6.3.1 Windows Testing

**Prerequisites**:
- Ensure Windows and server are on the same LAN
- Confirm server's LAN IP address (shown in server logs)

**Method 1: Use Python Script**

1. Start Watcher Server, confirm local IP in logs (e.g., `192.168.31.66`)

2. Run in Windows CMD:

```cmd
python -c "import socket,json; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1); s.sendto(json.dumps({'cmd':'DISCOVER'}).encode(),('192.168.31.255',37020)); print('Sent'); s.settimeout(3); print(s.recv(1024).decode())"
```

> Note: Replace `192.168.31.255` with your subnet broadcast address (change last digit of IP to 255)

**Method 2: PowerShell One-liner**

```powershell
$client = New-Object System.Net.Sockets.UdpClient; $client.EnableBroadcast = $true; $endpoint = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Broadcast, 37020); $bytes = [System.Text.Encoding]::ASCII.GetBytes('{"cmd":"DISCOVER"}'); $client.Send($bytes, $bytes.Length, $endpoint) | Out-Null; $client.Receive($endpoint); [System.Text.Encoding]::ASCII.GetString($client.Receive($endpoint)) | Write-Output
```

**Expected Output**:
```
Sent
{"cmd": "ANNOUNCE", "ip": "192.168.31.66", "port": 8765, "version": "1.0.0", "server": "watcher-server"}
```

#### 6.3.2 macOS Testing

**Method 1: Use Python**

```bash
python -c "
import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Send broadcast
broadcast_ip = '192.168.31.255'  # Replace with your subnet broadcast address
msg = json.dumps({'cmd': 'DISCOVER'})
s.sendto(msg.encode(), (broadcast_ip, 37020))
print('Broadcast sent')

# Wait for response
s.settimeout(3)
try:
    data, addr = s.recvfrom(1024)
    print(f'Response from {addr}:')
    print(data.decode())
except:
    print('Timeout')
s.close()
```

**Method 2: Use netcat to listen**

1. On macOS, listen on UDP port:
```bash
nc -lu 37020
```

2. Send broadcast from another computer, should see `{"cmd":"DISCOVER"}`

#### 6.3.3 Finding Correct Broadcast Address

If testing fails, it might be because the broadcast address is incorrect.

**Calculate Broadcast Address**:
- Assume server IP is `192.168.31.66`
- Subnet mask is usually `255.255.255.0`
- Broadcast address = `192.168.31.255`

**Quick Test**: Send directly to server IP (not broadcast)

```cmd
# Windows - send directly to server IP
python -c "import socket,json; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.sendto(json.dumps({'cmd':'DISCOVER'}).encode(),('192.168.31.66',37020)); s.settimeout(3); print(s.recv(1024).decode())"
```

```bash
# macOS/Linux - send directly to server IP
echo '{"cmd":"DISCOVER"}' | nc -u 192.168.31.66 37020
```

### 6.4 Network Packet Capture Verification

Use Wireshark to verify packet capture:

```
# Filter
udp.port == 37020

# Expected packets
1. ESP32 → 255.255.255.255: {"cmd":"DISCOVER",...}
2. Server → ESP32: {"cmd":"ANNOUNCE",...}
```

---

## 7. Optimization Suggestions

### 7.1 Reliability Optimization

| Optimization | Solution | Description |
|--------------|----------|-------------|
| Retry send | ESP32 sends 3-5 times after startup | 500ms interval, improve success rate |
| Timeout handling | Alert after 30s without discovery | Avoid infinite waiting |
| Reconnection mechanism | Re-discover after WebSocket disconnect | Improve connection stability |

### 7.2 Security Considerations

| Risk | Protection |
|------|-------------|
| Man-in-the-middle attack | Add device authentication (shared secret) |
| Unauthorized access | Device whitelist mechanism |
| Information leakage | Encrypt sensitive information |

### 7.3 Feature Extensions

1. **Multi-server support**: Respond with list of available servers for ESP32 to choose
2. **Load balancing**: Distribute connections based on server load
3. **Heartbeat keep-alive**: Regularly confirm device online status
4. **Remote configuration**: Update ESP32 config via UDP broadcast

---

## 8. Alternative: mDNS

If a more standardized solution is needed in the future, consider mDNS (Multicast DNS):

### ESP32 End
```cpp
#include <ESPmDNS.h>

void setup() {
  // Start mDNS
  if (!MDNS.begin("watcher-esp32")) {
    Serial.println("mDNS failed to start");
    return;
  }

  // Advertise WebSocket service
  MDNS.addService("websocket", "tcp", 8765);
}
```

### Python End
```python
from zeroconf import ServiceBrowser, Zeroconf

class Listener:
    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        ip = socket.inet_ntoa(info.addresses[0])
        print(f"Discovered device: {name} → {ip}:{info.port}")

zeroconf = Zeroconf()
browser = ServiceBrowser(zeroconf, "_websocket._tcp.local.", Listener())
```

---

## 9. Implementation Plan

| Phase | Task | Estimated Hours |
|-------|------|-----------------|
| **Phase 1** | Python server implementation | 2 hours |
| **Phase 2** | ESP32 code development | 3 hours |
| **Phase 3** | Integration testing | 2 hours |
| **Phase 4** | Documentation update | 1 hour |
| **Total** | - | **8 hours** |

---

## 10. Reference Resources

### Documentation and Tutorials
- [ESP32 AsyncUDP Library](https://github.com/me-no-dev/AsyncUDP)
- [ESP32 mDNS Tutorial - Random Nerd Tutorials](https://randomnerdtutorials.com/esp32-mdns/)
- [Python AsyncIO UDP](https://docs.python.org/3/library/asyncio-stream.html)

### Related Standards
- RFC 6762 - Multicast DNS
- RFC 6763 - DNS-Based Service Discovery

---

## Appendix: Troubleshooting

### Problem 1: ESP32 Cannot Receive Response

**Possible Causes**:
1. Firewall blocks UDP port
2. ESP32 and server not on same subnet
3. Router disables broadcast forwarding

**Debug Methods**:
```bash
# Check firewall
sudo ufw status

# Test UDP port
nc -lu 37020
```

### Problem 2: Server Cannot Get Correct LAN IP

**Solution**:
```python
# Method 1: Enumerate network interfaces
import netifaces
for interface in netifaces.interfaces():
    if interface != 'lo':
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            ip = addrs[netifaces.AF_INET][0]['addr']
            if not ip.startswith('127.'):
                return ip
```

### Problem 3: Multiple ESP32 Starting Simultaneously Causes Network Congestion

**Optimization**:
```cpp
// Random delay to avoid simultaneous broadcast
void setup() {
  delay(random(0, 5000));  // 0-5 second random delay
  // ... rest of code
}
```

---

**Document Version**: v1.0
**Last Updated**: 2026-03-04
