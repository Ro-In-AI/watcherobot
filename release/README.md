# WatcherRobot Body MCU Firmware

Pre-built firmware binaries for WatcherRobot Body MCU (ESP32).

## Hardware

- **Target Chip**: ESP32
- **Flash Size**: 4MB
- **Features**: BLE GATT Server, Servo Control (UART)

## Files

| File | Address | Size | Description |
|------|---------|------|-------------|
| `bootloader.bin` | 0x0000 | ~26 KB | ESP-IDF bootloader |
| `partition-table.bin` | 0x8000 | ~3 KB | Partition table |
| `WatcherRobotBody.bin` | 0x10000 | ~810 KB | Main application |

## Quick Flash

### Windows
```powershell
# 1. Activate ESP-IDF
. C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1

# 2. Flash (auto-detect COM port)
.\flash.bat

# Or specify port
.\flash.bat COM3
```

### macOS / Linux
```bash
# 1. Activate ESP-IDF
source $IDF_PATH/export.sh

# 2. Flash (auto-detect port)
./flash.sh

# Or specify port
./flash.sh /dev/ttyUSB0
```

## Manual Flash

If you don't have ESP-IDF, install `esptool` separately:

```bash
pip install esptool
```

Then flash:

```bash
esptool.py --chip esp32 -p PORT -b 921600 write_flash \
  --flash_mode dio --flash_size 4MB --flash_freq 40m \
  0x0000 bootloader.bin \
  0x8000 partition-table.bin \
  0x10000 WatcherRobotBody.bin
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `esptool.py not found` | Run ESP-IDF export script or `pip install esptool` |
| `Failed to connect` | Hold BOOT button, press RESET, release BOOT |
| `Wrong COM port` | Check Device Manager (Windows) or `ls /dev/tty*` (Linux/Mac) |
| Driver not installed | Install CH340 or CP2102 driver |

## Build from Source

```bash
# macOS/Linux
./build_release.sh

# Windows
.\build_release.bat
```

Requires ESP-IDF v5.2+ installed.
