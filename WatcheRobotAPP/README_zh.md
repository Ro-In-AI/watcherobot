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

> 一款通过蓝牙低功耗（BLE）控制双轴机器人（Watcher Robot）的 React Native 应用。

[English](./README.md) | [中文](./README_zh.md)

## 功能特点

- **蓝牙连接** - 通过 BLE 扫描并连接 Watcher Robot
- **手动控制** - 摇杆和方向键实时控制机器人
- **动作播放** - 播放预设动作或自定义 Blender 动画
- **舞蹈编程** - 组合动作编程自定义舞蹈序列

## 技术栈

- **框架**: React Native 0.84.1
- **语言**: TypeScript
- **状态管理**: Redux Toolkit + React Redux
- **导航**: React Navigation (底部标签栏)
- **蓝牙**: react-native-ble-plx
- **存储**: @react-native-async-storage/async-storage

## 快速开始

### 环境要求

- Node.js >= 22.11.0
- React Native CLI
- Android Studio / Xcode (iOS 开发)

### 安装

```bash
# 克隆仓库
git clone https://github.com/watcher-robot/watcher-robot-app.git
cd watcher-robot-app

# 安装依赖
npm install
# 或
yarn install

# 安装 iOS 依赖 (仅 iOS)
cd ios && pod install && cd ..
```

### 运行

```bash
# 启动 Metro 打包器
npm start
# 或
yarn start

# 运行在 Android
npm run android
# 或
yarn android

# 运行在 iOS
npm run ios
# 或
yarn ios
```

## BLE 通信协议

### 服务 UUID

| UUID | 名称 | 描述 |
|------|------|------|
| `0000FF00-0000-1000-8000-00805F9B34FB` | SERVICE_UUID | 主 BLE 服务 |

### 特征值

| UUID | 名称 | 方向 | 描述 |
|------|------|------|------|
| `0000FF01-0000-1000-8000-00805F9B34FB` | SERVO_CTRL | 写入 | 舵机控制 |
| `0000FF02-0000-1000-8000-00805F9B34FB` | ACTION_CTRL | 写入 | 预设动作控制 |
| `0000FF03-0000-1000-8000-00805F9B34FB` | RESPONSE | 通知 | 设备响应 |

### 命令参考

| 命令 | 格式 | 描述 |
|------|------|------|
| `SET_SERVO` | `SET_SERVO:<舵机ID>:<角度>` | 立即设置舵机角度 |
| `SERVO_MOVE` | `SERVO_MOVE:<舵机ID>:<方向>` | 持续移动（摇杆用） |
| `PLAY_ACTION` | `PLAY_ACTION:<动作ID>` | 播放预设动作 (0-1) |
| `QUEUE_ADD` | `QUEUE_ADD:<舵机ID>:<角度>:<时长>` | 添加命令到队列 |
| `QUEUE_CLEAR` | `QUEUE_CLEAR` | 清空命令队列 |
| `QUEUE_START` | `QUEUE_START` | 开始执行队列 |

### 舵机配置

| 属性 | 值 | 描述 |
|------|------|------|
| SERVO_X | 0 | 底部轴 (GPIO 12) |
| SERVO_Y | 1 | 头轴 (GPIO 15) |
| ANGLE_MIN_X | 30° | X轴最小角度 |
| ANGLE_MAX_X | 150° | X轴最大角度 |
| ANGLE_MIN_Y | 95° | Y轴最小角度 |
| ANGLE_MAX_Y | 150° | Y轴最大角度 |
| DEFAULT_ANGLE | 90° | 默认中间角度 |

## 项目结构

```
src/
├── modules/
│   ├── bluetooth/           # 蓝牙功能模块
│   │   ├── components/      # UI 组件
│   │   ├── config/         # 配置文件
│   │   ├── constants/      # 蓝牙常量
│   │   ├── hooks/          # 自定义 Hooks
│   │   ├── screens         # 蓝牙页面
│   │   ├── services       # 业务逻辑
│   │   ├── store           # Redux 状态管理
│   │   └── types           # TypeScript 类型
│   └── app-text/           # 国际化文本
├── screens/                # 页面组件
├── navigation/             # 导航配置
├── types/                  # 全局类型定义
├── utils/                  # 工具函数
└── assets/                 # 动画 JSON 文件
```

## 添加自定义动画

1. 从 Blender 导出动画为 JSON 格式（watcher animation 格式）
2. 将 JSON 文件放入 `src/assets/` 目录
3. 在 `MotionPage.tsx` 中导入并添加到动画列表：

```typescript
import myAnimationJson from '../assets/my_animation.json';

const ANIMATIONS = [
  { id: 'my_animation', name: '我的动画', json: myAnimationJson },
];
```

## 相关项目

- [watcher-robot-firmware](https://github.com/watcher-robot/watcher-robot-firmware) - Watcher Robot ESP32 固件

## 贡献指南

欢迎贡献代码！请先阅读我们的 [贡献指南](./CONTRIBUTING.md)。

## 许可证

本项目基于 **GNU 通用公共许可证 v3.0 (GPL-3.0)** 许可。

详见 [LICENSE](./LICENSE) 文件。

```
本程序是自由软件：您可以再分发之和/或修改它根据 GNU 通用公共许可证由自由软件基金会，许可证的第 3 版，或（您选择）任何更高版本。

本程序分发希望能有用，但没有任何保证；甚至没有暗示的保证适销性或特定用途的适用性。详见 GNU 通用公共许可证了解更多详情。
```

---

<p align="center">用 ❤️ 为开源社区打造</p>
