# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- UART communication support for MVP-W S3 integration
- Release binaries for easy flashing
- Cross-platform build and flash scripts

### Changed
- Optimized servo tracking period from 15ms to 10ms for smoother movement
- Improved servo queue command system for async motion control

## [1.0.0] - 2026-03-06

### Added
- BLE GATT Server with custom service (UUID 0x00FF)
- Dual servo control (X/Y axis) via LEDC PWM
- Three servo control modes:
  - Smooth tracking mode (slider/dial control)
  - Time-controlled mode (specified duration)
  - Joystick mode (continuous movement)
- Preset actions (wave, greet)
- FreeRTOS task-based architecture
- Command parsing layer for BLE/UART

### Hardware Support
- ESP32 target chip
- GPIO 12: X-axis servo
- GPIO 15: Y-axis servo
- PWM frequency: 50Hz
- Servo angle range: 0-180°

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-03-06 | Initial release with BLE servo control |
