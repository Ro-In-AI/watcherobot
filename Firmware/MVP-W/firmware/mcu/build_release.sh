#!/bin/bash
#
# MVP-W MCU 固件构建脚本 (Linux/macOS)
#
# 必须在 ESP-IDF 环境中运行:
#   source $HOME/esp/esp-idf/export.sh
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
BUILD_DIR="$SCRIPT_DIR/build"
RELEASE_DIR="$SCRIPT_DIR/release"

# 输出函数
info() { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  MVP-W MCU Firmware Builder v1.5.0${NC}"
echo -e "${CYAN}  (ESP32 舵机控制 + BLE)${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查 ESP-IDF 环境
if ! command -v idf.py &> /dev/null; then
    error "未检测到 ESP-IDF 环境。请运行: source \$HOME/esp/esp-idf/export.sh"
fi

# 切换到项目目录
cd "$SCRIPT_DIR"

# 构建
info "开始编译..."
idf.py build

success "编译完成"

# 创建 release 目录
mkdir -p "$RELEASE_DIR"

# 复制固件到 release 目录
info "复制固件到 release 目录..."

files=(
    "build/bootloader/bootloader.bin:release/bootloader.bin"
    "build/partition_table/partition-table.bin:release/partition-table.bin"
    "build/WatcherRobotBody.bin:release/MVP-W-MCU.bin"
)

for file in "${files[@]}"; do
    src="${file%%:*}"
    dst="${file##*:}"

    if [[ -f "$src" ]]; then
        cp -f "$src" "$dst"
        size=$(echo "scale=1; $(stat -c%s "$dst" 2>/dev/null || stat -f%z "$dst") / 1024" | bc)
        echo -e "  ${GREEN}✓${NC} $(basename "$dst") ($size KB)"
    else
        warn "  ✗ $(basename "$src") 不存在"
    fi
done

echo ""
success "========================================"
success "  构建完成！"
success "========================================"
echo ""
info "固件位置: $RELEASE_DIR"
echo ""
info "烧录命令:"
echo -e "  ${YELLOW}./flash.sh /dev/ttyUSB0${NC}"
echo ""
