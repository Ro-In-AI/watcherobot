#Requires -Version 5.1
<#
.SYNOPSIS
    MVP-W S3 固件烧录脚本 (Windows)

.DESCRIPTION
    自动烧录 MVP-W ESP32-S3 固件到设备。
    支持完整烧录（首次烧录/恢复出厂）和仅应用更新。

.PARAMETER Port
    串口号，例如 COM3, COM4。如果不指定，将自动检测。

.PARAMETER Baud
    烧录波特率，默认 115200。可提高至 460800 或 921600 加速。

.PARAMETER Full
    完整烧录模式。包含 bootloader、partition-table、srmodels、storage。
    首次烧录或恢复出厂时使用。

.PARAMETER AppOnly
    仅烧录应用固件。用于 OTA 升级场景。

.PARAMETER EraseFlash
    擦除整个 Flash 后再烧录。会清除所有用户数据。

.EXAMPLE
    .\flash.ps1 -Port COM3
    自动烧录（完整模式）

.EXAMPLE
    .\flash.ps1 -Port COM3 -AppOnly
    仅更新应用固件

.EXAMPLE
    .\flash.ps1 -Port COM3 -Baud 460800 -Full
    使用较低波特率完整烧录

.NOTES
    需要安装 esptool: pip install esptool
#>

param(
    [string]$Port,
    [int]$Baud = 115200,
    [switch]$Full,
    [switch]$AppOnly,
    [switch]$EraseFlash
)

$ErrorActionPreference = "Stop"

# 固件目录
$FirmwareDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FirmwarePath = Join-Path $FirmwareDir "firmware"

# 固件文件
$Bootloader = Join-Path $FirmwarePath "bootloader.bin"
$PartitionTable = Join-Path $FirmwarePath "partition-table.bin"
$AppFirmware = Join-Path $FirmwarePath "MVP-W-S3.bin"
$Srmodels = Join-Path $FirmwarePath "srmodels.bin"
$Storage = Join-Path $FirmwarePath "storage.bin"

# 颜色输出函数
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

# 检查 esptool
function Test-Esptool {
    try {
        $null = python -m esptool version 2>&1
        Write-Success "esptool 已安装"
        return $true
    } catch {
        Write-Error "未找到 esptool。请运行: pip install esptool"
        return $false
    }
}

# 自动检测串口
function Find-SerialPort {
    $ports = Get-WmiObject Win32_SerialPort | Where-Object {
        $_.Description -match "USB Serial|CH340|CP210|FTDI|ESP32"
    }

    if ($ports.Count -eq 1) {
        return $ports[0].DeviceID
    } elseif ($ports.Count -gt 1) {
        Write-Info "检测到多个串口:"
        $ports | ForEach-Object { Write-Host "  $($_.DeviceID) - $($_.Description)" }
        Write-Warning "请使用 -Port 参数指定串口"
        return $null
    } else {
        Write-Error "未检测到 ESP32 设备。请检查 USB 连接。"
        return $null
    }
}

# 检查固件文件
function Test-FirmwareFiles {
    $missing = @()

    if ($Full -or (-not $AppOnly)) {
        @($Bootloader, $PartitionTable, $AppFirmware, $Srmodels, $Storage) | ForEach-Object {
            if (-not (Test-Path $_)) {
                $missing += $_
            }
        }
    } else {
        if (-not (Test-Path $AppFirmware)) {
            $missing += $AppFirmware
        }
    }

    if ($missing.Count -gt 0) {
        Write-Error "缺少固件文件:"
        $missing | ForEach-Object { Write-Host "  $_" }
        return $false
    }
    return $true
}

# 主程序
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MVP-W S3 Firmware Flasher v1.5.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查依赖
if (-not (Test-Esptool)) { exit 1 }
if (-not (Test-FirmwareFiles)) { exit 1 }

# 确定串口
if (-not $Port) {
    $Port = Find-SerialPort
    if (-not $Port) { exit 1 }
    Write-Success "自动检测到串口: $Port"
}

# 显示配置
Write-Host ""
Write-Info "烧录配置:"
Write-Host "  串口: $Port"
Write-Host "  波特率: $Baud"
Write-Host "  模式: $(if ($AppOnly) { '仅应用' } else { '完整烧录' })"
if ($EraseFlash) { Write-Host "  擦除Flash: 是" -ForegroundColor Yellow }
Write-Host ""

# 进入下载模式提示
Write-Warning "请确保设备处于下载模式:"
Write-Host "  1. 按住 BOOT 键"
Write-Host "  2. 按一下 RST 键"
Write-Host "  3. 松开 BOOT 键"
Write-Host ""
Read-Host "按 Enter 开始烧录..."

# 擦除 Flash
if ($EraseFlash) {
    Write-Info "擦除 Flash..."
    python -m esptool --port $Port --baud $Baud erase_flash
    if ($LASTEXITCODE -ne 0) {
        Write-Error "擦除 Flash 失败"
        exit 1
    }
    Write-Success "Flash 擦除完成"
    Write-Host ""
    Write-Warning "擦除后需要重新进入下载模式:"
    Write-Host "  1. 按住 BOOT 键"
    Write-Host "  2. 按一下 RST 键"
    Write-Host "  3. 松开 BOOT 键"
    Write-Host ""
    Read-Host "按 Enter 继续烧录..."
}

# 烧录固件 - 使用单次命令烧录所有文件
Write-Info "开始烧录..."
Write-Host ""
Write-Warning "预计需要 2-3 分钟，请耐心等待..."
Write-Host ""

if ($AppOnly) {
    # 仅烧录应用固件
    Write-Info "烧录应用固件 (0x10000)..."
    python -m esptool --chip esp32s3 --port $Port --baud $Baud `
        --before default_reset --after hard_reset write_flash `
        0x10000 $AppFirmware
} else {
    # 完整烧录 - 单次命令烧录所有文件
    Write-Info "烧录完整固件..."
    Write-Host "  - Bootloader @ 0x0"
    Write-Host "  - 分区表 @ 0x8000"
    Write-Host "  - 应用固件 @ 0x10000"
    Write-Host "  - 唤醒词模型 @ 0x410000"
    Write-Host "  - 动画资源 @ 0x460000"

    python -m esptool --chip esp32s3 --port $Port --baud $Baud `
        --before default_reset --after hard_reset write_flash `
        0x0 $Bootloader `
        0x8000 $PartitionTable `
        0x10000 $AppFirmware `
        0x410000 $Srmodels `
        0x460000 $Storage
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "烧录失败"
    exit 1
}

Write-Host ""
Write-Success "========================================"
Write-Success "  烧录完成！"
Write-Success "========================================"
Write-Host ""
Write-Info "后续步骤:"
Write-Host "  1. 按 RST 键重启设备"
Write-Host "  2. 配置 WiFi（首次使用需要）"
Write-Host "  3. 启动云端服务器"
Write-Host ""
