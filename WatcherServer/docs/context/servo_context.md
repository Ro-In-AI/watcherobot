# 舵机模块上下文

> **最后更新**: 2026-03-04
> **主要实现**: ServoController (舵机动画控制器)

## 模块概述

舵机模块负责读取 JSON 格式的动画文件，并按时间轴发送舵机角度数据到客户端。支持循环播放和独占播放两种模式。

## 文件结构

```
src/modules/servo/
├── __init__.py
└── controller.py        # ServoController 实现
```

## 核心类

### ServoController

**文件**: [src/modules/servo/controller.py](../../src/modules/servo/controller.py)

#### 初始化参数

```python
ServoController(
    json_dir: str = "src/assets/JSON"   # JSON 动画文件目录
)
```

#### 数据模型

```python
@dataclass
class ServoFrame:
    """单帧数据（顺序帧格式）"""
    x: int  # X 轴角度
    y: int  # Y 轴角度

@dataclass
class ServoAnimation:
    """单个动画数据"""
    name: str
    fps: int
    frames: list[ServoFrame]  # 顺序帧列表（每帧同时包含 x 和 y）
    duration: float  # 动画总时长（秒）
```

#### 工作模式

**1. 循环播放模式** (`start`)

```python
await controller.start(state="speech_nod", loop=True)
```

- 持续循环播放动画
- 可以通过 `stop()` 停止
- 会被独占播放中断

**2. 独占播放模式** (`play_once`)

```python
await controller.play_once(state="speech_nod")
```

- 播放一次完整的动画
- 优先级更高，会中断当前循环播放
- 播放过程中不可停止
- x 和 y 按各自的时间轴分别发送（虽然每帧都有 x 和 y，但按顺序发送）

#### 关键实现细节

**动画加载**：

```python
async def load_animations(self):
    json_path = Path(self.json_dir)
    json_files = list(json_path.glob("*.json"))

    for json_file in json_files:
        state_name = json_file.stem
        animation = self._load_json(json_file)
        self.animations[state_name] = animation
```

**JSON 文件格式**：

```json
{
  "fps": 5,
  "animated_objects": [
    {
      "object_name": "头轴",
      "keyframe_data": [
        {
          "frame_number": 1,
          "rotation_angle": 90
        },
        {
          "frame_number": 10,
          "rotation_angle": 45
        }
      ]
    },
    {
      "object_name": "底部轴",
      "keyframe_data": [...]
    }
  ]
}
```

**轴映射规则**：
- `头轴` → y 轴（上下）
- `底部轴` → x 轴（左右）

**帧合并**：

将 x 和 y 的关键帧合并为顺序帧列表：

```python
# 分离 x 和 y 轴数据
x_frames_dict: dict[int, int] = {}  # frame_number -> angle
y_frames_dict: dict[int, int] = {}

# 合并为顺序帧列表
max_frame = max(max(x_frames_dict.keys()), max(y_frames_dict.keys()))
frames = []
for frame_num in range(1, max_frame + 1):
    x_angle = x_frames_dict.get(frame_num, 90)  # 默认值 90
    y_angle = y_frames_dict.get(frame_num, 90)
    frames.append(ServoFrame(x=x_angle, y=y_angle))
```

**循环播放实现**：

```python
async def _play_animation(self, state: str, loop: bool):
    animation = self.animations[state]
    frame_interval = 1.0 / animation.fps

    while self._is_playing:
        for frame in animation.frames:
            if not self._is_playing:
                break
            if self._send_callback:
                await self._send_callback(x=frame.x, y=frame.y)
            await asyncio.sleep(frame_interval)

        if not loop:
            break
```

**独占播放实现**：

```python
async def play_once(self, state: str):
    async with self._exclusive_lock:
        self._is_exclusive = True

        # 停止当前的循环播放
        if self._is_playing and self._current_task:
            self._is_playing = False
            self._current_task.cancel()

        # 开始独占播放
        await self._play_animation_by_timestamp(animation)

        self._is_exclusive = False
```

**发送回调**：

通过回调函数发送舵机数据：

```python
def set_send_callback(self, callback: callable):
    """callback 应该是 async 函数，接收 (x, y) 参数"""

# 使用示例
async def send_servo(x=None, y=None):
    await msg_handler.send_servo(x, y)

controller.set_send_callback(send_servo)
```

## 配置

### 环境变量

```bash
# 舵机配置
SERVO_JSON_DIR=src/assets/JSON    # 舵机 JSON 动画文件目录
SERVO_FRAME_RATE=30               # 舵机帧率 (FPS)
```

### JSON 文件位置

默认目录：`src/assets/JSON/`

示例文件结构：
```
src/assets/JSON/
├── speech_nod.json
├── speech_shake.json
├── idle.json
└── ...
```

