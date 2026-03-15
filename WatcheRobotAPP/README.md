# WatcherRobotAPP

<p align="center">
  <img src="./icon.png" alt="Watcher Robot Logo" width="128" height="128" />
</p>

<p align="center">
  <a href="https://github.com/watcher-robot/watcher-robot-app">
    <img src="https://img.shields.io/github/license/watcher-robot/watcher-robot-app?style=flat-square" alt="GPL-3.0 License" />
  </a>
  <a href="https://github.com/watcher-robot/watcher-robot-app/stargazers">
    <img src="https://img.shields.io/github/stars/watcher-robot/watcher-robot-app?style=flat-square" alt="Stars" />
  </a>
  <a href="https://github.com/watcher-robot/watcher-robot-app/issues">
    <img src="https://img.shields.io/github/issues/watcher-robot/watcher-robot-app?style=flat-square" alt="Issues" />
  </a>
  <a href="https://reactnative.dev">
    <img src="https://img.shields.io/badge/React%20Native-0.84.1-61DAFB?style=flat-square&logo=react" alt="React Native" />
  </a>
</p>

> A React Native application for controlling dual-axis robot (Watcher Robot) via Bluetooth Low Energy (BLE).

[English](./README.md) | [中文](./README_zh.md)

## Features

- **Bluetooth Connection** - Scan and connect to Watcher Robot via BLE
- **Manual Control** - Joystick and directional control for real-time robot manipulation
- **Motion Playback** - Play pre-defined actions or custom Blender animations
- **Dance Programming** - Program custom dance sequences with motion combinations

## Demo Screenshots

| Bluetooth | Control | Motion | Dance |
|-----------|---------|--------|-------|
| ![Bluetooth](./docs/images/bluetooth.png) | ![Control](./docs/images/control.png) | ![Motion](./docs/images/motion.png) | ![Dance](./docs/images/dance.png) |

## Technical Stack

- **Framework**: React Native 0.84.1
- **Language**: TypeScript
- **State Management**: Redux Toolkit + React Redux
- **Navigation**: React Navigation (Bottom Tabs)
- **Bluetooth**: react-native-ble-plx
- **Storage**: @react-native-async-storage/async-storage

## Quick Start

### Prerequisites

- Node.js >= 22.11.0
- React Native CLI
- Android Studio / Xcode (for iOS)

### Installation

```bash
# Clone the repository
git clone https://github.com/watcher-robot/watcher-robot-app.git
cd watcher-robot-app

# Install dependencies
npm install
# or
yarn install

# Install iOS pods (iOS only)
cd ios && pod install && cd ..
```

### Running

```bash
# Start Metro bundler
npm start
# or
yarn start

# Run on Android
npm run android
# or
yarn android

# Run on iOS
npm run ios
# or
yarn ios
```

## BLE Communication Protocol

### Service UUID

| UUID | Name | Description |
|------|------|-------------|
| `0000FF00-0000-1000-8000-00805F9B34FB` | SERVICE_UUID | Main BLE Service |

### Characteristics

| UUID | Name | Direction | Description |
|------|------|-----------|-------------|
| `0000FF01-0000-1000-8000-00805F9B34FB` | SERVO_CTRL | Write | Servo motor control |
| `0000FF02-0000-1000-8000-00805F9B34FB` | ACTION_CTRL | Write | Pre-defined action control |
| `0000FF03-0000-1000-8000-00805F9B34FB` | RESPONSE | Notify | Device response |

### Command Reference

| Command | Format | Description |
|---------|--------|-------------|
| `SET_SERVO` | `SET_SERVO:<servoId>:<angle>` | Set servo angle immediately |
| `SERVO_MOVE` | `SERVO_MOVE:<servoId>:<direction>` | Continuous movement (for joystick) |
| `PLAY_ACTION` | `PLAY_ACTION:<actionId>` | Play pre-defined action (0-1) |
| `QUEUE_ADD` | `QUEUE_ADD:<servoId>:<angle>:<duration>` | Add command to queue |
| `QUEUE_CLEAR` | `QUEUE_CLEAR` | Clear command queue |
| `QUEUE_START` | `QUEUE_START` | Start executing queue |

### Servo Configuration

| Property | Value | Description |
|----------|-------|-------------|
| SERVO_X | 0 | Base axis (GPIO 12) |
| SERVO_Y | 1 | Head axis (GPIO 15) |
| ANGLE_MIN_X | 30° | X-axis minimum angle |
| ANGLE_MAX_X | 150° | X-axis maximum angle |
| ANGLE_MIN_Y | 95° | Y-axis minimum angle |
| ANGLE_MAX_Y | 150° | Y-axis maximum angle |
| DEFAULT_ANGLE | 90° | Default center angle |

## Project Structure

```
src/
├── modules/
│   ├── bluetooth/           # BLE functionality
│   │   ├── components/      # UI components
│   │   ├── config/         # Configuration files
│   │   ├── constants/      # BLE constants
│   │   ├── hooks/         # Custom hooks
│   │   ├── screens/       # Bluetooth screen
│   │   ├── services/      # Business logic
│   │   ├── store/        # Redux store
│   │   └── types/        # TypeScript types
│   └── app-text/          # Localization
├── screens/                # Page components
├── navigation/             # Navigation configuration
├── types/                  # Global TypeScript types
├── utils/                  # Utility functions
└── assets/                 # Animation JSON files
```

## Adding Custom Animations

1. Export animation from Blender as JSON (watcher animation format)
2. Place JSON file in `src/assets/`
3. Import and add to animation list in `MotionPage.tsx`:

```typescript
import myAnimationJson from '../assets/my_animation.json';

const ANIMATIONS = [
  { id: 'my_animation', name: 'My Animation', json: myAnimationJson },
];
```

## Related Projects

- [watcher-robot-firmware](https://github.com/watcher-robot/watcher-robot-firmware) - ESP32 firmware for Watcher Robot

## Contributing

Contributions are welcome! Please read our [Contributing Guide](./CONTRIBUTING.md) first.

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

See [LICENSE](./LICENSE) file for details.

```
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
```

---

<p align="center">Made with ❤️ for the open source community</p>
