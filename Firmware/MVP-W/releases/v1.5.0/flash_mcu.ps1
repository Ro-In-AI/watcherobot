#Requires -Version 5.1
<#
.SYNOPSIS
    MVP-W MCU 固件烧录脚本 (Windows)

.DESCRIPTION
    烧录 MCU 舵机控制固件到 ESP32 设备。

.PARAMETER Port
    串口号，例如 COM4。如果不指定，将自动检测。

.PARAMETER Baud
    烧录波特率，默认 115200。

.EXAMPLE
    .\flash_mcu.ps1 -Port COM4
#>

param(
    [string]$Port,
    [int]$Baud = 115200
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FirmwareDir = Join-Path $ScriptDir "firmware\mcu"

$Bootloader = Join-Path $FirmwareDir "bootloader.bin"
$PartitionTable = Join-Path $FirmwareDir "partition-table.bin"
$AppFirmware = Join-Path $FirmwareDir "MVP-W-MCU.bin"

function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MVP-W MCU Flasher v1.5.0" -ForegroundColor Cyan
Write-Host "  (ESP32 舵机控制 + BLE)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 esptool
try {
    $null = python -m esptool version 2>&1
    Write-Success "esptool 已安装"
} catch {
    Write-Error "未找到 esptool。请运行: pip install esptool"
    exit 1
}

# 检查固件文件
$missing = @()
if (-not (Test-Path $Bootloader)) { $missing += $Bootloader }
if (-not (Test-Path $PartitionTable)) { $missing += $PartitionTable }
if (-not (Test-Path $AppFirmware)) { $missing += $AppFirmware }

if ($missing.Count -gt 0) {
    Write-Error "缺少固件文件:"
    $missing | ForEach-Object { Write-Host "  $_" }
    exit 1
}

# 自动检测串口
if (-not $Port) {
    $ports = Get-WmiObject Win32_SerialPort | Where-Object {
        $_.Description -match "USB Serial|CH340|CP210|FTDI|ESP32"
    }

    if ($ports.Count -eq 1) {
        $Port = $ports[0].DeviceID
        Write-Success "自动检测到串口: $Port"
    } elseif ($ports.Count -gt 1) {
        Write-Info "检测到多个串口:"
        $ports | ForEach-Object { Write-Host "  $($_.DeviceID) - $($_.Description)" }
        Write-Warning "请使用 -Port 参数指定串口"
        exit 1
    } else {
        Write-Error "未检测到 ESP32 设备"
        exit 1
    }
}

Write-Host ""
Write-Info "烧录配置:"
Write-Host "  串口: $Port"
Write-Host "  波特率: $Baud"
Write-Host ""

Write-Warning "请确保设备处于下载模式:"
Write-Host "  1. 按住 BOOT 键"
Write-Host "  2. 按一下 RST 键"
Write-Host "  3. 松开 BOOT 键"
Write-Host ""
Read-Host "按 Enter 开始烧录..."

Write-Info "开始烧录..."
Write-Host ""
Write-Warning "预计需要 1 分钟，请耐心等待..."
Write-Host ""

python -m esptool --chip esp32 --port $Port --baud $Baud `
    --before default_reset --after hard_reset write_flash `
    --flash_mode dio --flash_size 4MB --flash_freq 40m `
    0x0 $Bootloader `
    0x8000 $PartitionTable `
    0x10000 $AppFirmware

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
Write-Host "  2. 手机蓝牙扫描 'ESP_ROBOT' 连接"
Write-Host "  3. 或通过 UART 与 S3 主控通信"
Write-Host ""
