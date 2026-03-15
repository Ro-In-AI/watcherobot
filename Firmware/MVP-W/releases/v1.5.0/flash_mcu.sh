#!/bin/bash
#
# MVP-W MCU 固件烧录脚本 (Linux/macOS)
#
# 用法: ./flash_mcu.sh [PORT]
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIRMWARE_DIR="$SCRIPT_DIR/firmware/mcu"

PORT="${1:-}"
BAUD=115200

info() { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  MVP-W MCU Flasher v1.5.0${NC}"
echo -e "${CYAN}  (ESP32 舵机控制 + BLE)${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查 esptool
if ! python -m esptool version &> /dev/null; then
    error "未找到 esptool。请运行: pip install esptool"
fi
success "esptool 已安装"

# 检查固件文件
BOOTLOADER="$FIRMWARE_DIR/bootloader.bin"
PARTITION_TABLE="$FIRMWARE_DIR/partition-table.bin"
APP_FIRMWARE="$FIRMWARE_DIR/MVP-W-MCU.bin"

missing=()
[[ ! -f "$BOOTLOADER" ]] && missing+=("$BOOTLOADER")
[[ ! -f "$PARTITION_TABLE" ]] && missing+=("$PARTITION_TABLE")
[[ ! -f "$APP_FIRMWARE" ]] && missing+=("$APP_FIRMWARE")

if [[ ${#missing[@]} -gt 0 ]]; then
    error "缺少固件文件:\n  ${missing[*]}"
fi

# 自动检测串口
if [[ -z "$PORT" ]]; then
    if [[ -d /dev/serial/by-id ]]; then
        PORT=$(ls /dev/serial/by-id/*USB* 2>/dev/null | head -1)
    fi
    if [[ -z "$PORT" ]] && [[ "$OSTYPE" == "darwin"* ]]; then
        PORT=$(ls /dev/cu.usbserial* 2>/dev/null | head -1 || ls /dev/cu.usbmodem* 2>/dev/null | head -1)
    fi
    if [[ -z "$PORT" ]]; then
        PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -1 || ls /dev/ttyACM* 2>/dev/null | head -1)
    fi
    if [[ -z "$PORT" ]]; then
        error "未检测到 ESP32 设备"
    fi
    success "自动检测到串口: $PORT"
fi

echo ""
info "烧录配置:"
echo "  串口: $PORT"
echo "  波特率: $BAUD"
echo ""

warn "请确保设备处于下载模式:"
echo "  1. 按住 BOOT 键"
echo "  2. 按一下 RST 键"
echo "  3. 松开 BOOT 键"
echo ""
read -p "按 Enter 开始烧录..."

info "开始烧录..."
echo ""
warn "预计需要 1 分钟，请耐心等待..."
echo ""

python -m esptool --chip esp32 --port "$PORT" --baud "$BAUD" \
    --before default_reset --after hard_reset write_flash \
    --flash_mode dio --flash_size 4MB --flash_freq 40m \
    0x0 "$BOOTLOADER" \
    0x8000 "$PARTITION_TABLE" \
    0x10000 "$APP_FIRMWARE"

echo ""
success "========================================"
success "  烧录完成！"
success "========================================"
echo ""
info "后续步骤:"
echo "  1. 按 RST 键重启设备"
echo "  2. 手机蓝牙扫描 'ESP_ROBOT' 连接"
echo "  3. 或通过 UART 与 S3 主控通信"
echo ""
