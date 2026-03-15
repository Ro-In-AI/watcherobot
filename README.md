<h1 align="center">WatcherRobot: Mini Desktop OpenClaw Robot</h1>

<div align="center">

> A desktop-level OpenClaw voice interaction robot based on SenseCAP Watcher

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-ESP32%20%7C%20React%20Native%20%7C%20Python-blue)]()
[![Status](https://img.shields.io/badge/status-Active-green)]()

<p align="center">
  <img src="./icon.png" alt="Watcher Robot Logo" width="200" height="200" />
</p>

</div>

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
  - [Firmware](#firmware-embedded-firmware)
  - [WatcherServer](#watcherserver-pc-voice-service)
  - [WatcheRobotAPP](#watcherrobotapp-mobile-app)
  - [Hardware](#hardware-hardware-design)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)
- [FAQ](#faq)

---

## Introduction

WatcherRobot is an open-source desktop-level OpenClaw voice interaction platform designed for education and research purposes. The project uses SenseCAP Watcher module for core control functionality, enabling voice-based interaction with the robot through the OpenClaw system.

### Target Users

- Robotics enthusiasts
- Embedded development learners
- Educational institutions
- Researchers

---

## Features

- 🎙️ **Voice Control** - Voice command support via OpenClaw for robot interaction
- 📱 **Mobile App** - Cross-platform mobile app built with React Native
- 🖥️ **PC Server** - Backend service for OpenClaw voice functionality
- 🔧 **Modular Design** - Firmware, hardware, and software separated for easy development
- 🛠️ **Extensibility** - Support for feature expansion and custom development

---

## Directory Structure

```
Watcher/
├── Firmware/               # Embedded firmware code
│   ├── MVP-W/             # MVP-W firmware (v1.5.0)
│   │   ├── firmware/
│   │   │   ├── s3/       # ESP32-S3 main firmware
│   │   │   └── mcu/      # ESP32 MCU servo control
│   │   ├── releases/     # Pre-built firmware binaries
│   │   ├── docs/         # Firmware documentation
│   │   ├── server/       # Python edge server
│   │   └── README.md     # Firmware guide
│   └── CLAUDE.md        # Firmware development guide
│
├── WatcherServer/         # PC voice service
│   ├── src/               # Source code
│   ├── docs/              # Development documentation
│   ├── tests/             # Test cases
│   ├── config/            # Configuration files
│   ├── main.py            # Entry point
│   └── README.md          # Server documentation
│
├── WatcheRobotAPP/        # Mobile app (React Native)
│   ├── src/               # Source code
│   ├── ios/               # iOS project
│   ├── android/           # Android project
│   ├── docs/              # App documentation
│   └── README.md          # App documentation
│
├── Hardware/              # Hardware design (PCB, structure)
│   ├── PCB.pcbdoc/schdoc # PCB design files
│   ├── Gerber/           # PCB manufacturing files
│   ├── BOM/              # Bill of materials
│   ├── RobotModel/       # 3D structural models
│   └── Assets/           # Design assets
│
├── Design/                # Design files
│   └── (to be added)
│
├── LICENSE                # GNU GPL v3 License
├── CONTRIBUTING.md        # Contributing guidelines
├── CODE_OF_CONDUCT.md    # Code of conduct
└── README.md             # This file
```

---

## Getting Started

### Firmware (Embedded Firmware)

The Firmware directory contains MVP-W (Minimum Viable Product) firmware, featuring dual-chip architecture with ESP32-S3 main controller and ESP32 MCU for servo control.

**System Features:**
- End-to-end voice interaction (ASR → LLM → TTS)
- ESP-SR offline wake word detection ("Hi 乐鑫")
- VAD (Voice Activity Detection) auto-stop
- PNG animation display (24-frame expressions)
- WebSocket bidirectional communication
- UDP service discovery
- Dual-axis gimbal control (MCU + BLE)

**Hardware Requirements:**
- **S3 Main Controller**: ESP32-S3 (16MB Flash + 8MB PSRAM)
- **MCU Servo Controller**: ESP32 (4MB Flash)
- **Microphone**: I2S DMIC, 16kHz sampling
- **Speaker**: I2S, 24kHz playback
- **Servos**: PWM × 2 (X-axis: GPIO 12, Y-axis: GPIO 15)

**Build Steps:**

```bash
# S3 Main Firmware
cd Firmware/MVP-W/firmware/s3
idf.py set-target esp32s3
idf.py build

# MCU Servo Firmware
cd Firmware/MVP-W/firmware/mcu
idf.py set-target esp32
idf.py build
```

For detailed firmware documentation and flashing instructions, see [Firmware/MVP-W/README.md](Firmware/MVP-W/README.md)

---

### WatcherServer (PC Voice Service)

WatcherServer provides OpenClaw-based voice services, handling Automatic Speech Recognition (ASR) and Text-to-Speech (TTS).

**Requirements:**
- Python 3.8+
- Conda or venv environment

**Quick Start:**

```bash
# 1. Create and activate environment
conda env create -f environment.yml
conda activate watcher

# 2. Copy configuration
cp .env.example .env
# Edit .env file to configure necessary API keys

# 3. Start service
python main.py
```

For detailed instructions, see [WatcherServer/README.md](WatcherServer/README.md)

---

### WatcheRobotAPP (Mobile App)

A cross-platform mobile app built with React Native for controlling the robot and interacting with OpenClaw voice services.

**Requirements:**
- Node.js 18+
- Yarn or npm
- React Native CLI
- Xcode (iOS development)
- Android Studio (Android development)

**Installation:**

```bash
cd WatcheRobotAPP

# Install dependencies
yarn install

# Run on iOS
yarn ios

# Run on Android
yarn android
```

For detailed instructions, see [WatcheRobotAPP/README.md](WatcheRobotAPP/README.md)

---

### Hardware (Hardware Design)

The Hardware directory contains PCB design files and 3D structural model files.

**Directory Structure:**

```
Hardware/
├── PCB.pcbdoc           # PCB design file (Altium Designer)
├── PCB.schdoc           # PCB schematic file
├── Schematic_PDF.pdf    # Schematic PDF version
├── README.md            # Hardware design documentation
├── Assets/              # Design assets
│   ├── render.png       # Render image
│   ├── render.gif       # Render animation
│   └── WatcheRobot.PNG  # Showcase image
├── Gerber/              # PCB manufacturing files
├── BOM/                 # Bill of materials
│   └── BOM.xls          # BOM Excel file
└── RobotModel/          # 3D model files (STEP/STL)
    ├── 机身.stl             # Body 3D model
    ├── 机身加灯带.stl       # Body with LED strip
    ├── 底座.step            # Base
    ├── 支架前盖.step        # Front bracket
    ├── 支架后壳.step        # Back bracket
    ├── MG90S Assembly SERVO-_.step  # Servo model
    ├── 3D_PCB1_Layout.step          # PCB 3D model
    └── ...
```

**Main Components:**

- Main Controller: ESP32-S3
- Servos: MG90S × 3 (optional for motion control)
- Sensors: Extended IO, environmental sensor interfaces

For detailed documentation, see [Hardware/README.md](Hardware/README.md)

---

## Tech Stack

| Module | Technology |
|--------|------------|
| Embedded Firmware | ESP-IDF, ESP32-S3, ESP32 (MCU), FreeRTOS, LVGL, ESP-SR |
| PC Server | Python, WebSocket, ASR (Alibaba Cloud), LLM (Claude API), TTS (Volcengine) |
| Mobile App | React Native, TypeScript |
| Hardware | Altium Designer (PCB), Fusion 360 (3D) |

---

## Contributing

Contributions to WatcherRobot are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) to learn how to participate.

### Reporting Issues

- Search for existing issues before opening a new one
- Issues should include clear problem descriptions and reproduction steps
- For feature requests, please describe the use case and expected behavior

### Submitting Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **GNU General Public License v3.0**.

See the [LICENSE](LICENSE) file for details.

---

## FAQ

### Q: Which development boards are supported?

A: Currently, ESP32-S3 series development boards are primarily supported. Other ESP32 models are being adapted.

### Q: How to obtain voice API keys?

A: Please refer to [WatcherServer/DEVELOPMENT.md](WatcherServer/DEVELOPMENT.md) for supported ASR/TTS service configuration methods.

### Q: Can other voice assistants be used?

A: Yes, WatcherServer uses a modular design and can add new voice service support according to the documentation.

### Q: Where are the hardware design files?

A: Hardware design files have been released in the Hardware directory, including:
- PCB design files (Altium Designer format)
- Gerber manufacturing files
- 3D structural models (STEP/STL format)
- BOM (Bill of Materials)

For detailed documentation, see [Hardware/README.md](Hardware/README.md)

---

## Contact

- Issue Tracker: [GitHub Issues](https://github.com/Ro-In-AI/WatcheRobot/issues)
- Discussions: [GitHub Discussions](https://github.com/Ro-In-AI/WatcheRobot/discussions)

---

<div align="center">

**Thanks for your attention and support!** ⭐

If you find this project helpful, please give it a Star!

</div>
