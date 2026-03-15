#!/bin/bash
#
# MVP-W S3 固件烧录脚本 (Linux/macOS)
#
# 用法:
#   ./flash.sh [PORT] [BAUD]
#   ./flash.sh /dev/ttyUSB0 921600
#
# 选项:
#   --full       完整烧录（首次烧录/恢复出厂）
#   --app-only   仅烧录应用固件
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
NC='\033[0m' # No Color

# 固件目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIRMWARE_DIR="$SCRIPT_DIR/firmware"

# 固件文件
BOOTLOADER="$FIRMWARE_DIR/bootloader.bin"
PARTITION_TABLE="$FIRMWARE_DIR/partition-table.bin"
APP_FIRMWARE="$FIRMWARE_DIR/MVP-W-S3.bin"
SRMODELS="$FIRMWARE_DIR/srmodels.bin"
STORAGE="$FIRMWARE_DIR/storage.bin"

# 默认参数
PORT=""
BAUD=115200
FULL=false
APP_ONLY=false
ERASE_FLASH=false

# 帮助信息
show_help() {
    echo -e "${CYAN}MVP-W S3 Firmware Flasher v1.5.0${NC}"
    echo ""
    echo "用法: $0 [选项] [PORT] [BAUD]"
    echo ""
    echo "选项:"
    echo "  --full       完整烧录（首次烧录/恢复出厂）"
    echo "  --app-only   仅烧录应用固件（OTA 升级）"
    echo "  --erase      擦除整个 Flash（清除所有数据）"
    echo "  --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                           # 自动检测串口，完整烧录"
    echo "  $0 /dev/ttyUSB0              # 指定串口"
    echo "  $0 --app-only /dev/ttyUSB0   # 仅更新应用 (波特率默认 115200)"
    echo ""
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL=true
            shift
            ;;
        --app-only)
            APP_ONLY=true
            shift
            ;;
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
    if ! command -v esptool.py &> /dev/null; then
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

# 检查固件文件
check_firmware() {
    local missing=()

    if $APP_ONLY; then
        [[ ! -f "$APP_FIRMWARE" ]] && missing+=("$APP_FIRMWARE")
    else
        for file in "$BOOTLOADER" "$PARTITION_TABLE" "$APP_FIRMWARE" "$SRMODELS" "$STORAGE"; do
            [[ ! -f "$file" ]] && missing+=("$file")
        done
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "缺少固件文件:\n  ${missing[*]}"
    fi
    success "固件文件检查通过"
}

# 主程序
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  MVP-W S3 Firmware Flasher v1.5.0${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

check_esptool
check_firmware

# 确定串口
if [[ -z "$PORT" ]]; then
    find_port
fi

# 显示配置
echo ""
info "烧录配置:"
echo "  串口: $PORT"
echo "  波特率: $BAUD"
echo "  模式: $(if $APP_ONLY; then echo '仅应用'; else echo '完整烧录'; fi)"
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
    esptool.py --port "$PORT" --baud "$BAUD" erase_flash
    success "Flash 擦除完成"
    echo ""
    warn "擦除后需要重新进入下载模式:"
    echo "  1. 按住 BOOT 键"
    echo "  2. 按一下 RST 键"
    echo "  3. 松开 BOOT 键"
    echo ""
    read -p "按 Enter 继续烧录..."
fi

# 烧录固件 - 使用单次命令烧录所有文件
info "开始烧录..."
echo ""
warn "预计需要 2-3 分钟，请耐心等待..."
echo ""

if $APP_ONLY; then
    # 仅烧录应用固件
    info "烧录应用固件 (0x10000)..."
    esptool.py --chip esp32s3 --port "$PORT" --baud "$BAUD" \
        --before default_reset --after hard_reset write_flash \
        0x10000 "$APP_FIRMWARE"
else
    # 完整烧录 - 单次命令烧录所有文件
    info "烧录完整固件..."
    echo "  - Bootloader @ 0x0"
    echo "  - 分区表 @ 0x8000"
    echo "  - 应用固件 @ 0x10000"
    echo "  - 唤醒词模型 @ 0x410000"
    echo "  - 动画资源 @ 0x460000"

    esptool.py --chip esp32s3 --port "$PORT" --baud "$BAUD" \
        --before default_reset --after hard_reset write_flash \
        0x0 "$BOOTLOADER" \
        0x8000 "$PARTITION_TABLE" \
        0x10000 "$APP_FIRMWARE" \
        0x410000 "$SRMODELS" \
        0x460000 "$STORAGE"
fi

echo ""
success "========================================"
success "  烧录完成！"
success "========================================"
echo ""
info "后续步骤:"
echo "  1. 按 RST 键重启设备"
echo "  2. 配置 WiFi（首次使用需要）"
echo "  3. 启动云端服务器"
echo ""
