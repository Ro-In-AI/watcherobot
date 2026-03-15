#!/bin/bash
# ============================================================
# Build Release Binary for WatcherRobot Body MCU
# This creates a single flashable .bin file
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
    echo "  Or install ESP-IDF and add to PATH"
    exit 1
fi

# Set project root
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Clean previous build
if [ -f "build/watcherobot_merged.bin" ]; then
    echo "[1/4] Cleaning previous release..."
    rm -f build/watcherobot_merged.bin
fi

# Build the project
echo "[2/4] Building project..."
idf.py build

# Create merged binary for easy flashing
echo "[3/4] Creating merged binary..."
esptool.py --chip esp32 merge_bin \
    -o build/watcherobot_merged.bin \
    --flash_mode dio \
    --flash_size 4MB \
    --flash_freq 40m \
    0x0000 build/bootloader/bootloader.bin \
    0x8000 build/partition_table/partition-table.bin \
    0x10000 build/WatcherRobotBody.bin

# Copy to release folder
echo "[4/4] Copying to release folder..."
mkdir -p "$PROJECT_ROOT/release"
cp -f "$PROJECT_ROOT/build/watcherobot_merged.bin" "$PROJECT_ROOT/release/watcherobot_merged.bin"

echo ""
echo "========================================"
echo " Build Complete!"
echo "========================================"
echo ""
echo "Output files:"
echo "  build/watcherobot_merged.bin"
echo "  release/watcherobot_merged.bin  (for distribution)"
echo ""
echo "Flash with: ./flash.sh /dev/ttyUSB0"
echo "Example: ./flash.sh /dev/ttyUSB0"
echo ""
