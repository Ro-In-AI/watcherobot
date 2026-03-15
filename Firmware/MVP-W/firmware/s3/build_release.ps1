#Requires -Version 5.1
<#
.SYNOPSIS
    MVP-W S3 固件构建脚本

.DESCRIPTION
    编译固件并复制到 releases 目录。

.NOTES
    必须在 ESP-IDF PowerShell 中运行：
    C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1
#>

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildDir = Join-Path $ScriptDir "build"
$ReleasesDir = Join-Path $ScriptDir "..\..\releases\v1.5.0\firmware"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MVP-W S3 Firmware Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 ESP-IDF 环境
try {
    $null = idf.py --version 2>&1
} catch {
    Write-Host "[ERROR] 未检测到 ESP-IDF 环境" -ForegroundColor Red
    Write-Host "请先运行: C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1" -ForegroundColor Yellow
    exit 1
}

# 构建
Write-Host "[INFO] 开始编译..." -ForegroundColor Cyan
idf.py build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 编译失败" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] 编译完成" -ForegroundColor Green

# 复制到 releases
Write-Host "[INFO] 复制固件到 releases 目录..." -ForegroundColor Cyan

$files = @(
    "MVP-W-S3.bin",
    "bootloader\bootloader.bin",
    "partition_table\partition-table.bin",
    "srmodels\srmodels.bin",
    "storage.bin"
)

foreach ($file in $files) {
    $src = Join-Path $BuildDir $file
    $fileName = Split-Path $file -Leaf
    $dst = Join-Path $ReleasesDir $fileName

    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  - $fileName" -ForegroundColor Green
    } else {
        Write-Host "  - $fileName (不存在)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  构建完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "固件位置: $ReleasesDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步: 运行烧录脚本" -ForegroundColor Yellow
Write-Host "  cd ..\..\releases\v1.5.0" -ForegroundColor Yellow
Write-Host "  .\flash.ps1 -Port COM28" -ForegroundColor Yellow
Write-Host ""
