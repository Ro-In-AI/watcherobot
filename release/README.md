# Release Binaries

This folder contains pre-built firmware binaries for WatcherRobot Body MCU.

## Files

| File | Description |
|------|-------------|
| `watcherobot_merged.bin` | Combined binary (bootloader + partition table + app) |

## Flashing

### Windows
```powershell
flash.bat COM3
```

### macOS / Linux
```bash
./flash.sh /dev/ttyUSB0
```

## Manual Flashing

If you prefer to flash manually with `esptool.py`:

```bash
esptool.py --chip esp32 -p PORT -b 921600 write_flash 0x0 release/watcherobot_merged.bin
```

## Build Your Own

To build from source:
```bash
./build_release.sh   # macOS/Linux
build_release.bat    # Windows
```
