#Requires -Version 5.1
<#
.SYNOPSIS
    MVP-W MCU 固件构建脚本

.DESCRIPTION
    编译固件并复制到 release 目录。

.NOTES
    必须在 ESP-IDF PowerShell 中运行：
    C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1
#>

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildDir = Join-Path $ScriptDir "build"
$ReleaseDir = Join-Path $ScriptDir "release"

# 颜色输出函数
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MVP-W MCU Firmware Builder v1.5.0" -ForegroundColor Cyan
Write-Host "  (ESP32 舵机控制 + BLE)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 ESP-IDF 环境
try {
    $null = idf.py --version 2>&1
} catch {
    Write-Error "未检测到 ESP-IDF 环境"
    Write-Host "请先运行: C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1"
    exit 1
}

# 切换到项目目录
Set-Location $ScriptDir

# 构建
Write-Info "开始编译..."
idf.py build

if ($LASTEXITCODE -ne 0) {
    Write-Error "编译失败"
    exit 1
}

Write-Success "编译完成"

# 创建 release 目录
if (-not (Test-Path $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir | Out-Null
}

# 复制固件到 release 目录
Write-Info "复制固件到 release 目录..."

$files = @(
    @{Src = "build\bootloader\bootloader.bin"; Dst = "release\bootloader.bin"},
    @{Src = "build\partition_table\partition-table.bin"; Dst = "release\partition-table.bin"},
    @{Src = "build\WatcherRobotBody.bin"; Dst = "release\MVP-W-MCU.bin"}
)

foreach ($file in $files) {
    $src = Join-Path $ScriptDir $file.Src
    $dst = Join-Path $ScriptDir $file.Dst

    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        $size = (Get-Item $dst).Length / 1KB
        Write-Host "  ✓ $(Split-Path $file.Dst -Leaf) ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
    } else {
        Write-Warning "  ✗ $(Split-Path $file.Src -Leaf) 不存在"
    }
}

Write-Host ""
Write-Success "========================================"
Write-Success "  构建完成！"
Write-Success "========================================"
Write-Host ""
Write-Info "固件位置: $ReleaseDir"
Write-Host ""
Write-Info "烧录命令:"
Write-Host "  .\flash.ps1 -Port COM4" -ForegroundColor Yellow
Write-Host ""
