#!/bin/bash
#
# 生成 MVP-W S3 合并固件
#
# 用法: ./merge_firmware.sh
#
# 依赖: esptool (pip install esptool)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIRMWARE_DIR="$SCRIPT_DIR/firmware"
OUTPUT_FILE="$SCRIPT_DIR/MVP-W-S3-combined.bin"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# 检查 esptool
if ! command -v esptool.py &> /dev/null; then
    echo -e "${RED}[ERROR] 未找到 esptool。请运行: pip install esptool${NC}"
    exit 1
fi

# 检查固件文件
files=("bootloader.bin" "partition-table.bin" "MVP-W-S3.bin" "srmodels.bin" "storage.bin")
for file in "${files[@]}"; do
    if [[ ! -f "$FIRMWARE_DIR/$file" ]]; then
        echo -e "${RED}[ERROR] 缺少固件文件: $FIRMWARE_DIR/$file${NC}"
        exit 1
    fi
done

echo -e "${CYAN}[INFO] 生成合并固件...${NC}"

esptool.py --chip esp32s3 merge_bin \
    -o "$OUTPUT_FILE" \
    --flash_mode dio \
    --flash_size 16MB \
    --flash_freq 80m \
    0x0 "$FIRMWARE_DIR/bootloader.bin" \
    0x8000 "$FIRMWARE_DIR/partition-table.bin" \
    0x10000 "$FIRMWARE_DIR/MVP-W-S3.bin" \
    0x410000 "$FIRMWARE_DIR/srmodels.bin" \
    0x460000 "$FIRMWARE_DIR/storage.bin"

size=$(echo "scale=2; $(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE") / 1048576" | bc)
echo -e "${GREEN}[OK] 合并固件已生成: $OUTPUT_FILE (${size} MB)${NC}"
