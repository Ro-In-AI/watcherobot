# 动作数据发送机制说明

## 概述

MotionPage 提供了两种控制机器人的方式：
1. **预设动作** - 嵌入式预设动作（ID 0-1）
2. **Blender 动画** - 自定义 JSON 关键帧动画

---

## 数据流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MotionPage 动作发送流程                           │
└─────────────────────────────────────────────────────────────────────────┘

  用户点击动作/动画
         │
         ▼
  ┌─────────────────┐
  │ 检查蓝牙连接    │ ── 未连接 ──▶ Alert 提示
  └────────┬────────┘
           │ 已连接
           ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                         两种发送模式                                 │
  └─────────────────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
  ┌──────────────────────┐      ┌──────────────────────────────────────┐
  │   预设动作模式        │      │         Blender 动画模式               │
  └──────────┬───────────┘      └──────────────────┬───────────────────┘
             │                                        │
             ▼                                        ▼
  ┌──────────────────────┐              ┌────────────────────────────────┐
  │ 1. sendActionCommand │              │ 1. parseBlenderAnimation()     │
  │    PLAY_ACTION:<ID>  │              │    解析 JSON → AnimationMeta   │
  └──────────────────────┘              └────────────────┬───────────────┘
                                                        │
                                                        ▼
                                             ┌────────────────────────┐
                                             │ 2. generateESP32Cmds() │
                                             │    生成命令队列        │
                                             └───────────┬────────────┘
                                                         │
                                                         ▼
                                              ┌────────────────────────┐
                                              │ 3. 循环发送命令        │
                                              │  for cmd in commands  │
                                              │    await sendBLECmd   │
                                              │    delay 10ms         │
                                              └────────────────────────┘
```

---

## 预设动作模式

### 发送函数
```typescript
// 文件: MotionPage.tsx 第 69-88 行
const sendActionCommand = useCallback(async (actionId: number) => {
  // 1. 检查连接
  if (!isConnected) { ... }

  // 2. 构建命令
  const command = COMMANDS.PLAY_ACTION(actionId);
  //    例: PLAY_ACTION:0

  // 3. 发送到 ACTION_CTRL 特征值
  await sendCommand({
    data: command,
    serviceUUID: BLUETOOTH_UUIDS.SERVICE_UUID,  // '00FF'
    characteristicUUID: BLUETOOTH_UUIDS.ACTION_CTRL,  // 'FF02'
    type: 'response',
  });
}, [isConnected, sendCommand]);
```

### 命令格式
```
PLAY_ACTION:<actionId>

例:
PLAY_ACTION:0   → 播放动作 ID 0 (挥手)
PLAY_ACTION:1   → 播放动作 ID 1 (问候)
```

### 特征值
| UUID | 名称 | 用途 |
|------|------|------|
| `00FF` | SERVICE_UUID | 主服务 UUID |
| `FF02` | ACTION_CTRL | 动作控制特征值 |

---

## Blender 动画模式

### 完整流程

#### 第 1 步: 解析 JSON 文件
```typescript
// MotionPage.tsx 第 91-127 行
const playAnimation = useCallback(async (animation) => {
  // 解析 Blender 导出的 JSON
  const parsed = parseBlenderAnimation(animation.json, animation.name);
  // 返回 AnimationMeta 对象
}, ...);
```

**解析函数** (`animationParser.ts`):
```typescript
function parseBlenderAnimation(json, name) {
  // 1. 计算每帧时间: msPerFrame = 1000 / fps
  // 2. 遍历所有 animated_objects (舵机)
  // 3. 对每个关键帧计算:
  //    - durationMs = (currFrame - prevFrame) / fps * 1000
  //    - angle = rotation_angle
  // 4. 返回 { name, duration, servoCommands[] }
}
```

#### 第 2 步: 生成 ESP32 命令
```typescript
// 生成命令队列
const commands = generateESP32Commands(parsed);

