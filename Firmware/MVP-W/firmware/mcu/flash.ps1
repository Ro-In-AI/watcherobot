#Requires -Version 5.1
<#
.SYNOPSIS
    MVP-W MCU 固件烧录脚本 (Windows)

.DESCRIPTION
    自动烧录 MVP-W ESP32 MCU 舵机控制固件到设备。

.PARAMETER Port
    串口号，例如 COM3, COM4。如果不指定，将自动检测。

.PARAMETER Baud
    烧录波特率，默认 115200。可提高至 460800 加速。

.PARAMETER EraseFlash
    擦除整个 Flash 后再烧录。会清除所有用户数据。

.EXAMPLE
    .\flash.ps1 -Port COM4
    自动烧录

.EXAMPLE
    .\flash.ps1 -Port COM4 -Baud 460800
    使用更高波特率加速

.NOTES
    需要安装 esptool: pip install esptool
#>

param(
    [string]$Port,
    [int]$Baud = 115200,
    [switch]$EraseFlash
)

$ErrorActionPreference = "Stop"

# 固件目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 查找固件文件（优先 release/，其次 build/）
$BinDir = $null
$Bootloader = $null
$PartitionTable = $null
$AppFirmware = $null

if (Test-Path "$ScriptDir\release\bootloader.bin") {
    $BinDir = "$ScriptDir\release"
    $Bootloader = "$BinDir\bootloader.bin"
    $PartitionTable = "$BinDir\partition-table.bin"
    $AppFirmware = "$BinDir\MVP-W-MCU.bin"
} elseif (Test-Path "$ScriptDir\build\bootloader\bootloader.bin") {
    $BinDir = "$ScriptDir\build"
    $Bootloader = "$BinDir\bootloader\bootloader.bin"
    $PartitionTable = "$BinDir\partition_table\partition-table.bin"
    $AppFirmware = "$BinDir\MVP-W-MCU.bin"
}

# 如果没有找到 MVP-W-MCU.bin，尝试 WatcherRobotBody.bin
if ($null -eq $AppFirmware -or -not (Test-Path $AppFirmware)) {
    if (Test-Path "$ScriptDir\release\WatcherRobotBody.bin") {
        $AppFirmware = "$ScriptDir\release\WatcherRobotBody.bin"
    } elseif (Test-Path "$ScriptDir\build\WatcherRobotBody.bin") {
        $AppFirmware = "$ScriptDir\build\WatcherRobotBody.bin"
    }
}

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
    if ($null -eq $BinDir) {
        Write-Error "未找到固件文件！"
        Write-Host "请先运行 build_release.ps1 编译固件"
        return $false
    }

    $missing = @()
    if (-not (Test-Path $Bootloader)) { $missing += $Bootloader }
    if (-not (Test-Path $PartitionTable)) { $missing += $PartitionTable }
    if (-not (Test-Path $AppFirmware)) { $missing += $AppFirmware }

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
Write-Host "  MVP-W MCU Firmware Flasher v1.5.0" -ForegroundColor Cyan
Write-Host "  (ESP32 舵机控制 + BLE)" -ForegroundColor Cyan
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
Write-Host "  固件目录: $BinDir"
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

# 烧录固件
Write-Info "开始烧录..."
Write-Host ""
Write-Warning "预计需要 1-2 分钟，请耐心等待..."
Write-Host ""
Write-Host "  - Bootloader @ 0x0"
Write-Host "  - 分区表 @ 0x8000"
Write-Host "  - 应用固件 @ 0x10000"

python -m esptool --chip esp32 --port $Port --baud $Baud `
    --before default_reset --after hard_reset write_flash `
    --flash_mode dio --flash_size 4MB --flash_freq 40m `
    0x0 $Bootloader `
    0x8000 $PartitionTable `
    0x10000 $AppFirmware

if ($LASTEXITCODE -ne 0) {
    Write-Error "烧录失败"
    Write-Host ""
    Write-Host "常见问题:"
    Write-Host "  - 串口号错误"
    Write-Host "  - 设备未进入下载模式"
    Write-Host "  - 驱动未安装 (CH340/CP2102)"
    exit 1
}

Write-Host ""
Write-Success "========================================"
Write-Success "  烧录完成！"
Write-Success "========================================"
Write-Host ""
Write-Info "后续步骤:"
Write-Host "  1. 按 RST 键重启设备"
Write-Host "  2. 通过 BLE 或 UART 控制舵机"
Write-Host ""