## 使用示例

### 基本使用

```python
from src.modules.servo.controller import ServoController

# 创建控制器
controller = ServoController(json_dir="src/assets/JSON")

# 加载动画
await controller.load_animations()

# 设置发送回调
async def send_servo(x=None, y=None):
    print(f"发送舵机数据: x={x}, y={y}")

controller.set_send_callback(send_servo)

# 循环播放
await controller.start("speech_nod", loop=True)

# 停止播放
await controller.stop()

# 独占播放（一次性）
await controller.play_once("speech_nod")

# 获取可用动画列表
states = controller.get_available_states()
print(states)  # ['speech_nod', 'speech_shake', 'idle', ...]
```

### 在 WebSocket 服务中使用

```python
# websocket_server.py

# 初始化时加载动画
await self.servo_controller.load_animations()

# 发送可用状态列表给客户端
servo_states = self.servo_controller.get_available_states()
await msg_handler.send_servo_states(servo_states)

# 设置发送回调
async def send_servo(x=None, y=None):
    await msg_handler.send_servo(x, y)

self.servo_controller.set_send_callback(send_servo)

# 客户端请求循环播放
if action == "start" and state:
    await self.servo_controller.start(state, loop=True)

# 客户端请求停止
if action == "stop":
    await self.servo_controller.stop()

# 客户端请求独占播放（type: "state"）
if msg_type == "state":
    await self.servo_controller.play_once(data)
```

### TTS 播放时同步舵机动画

```python
# 设置 TTS 使用的舵机动画状态
self.tts_servo_state = "watcher_animation"

# TTS 播放时自动使用该状态
async for tts_result in self.tts_provider.synthesize_stream(text):
    if first_chunk:
        await self.servo_controller.start(self.tts_servo_state, loop=True)
        first_chunk = False
    await websocket.send(tts_result.audio_data)

await self.servo_controller.stop()
```

## WebSocket 消息协议

### 客户端 → 服务端

**循环播放控制**：
```json
// 开始播放
{"type": "servo", "action": "start", "state": "speech_nod"}

// 停止播放
{"type": "servo", "action": "stop"}
```

**独占播放**：
```json
{"type": "state", "data": "speech_nod"}
```

### 服务端 → 客户端

**舵机数据**（x 和 y 可能分开发送）：
```json
// 发送 x 轴
{"type": "servo", "code": 0, "data": {"x": 90}}

// 发送 y 轴
{"type": "servo", "code": 0, "data": {"y": 45}}
```

**可用状态列表**：
```json
{"type": "servo_states", "code": 0, "data": {"states": ["speech_nod", "speech_shake", ...]}}
```

## 客户端实现示例

```javascript
// 维护当前舵机状态
let currentX = 90;
let currentY = 90;

// 接收舵机数据
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'servo') {
        // 分别处理 x 和 y
        if (msg.data.x !== undefined && msg.data.x !== null) {
            currentX = msg.data.x;
            // 执行舵机控制
            controlServoX(currentX);
        }
        if (msg.data.y !== undefined && msg.data.y !== null) {
            currentY = msg.data.y;
            // 执行舵机控制
            controlServoY(currentY);
        }
    }
};

// 发送舵机动画请求
function startServoAnimation(state) {
    ws.send(JSON.stringify({
        type: 'servo',
        action: 'start',
        state: state
    }));
}

function stopServoAnimation() {
    ws.send(JSON.stringify({
        type: 'servo',
        action: 'stop'
    }));
}
```

## 常见问题

### Q: 动画不播放

**可能原因**：
1. JSON 文件格式错误
2. 文件路径配置错误
3. 未设置发送回调

**解决方法**：
- 检查 `servo_json_dir` 配置
- 确认 JSON 文件包含 `fps` 和 `animated_objects`
- 检查日志中的动画加载信息
- 确保设置了 `set_send_callback()`

### Q: 舵机角度不对

**可能原因**：
1. 轴映射错误（`头轴` 应该是 y，`底部轴` 应该是 x）
2. 角度值超出范围（0-180）

**解决方法**：
- 检查 JSON 文件中的 `object_name`
- 确认角度值在 0-180 范围内

### Q: 动画播放速度不对

**可能原因**：
1. `fps` 配置错误
2. 发送延迟导致实际帧率低于配置

**解决方法**：
- 检查 JSON 文件中的 `fps` 值
- 优化网络延迟

## 最近修改记录

- **2026-03-04**: 添加独占播放模式（play_once）
- **2026-03-04**: 支持异步发送回调
- **2026-03-04**: 实现 X/Y 轴独立时间轴发送

---

**注意**: 修改此模块后，请更新本文档的"最近修改记录"部分。
