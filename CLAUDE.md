# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ESP-IDF BLE GATT Server project for WatcherRobotBody. Implements a GATT server with service table on ESP32 series chips.

## Build Commands

```bash
# Set target chip (required before first build)
idf.py set-target <chip_name>

# Build, flash and monitor
idf.py -p PORT flash monitor

# Clean build
idf.py fullclean

# Menuconfig
idf.py menuconfig
```

## Supported Targets

ESP32, ESP32-C2, ESP32-C3, ESP32-C6, ESP32-H2, ESP32-S3

## Architecture

- **GATT Service UUID**: 0x00FF
- **Characteristic UUIDs**: 0xFF01 (A), 0xFF02 (B), 0xFF03 (C)
- Device name: ESP_GATTS_DEMO
- Uses ESP-IDF BLE GATT API with predefined attribute table
- Profile-based architecture supporting multiple profiles (currently 1)

## Key Files

- `main/gatts_table_creat_demo.c` - Main GATT server implementation
- `main/gatts_table_creat_demo.h` - Attribute indices enum
- `sdkconfig.defaults` - Default configuration
