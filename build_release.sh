#!/bin/bash
# ============================================================
# Build Release Binaries for WatcherRobot Body MCU
# ============================================================

set -e

echo ""
echo "========================================"
echo " WatcherRobot Body - Build Release"
echo "========================================"
echo ""

# Check if idf.py is available
if ! command -v idf.py &> /dev/null; then
    echo "[ERROR] idf.py not found!"
    echo "Please source ESP-IDF export script first:"
    echo "  Linux/macOS: source \$IDF_PATH/export.sh"
    exit 1
fi

# Set project root
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Build the project
echo "[1/2] Building project..."
idf.py build

# Copy binaries to release folder
echo "[2/2] Copying binaries to release folder..."
mkdir -p "$PROJECT_ROOT/release"

cp -f "$PROJECT_ROOT/build/bootloader/bootloader.bin" "$PROJECT_ROOT/release/bootloader.bin"
cp -f "$PROJECT_ROOT/build/partition_table/partition-table.bin" "$PROJECT_ROOT/release/partition-table.bin"
cp -f "$PROJECT_ROOT/build/WatcherRobotBody.bin" "$PROJECT_ROOT/release/WatcherRobotBody.bin"

echo ""
echo "========================================"
echo " Build Complete!"
echo "========================================"
echo ""
echo "Output files in release/:"
echo "  bootloader.bin       (0x0000)"
echo "  partition-table.bin  (0x8000)"
echo "  WatcherRobotBody.bin (0x10000)"
echo ""
echo "Flash with: ./flash.sh /dev/ttyUSB0"
echo "Example: ./flash.sh /dev/ttyUSB0"
echo ""
