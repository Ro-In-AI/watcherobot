# Release Binaries

This folder contains pre-built firmware binaries for WatcherRobot Body MCU.

## Files

| File | Address | Description |
|------|---------|-------------|
| `bootloader.bin` | 0x0000 | ESP-IDF bootloader |
| `partition-table.bin` | 0x8000 | Partition table |
| `WatcherRobotBody.bin` | 0x10000 | Main application |

## Flashing

### Windows
```powershell
# Activate ESP-IDF first
. C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1

# Flash
.\flash.bat COM3
```

### macOS / Linux
```bash
# Activate ESP-IDF first
source $IDF_PATH/export.sh

# Flash
./flash.sh /dev/ttyUSB0
```

## Manual Flashing

```bash
esptool.py --chip esp32 -p PORT -b 921600 write_flash \
  0x0000 release/bootloader.bin \
  0x8000 release/partition-table.bin \
  0x10000 release/WatcherRobotBody.bin
```

## Build from Source

```bash
./build_release.sh   # macOS/Linux
build_release.bat    # Windows
```
