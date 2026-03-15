#!/bin/bash
# ============================================================
# Flash Script for WatcherRobot Body MCU
# Usage: ./flash.sh [PORT]
# Example: ./flash.sh /dev/ttyUSB0
# ============================================================

set -e

PORT="${1:-}"
BAUD="921600"

echo ""
echo "========================================"
echo " WatcherRobot Body - Flash Tool"
echo "========================================"
echo ""

# Check if esptool is available
if ! command -v esptool.py &> /dev/null; then
    echo "[ERROR] esptool.py not found!"
    echo "Please source ESP-IDF export script first:"
    echo "  Linux/macOS: source \$IDF_PATH/export.sh"
    exit 1
fi

# Auto-detect port if not specified
if [ -z "$PORT" ]; then
    echo "[INFO] No port specified, auto-detecting..."

    # Linux: try common USB serial ports
    for candidate in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1; do
        if [ -e "$candidate" ]; then
            PORT="$candidate"
            echo "[INFO] Found port: $PORT"
            break
        fi
    done

    # macOS: try USB serial ports
    if [ -z "$PORT" ]; then
        for candidate in /dev/cu.usbserial* /dev/cu.SLAB_USBtoUART* /dev/cu.usbmodem*; do
            if [ -e "$candidate" ]; then
                PORT="$candidate"
                echo "[INFO] Found port: $PORT"
                break
            fi
        done
    fi

    if [ -z "$PORT" ]; then
        echo "[ERROR] No serial port found!"
        echo "Usage: $0 [PORT]"
        echo "Example: $0 /dev/ttyUSB0"
        exit 1
    fi
fi

# Set project root
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Check if binaries exist (prefer release folder)
if [ -f "$PROJECT_ROOT/release/bootloader.bin" ]; then
    BIN_DIR="$PROJECT_ROOT/release"
elif [ -f "$PROJECT_ROOT/build/bootloader/bootloader.bin" ]; then
    BIN_DIR="$PROJECT_ROOT/build"
else
    echo "[ERROR] Binary files not found!"
    echo "Please run ./build_release.sh first."
    exit 1
fi

echo ""
echo "[INFO] Port: $PORT"
echo "[INFO] Baud: $BAUD"
echo "[INFO] Binary dir: $BIN_DIR"
echo ""
echo "[1/2] Entering bootloader mode..."
echo "      Please ensure the device is connected and in download mode."
echo ""

# Flash all binaries
echo "[2/2] Flashing..."
if [ "$BIN_DIR" = "$PROJECT_ROOT/release" ]; then
    esptool.py --chip esp32 -p "$PORT" -b "$BAUD" write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m \
        0x0000 "$BIN_DIR/bootloader.bin" \
        0x8000 "$BIN_DIR/partition-table.bin" \
        0x10000 "$BIN_DIR/WatcherRobotBody.bin"
else
    esptool.py --chip esp32 -p "$PORT" -b "$BAUD" write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m \
        0x0000 "$BIN_DIR/bootloader/bootloader.bin" \
        0x8000 "$BIN_DIR/partition_table/partition-table.bin" \
        0x10000 "$BIN_DIR/WatcherRobotBody.bin"
fi

echo ""
echo "========================================"
echo " Flash Complete!"
echo "========================================"
echo ""
echo "Starting serial monitor (Ctrl+] to exit)..."
echo ""

idf.py -p "$PORT" monitor
