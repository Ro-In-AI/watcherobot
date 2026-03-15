# 变更日志

本文档记录 MVP-W 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.5.0] - 2026-03-11

### 新增
- 唤醒词检测 (ESP-SR "你好小智")
- VAD (语音活动检测) 自动停止录音
- 连续对话支持 (TTS 播放后自动恢复唤醒词)
- PNG 动画系统 (LVGL 412×412)
- 服务发现 UDP 广播

### 修复
- PNG 动画白屏问题 (LV_IMG_CF_RAW_ALPHA 格式)
- PNG 动画花屏问题 (SPIRAM 速度 40MHz → 80MHz)
- 唤醒词检测在 TTS 后恢复
- TTS 采样率修复 (24kHz)

### 技术细节
- 添加 `voice_recorder_resume_wake_word()` 函数
- 同步 sdkconfig.defaults 与 factory_firmware 配置
- 启用 `CONFIG_LV_USE_PNG`, `CONFIG_LV_MEM_CUSTOM`

## [1.4.0] - 2026-03-04

### 新增
- S3 ↔ MCU UART 通信闭环
- 舵机控制验证通过

### 修复
- 按键响应优化
- 物理重启功能

## [1.3.0] - 2026-02-28

### 新增
- MVP 核心功能完成
- WebSocket 双向通信 (v2.0 协议)
- 语音录制 (16kHz PCM)
- TTS 播放 (24kHz PCM)
- ASR 集成 (阿里云)
- TTS 集成 (火山引擎)
- Claude API 集成 (OpenClaw)
- 双轴舵机控制 (UART to MCU)
- LVGL 显示动画
- WiFi 自动重连
- 启动动画 (arc 进度条)

## [1.0.0] - 2026-02-25

### 新增
- 项目初始化
- 基础架构搭建
- S3 固件框架
- MCU 固件框架

---

[1.5.0]: https://github.com/your-org/WatcherProject/MVP-W/releases/tag/v1.5.0
[1.4.0]: https://github.com/your-org/WatcherProject/MVP-W/releases/tag/v1.4.0
[1.3.0]: https://github.com/your-org/WatcherProject/MVP-W/releases/tag/v1.3.0
[1.0.0]: https://github.com/your-org/WatcherProject/MVP-W/releases/tag/v1.0.0