// 输出格式:
[
  'QUEUE_CLEAR',                              // 先清空队列
  'QUEUE_ADD:0:90:100',                      // 舵机0 → 90° → 100ms
  'QUEUE_ADD:1:120:150',                     // 舵机1 → 120° → 150ms
  'QUEUE_ADD:0:45:200',                      // 舵机0 → 45° → 200ms
  ...
]
```

#### 第 3 步: 循环发送
```typescript
// 依次发送所有命令
for (const cmd of commands) {
  await sendBLECommand(cmd);      // 发送命令
  await new Promise(r => setTimeout(r, 10));  // 延迟 10ms
}
```

---

## 核心命令格式

| 命令 | 格式 | 说明 |
|------|------|------|
| `SET_SERVO` | `SET_SERVO:<servoId>:<angle>` | 立即设置舵机角度 |
| `SERVO_MOVE` | `SERVO_MOVE:<servoId>:<direction>` | 持续移动 (摇杆) |
| `PLAY_ACTION` | `PLAY_ACTION:<actionId>` | 播放预设动作 |
| `QUEUE_ADD` | `QUEUE_ADD:<servoId>:<angle>:<duration>` | 添加到队列 |
| `QUEUE_CLEAR` | `QUEUE_CLEAR` | 清空队列 |
| `QUEUE_START` | `QUEUE_START` | 开始执行队列 |

---

## 数据类型定义

### BlenderAnimation (JSON 格式)
```typescript
interface BlenderAnimation {
  scene_name: string;
  frame_start: number;
  frame_end: number;
  fps: number;
  animated_objects: AnimatedObject[];
}

interface AnimatedObject {
  object_name: string;    // '底部轴' 或 '头轴'
  object_type: string;
  action_name: string;
  keyframe_data: AnimationKeyframe[];
}

interface AnimationKeyframe {
  frame_number: number;
  active_axis: string;
  rotation_angle: number;  // 目标角度
}
```

### AnimationMeta (解析后)
```typescript
interface AnimationMeta {
  name: string;
  duration: number;       // 总时长 ms
  servoCommands: ServoCommand[];
}

interface ServoCommand {
  servoId: number;       // 0 = 底部轴/X轴, 1 = 头轴/Y轴
  angle: number;         // 目标角度
  durationMs: number;    // 移动时间
}
```

---

## 舵机配置

| 属性 | 值 | 说明 |
|------|-----|------|
| SERVO_X | 0 | 底部轴 (GPIO 12) |
| SERVO_Y | 1 | 头轴 (GPIO 15) |
| ANGLE_MIN_X | 30 | X轴最小角度 |
| ANGLE_MAX_X | 150 | X轴最大角度 |
| ANGLE_MIN_Y | 95 | Y轴最小角度 |
| ANGLE_MAX_Y | 150 | Y轴最大角度 |
| DEFAULT_ANGLE | 90 | 默认角度 |

---

## ESP32 端行为

当接收到命令时的处理:

1. **QUEUE_CLEAR** → 清空当前命令队列
2. **QUEUE_ADD:id:angle:duration** →
   - 添加命令到队列
   - ESP32 检测到队列非空自动开始执行
   - 按顺序执行，每条命令执行 `duration` 时间后执行下一条
3. **SET_SERVO:id:angle** → 立即设置舵机角度
4. **PLAY_ACTION:id** → 播放嵌入式预设动作

---

## 新增动画文件

将 JSON 文件放入 `src/assets/` 目录，然后在 `MotionPage.tsx` 中:

1. 导入:
   ```typescript
   import xxxAnimationJson from '../assets/xxx_watcher_animation.json';
   ```

2. 添加到列表:
   ```typescript
   const ANIMATIONS = [
     { id: 'xxx', name: '动画名', json: xxxAnimationJson as BlenderAnimation },
   ];
   ```

---

## 文件结构

```
src/
├── screens/
│   └── MotionPage.tsx          # 动作控制页面
├── utils/
│   └── animationParser.ts       # 动画解析工具
├── modules/bluetooth/
│   └── constants/
│       └── bluetoothConstants.ts # 命令常量定义
├── types/
│   └── animation.ts            # 数据类型定义
└── assets/
    ├── 思考 - 关键_watcher_animation.json
    ├── 睡觉 - 关键_watcher_animation.json
    └── 测试 - X_watcher_animation.json
```
