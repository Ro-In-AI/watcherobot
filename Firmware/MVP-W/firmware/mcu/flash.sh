#!/bin/bash
#
# MVP-W MCU 固件烧录脚本 (Linux/macOS)
#
# 用法:
#   ./flash.sh [PORT] [BAUD]
#   ./flash.sh /dev/ttyUSB0 115200
#
# 选项:
#   --erase      擦除整个 Flash
#
# 依赖: esptool (pip install esptool)
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 默认参数
PORT=""
BAUD=115200
ERASE_FLASH=false

# 帮助信息
show_help() {
    echo -e "${CYAN}MVP-W MCU Firmware Flasher v1.5.0${NC}"
    echo -e "${CYAN}(ESP32 舵机控制 + BLE)${NC}"
    echo ""
    echo "用法: $0 [选项] [PORT] [BAUD]"
    echo ""
    echo "选项:"
    echo "  --erase      擦除整个 Flash（清除所有数据）"
    echo "  --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                           # 自动检测串口"
    echo "  $0 /dev/ttyUSB0              # 指定串口"
    echo "  $0 --erase /dev/ttyUSB0      # 擦除后烧录"
    echo ""
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --erase)
            ERASE_FLASH=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        /dev/*|COM*)
            PORT="$1"
            shift
            ;;
        [0-9]*)
            BAUD="$1"
            shift
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 输出函数
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 检查 esptool
check_esptool() {
    if ! python -m esptool version &> /dev/null; then
        error "未找到 esptool。请运行: pip install esptool"
    fi
    success "esptool 已安装"
}

# 自动检测串口
find_port() {
    # Linux
    if [[ -d /dev/serial/by-id ]]; then
        PORT=$(ls /dev/serial/by-id/*esp32* 2>/dev/null | head -1 || ls /dev/serial/by-id/*USB* 2>/dev/null | head -1)
    fi

    # macOS
    if [[ -z "$PORT" ]] && [[ "$OSTYPE" == "darwin"* ]]; then
        PORT=$(ls /dev/cu.usbserial* 2>/dev/null | head -1 || ls /dev/cu.usbmodem* 2>/dev/null | head -1)
    fi

    # Linux fallback
    if [[ -z "$PORT" ]]; then
        PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -1 || ls /dev/ttyACM* 2>/dev/null | head -1)
    fi

    if [[ -z "$PORT" ]]; then
        error "未检测到 ESP32 设备。请检查 USB 连接或手动指定串口。"
    fi

    success "自动检测到串口: $PORT"
}

# 查找固件文件
find_firmware() {
    if [[ -f "$SCRIPT_DIR/release/bootloader.bin" ]]; then
        BIN_DIR="$SCRIPT_DIR/release"
        BOOTLOADER="$BIN_DIR/bootloader.bin"
        PARTITION_TABLE="$BIN_DIR/partition-table.bin"
        APP_FIRMWARE="$BIN_DIR/MVP-W-MCU.bin"

        # 回退到旧名称
        if [[ ! -f "$APP_FIRMWARE" ]]; then
            APP_FIRMWARE="$BIN_DIR/WatcherRobotBody.bin"
        fi
    elif [[ -f "$SCRIPT_DIR/build/bootloader/bootloader.bin" ]]; then
        BIN_DIR="$SCRIPT_DIR/build"
        BOOTLOADER="$BIN_DIR/bootloader/bootloader.bin"
        PARTITION_TABLE="$BIN_DIR/partition_table/partition-table.bin"
        APP_FIRMWARE="$BIN_DIR/MVP-W-MCU.bin"

        # 回退到旧名称
        if [[ ! -f "$APP_FIRMWARE" ]]; then
            APP_FIRMWARE="$BIN_DIR/WatcherRobotBody.bin"
        fi
    else
        error "未找到固件文件！请先运行 ./build_release.sh"
    fi

    # 检查文件是否存在
    local missing=()
    [[ ! -f "$BOOTLOADER" ]] && missing+=("$BOOTLOADER")
    [[ ! -f "$PARTITION_TABLE" ]] && missing+=("$PARTITION_TABLE")
    [[ ! -f "$APP_FIRMWARE" ]] && missing+=("$APP_FIRMWARE")

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "缺少固件文件:\n  ${missing[*]}"
    fi

    success "固件文件检查通过"
}

# 主程序
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  MVP-W MCU Firmware Flasher v1.5.0${NC}"
echo -e "${CYAN}  (ESP32 舵机控制 + BLE)${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

check_esptool
find_firmware

# 确定串口
if [[ -z "$PORT" ]]; then
    find_port
fi

# 显示配置
echo ""
info "烧录配置:"
echo "  串口: $PORT"
echo "  波特率: $BAUD"
echo "  固件目录: $BIN_DIR"
if $ERASE_FLASH; then
    echo -e "  擦除Flash: ${YELLOW}是${NC}"
fi
echo ""

# 进入下载模式提示
warn "请确保设备处于下载模式:"
echo "  1. 按住 BOOT 键"
echo "  2. 按一下 RST 键"
echo "  3. 松开 BOOT 键"
echo ""
read -p "按 Enter 开始烧录..."

# 擦除 Flash
if $ERASE_FLASH; then
    info "擦除 Flash..."
    python -m esptool --port "$PORT" --baud "$BAUD" erase_flash
    success "Flash 擦除完成"
    echo ""
    warn "擦除后需要重新进入下载模式:"
    echo "  1. 按住 BOOT 键"
    echo "  2. 按一下 RST 键"
    echo "  3. 松开 BOOT 键"
    echo ""
    read -p "按 Enter 继续烧录..."
fi

# 烧录固件
info "开始烧录..."
echo ""
warn "预计需要 1-2 分钟，请耐心等待..."
echo ""
echo "  - Bootloader @ 0x0"
echo "  - 分区表 @ 0x8000"
echo "  - 应用固件 @ 0x10000"

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
echo "  2. 通过 BLE 或 UART 控制舵机"
echo ""
