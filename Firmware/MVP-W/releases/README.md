# MVP-W 固件发布

本目录包含 MVP-W ESP32-S3 固件的预编译版本，用户无需编译源码即可烧录使用。

## 版本列表

| 版本 | 发布日期 | 说明 |
|------|----------|------|
| [v1.5.0](./v1.5.0/) | 2026-03-15 | 首个开源发布版本 |

## 快速开始

### 1. 安装 esptool

```bash
# Windows/macOS/Linux
pip install esptool
```

### 2. 下载固件

从对应版本目录下载固件文件。

### 3. 烧录

#### Windows
```powershell
cd releases\v1.5.0
.\flash.ps1 -Port COM3
```

#### Linux/macOS
```bash
cd releases/v1.5.0
chmod +x flash.sh
./flash.sh /dev/ttyUSB0
```

## 固件文件说明

| 文件 | 地址 | 大小 | 用途 |
|------|------|------|------|
| `bootloader.bin` | 0x0 | 21KB | ESP-IDF 引导程序 |
| `partition-table.bin` | 0x8000 | 3KB | 分区表 |
| `MVP-W-S3.bin` | 0x10000 | 1.9MB | 应用固件 |
| `srmodels.bin` | 0x410000 | 285KB | ESP-SR 唤醒词模型 |
| `storage.bin` | 0x460000 | 10.5MB | SPIFFS 动画资源 |

## 烧录模式

### 完整烧录（推荐首次使用）
包含所有固件组件，适用于：
- 首次烧录
- 恢复出厂设置
- 固件损坏后修复

```bash
# Windows
.\flash.ps1 -Port COM3 -Full

# Linux/macOS
./flash.sh --full /dev/ttyUSB0
```

### 仅应用更新
仅更新应用固件，适用于：
- OTA 升级
- 保留用户配置

```bash
# Windows
.\flash.ps1 -Port COM3 -AppOnly

# Linux/macOS
./flash.sh --app-only /dev/ttyUSB0
```

## 进入下载模式

ESP32-S3 下载模式操作：
1. 按住 **BOOT** 键
2. 按一下 **RST** 键
3. 松开 **BOOT** 键

## 故障排除

### esptool 找不到设备
- 检查 USB 线是否连接
- 尝试更换 USB 端口
- Windows 用户可能需要安装 [CH340 驱动](http://www.wch.cn/download/CH341SER_EXE.html)

### 烧录失败
- 确保设备处于下载模式（按住 BOOT → 按 RST → 松开 BOOT）
- 尝试擦除 Flash：`-EraseFlash` 或 `--erase`

### 设备无法启动
- 使用完整烧录模式重新烧录
- 检查是否烧录了所有固件组件

## 从源码构建

如需自行编译固件，请参考 [MVP-W/CLAUDE.md](../CLAUDE.md) 中的开发环境配置说明。

```bash
# 激活 ESP-IDF 环境
# Windows PowerShell
C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1

# Linux/macOS
. $HOME/esp/esp-idf/export.sh

# 编译
cd firmware/s3
idf.py build
```

## 相关链接

- [MVP-W 项目文档](../CLAUDE.md)
- [通信协议](../docs/COMMUNICATION_PROTOCOL.md)
- [语音流协议](../docs/VOICE_STREAM_PROTOCOL.md)
