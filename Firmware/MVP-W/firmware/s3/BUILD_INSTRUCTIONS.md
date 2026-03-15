# S3 Firmware Build Instructions

## Prerequisites
- ESP-IDF v5.2.1 installed at `C:\Espressif\frameworks\esp-idf-v5.2.1`
- ESP32-S3 target board connected

## Build Steps

Open a **fresh Windows CMD terminal** (not MinGW/Git Bash), then:

```cmd
cd /d D:\GithubRep\WatcherProject\MVP-W\firmware\s3
C:\Espressif\frameworks\esp-idf-v5.2.1\export.bat
idf.py set-target esp32s3
idf.py build
```

## Flash

```cmd
idf.py -p COM3 flash monitor
```

Replace `COM3` with your actual COM port.

## Configuration

Edit the following files before building:
- `main/wifi_client.c` - Set your WiFi SSID and password
- `main/ws_client.c` - Set your WebSocket server URL

## Project Structure

```
firmware/s3/
├── CMakeLists.txt          # Project config
├── sdkconfig.defaults      # ESP32-S3 defaults
├── main/
│   ├── app_main.c          # Entry point
│   ├── ws_router.c/h       # WebSocket message routing
│   ├── uart_bridge.c/h     # UART to MCU
│   ├── button_voice.c/h    # Voice recorder state machine
│   ├── display_ui.c/h      # Display state mapping
│   ├── hal_*.c/h           # Hardware abstraction layer
│   ├── wifi_client.c/h     # WiFi connection
│   └── ws_client.c/h       # WebSocket client
└── test_host/              # Host-side TDD tests
```
