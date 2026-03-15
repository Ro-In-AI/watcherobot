#Requires -Version 5.1
<#
.SYNOPSIS
    生成 MVP-W S3 合并固件

.DESCRIPTION
    将分离的固件文件合并为单个 bin 文件，便于首次烧录。

.EXAMPLE
    .\merge_firmware.ps1

.NOTES
    需要安装 esptool: pip install esptool
#>

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FirmwareDir = Join-Path $ScriptDir "firmware"
$OutputFile = Join-Path $ScriptDir "MVP-W-S3-combined.bin"

# 检查 esptool
try {
    $null = esptool.py version 2>&1
} catch {
    Write-Host "[ERROR] 未找到 esptool。请运行: pip install esptool" -ForegroundColor Red
    exit 1
}

# 检查固件文件
$files = @(
    "bootloader.bin",
    "partition-table.bin",
    "MVP-W-S3.bin",
    "srmodels.bin",
    "storage.bin"
)

foreach ($file in $files) {
    $path = Join-Path $FirmwareDir $file
    if (-not (Test-Path $path)) {
        Write-Host "[ERROR] 缺少固件文件: $path" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[INFO] 生成合并固件..." -ForegroundColor Cyan

esptool.py --chip esp32s3 merge_bin `
    -o $OutputFile `
    --flash_mode dio `
    --flash_size 16MB `
    --flash_freq 80m `
    0x0 (Join-Path $FirmwareDir "bootloader.bin") `
    0x8000 (Join-Path $FirmwareDir "partition-table.bin") `
    0x10000 (Join-Path $FirmwareDir "MVP-W-S3.bin") `
    0x410000 (Join-Path $FirmwareDir "srmodels.bin") `
    0x460000 (Join-Path $FirmwareDir "storage.bin")

if ($LASTEXITCODE -eq 0) {
    $size = (Get-Item $OutputFile).Length / 1MB
    Write-Host "[OK] 合并固件已生成: $OutputFile ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] 生成失败" -ForegroundColor Red
    exit 1
}
