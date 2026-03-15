[English](websocket_message_protocol.md) | [中文](websocket_message_protocol_CN.md)

# WebSocket 消息协议文档

## 消息格式

所有消息采用统一的 JSON 格式：

```json
{
  "type": "消息类型",
  "code": 0,
  "data": "消息数据"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 消息类型 |
| code | int | 错误码，`0` 表示成功，`1` 表示错误 |
| data | any | 消息数据 |

---

## 服务端 → 客户端消息

### 1. ASR 识别结果 (asr_result)

语音识别完成后的文本结果。

```json
{"type": "asr_result", "code": 0, "data": "识别到的文本内容"}
```

---

### 2. Bot 回复 (bot_reply)

AI 对话返回的回复文本。

```json
{"type": "bot_reply", "code": 0, "data": "AI 回复内容"}
```

---

### 3. 状态消息 (status)

系统状态变化通知，如 OpenClaw 思考状态、舵机动画状态等。

```json
{"type": "status", "code": 0, "data": "状态描述信息"}
```

**示例场景**：
- OpenClaw 思考中：`[thinking] 正在思考...`
- 舵机动画开始：`舵机动画开始: speech_nod`

---

### 4. 错误消息 (error)

系统错误或异常信息。

```json
{"type": "error", "code": 1, "data": "错误描述信息"}
```

---

### 5. 舵机控制 (servo)

实时舵机角度数据，用于控制机器人动作。

**重要**：x 和 y 可能分开发送（独立的时间轴）。

#### 发送 x 轴数据

```json
{"type": "servo", "code": 0, "data": {"x": 90}}
```

#### 发送 y 轴数据

```json
{"type": "servo", "code": 0, "data": {"y": 45}}
```

#### 同时发送 x 和 y（分开两条消息）

```json
{"type": "servo", "code": 0, "data": {"x": 90}}
{"type": "servo", "code": 0, "data": {"y": 45}}
```

**字段说明**：

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| x | int | 0-180 | X 轴角度，控制左右（可为 null） |
| y | int | 0-180 | Y 轴角度，控制上下（可为 null） |

**客户端接收处理建议**：
- 客户端应分别处理 x 和 y 数据
- 收到 x 数据时只更新 x 轴，y 轴保持不变
- 收到 y 数据时只更新 y 轴，x 轴保持不变

---

### 6. TTS 音频结束 (tts_end)

TTS 语音合成完成，所有音频数据已发送完毕。

```json
{"type": "tts_end", "code": 0, "data": "ok"}
```

---

### 7. TTS 音频数据 (二进制)

TTS 合成的音频数据，直接发送二进制内容（PCM 格式）。

- **消息类型**：二进制（非 JSON）
- **数据格式**：PCM 音频
- **采样率**：24000 Hz

---

### 8. OpenClaw 实时日志 (openclaw_log)

OpenClaw 执行过程中的实时日志输出（仅 TMUX 方式支持）。

```json
{
  "type": "openclaw_log",
  "code": 0,
  "data": {
    "content": "Waiting for agent reply...",
    "status": "thinking"
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| content | string | 日志内容 |
| status | string | 当前执行状态 (thinking/processing) |

**示例场景**：
- 思考中：`{"type": "openclaw_log", "data": {"content": "◐  Waiting for agent reply…", "status": "thinking"}}`
- 处理中：`{"type": "openclaw_log", "data": {"content": "Loading project context...", "status": "processing"}}`

---

## 客户端 → 服务端消息

### 1. 语音音频数据

客户端发送的 PCM 音频流数据。

- **消息类型**：二进制
- **采样率**：16000 Hz
- **声道**：单声道

---

### 2. 结束标记 (over)

客户端发送结束标记，表示音频数据已发送完毕，等待识别结果。

```json
"over"
```

---

### 3. 舵机动画控制 (servo)

控制舵机动画的播放（循环模式）。

```json
{"type": "servo", "action": "start", "state": "speech_nod"}
```

或

```json
{"type": "servo", "action": "stop"}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| action | string | 操作类型：`start` 播放动画，`stop` 停止动画 |
| state | string | 动画状态名，对应 JSON 文件名（不含扩展名） |

---

### 4. 舵机动画播放 (state)

触发舵机动画的独占播放（一次性播放，不循环，不可中断）。

```json
{"type": "state", "data": "speech_nod"}
```

**说明**：
- 播放一次完整的动画数据
- 优先级高于循环播放，会中断当前循环播放
- 播放过程中不可停止
- x 和 y 按各自的时间轴分别发送

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定为 `state` |
| data | string | 动画状态名，对应 JSON 文件名（不含扩展名） |

---

## 消息流程示例

### 完整语音对话流程

```
客户端 → 服务端：发送音频数据（二进制）
客户端 → 服务端：发送 "over" 标记
服务端 → 客户端：{"type": "asr_result", "code": 0, "data": "今天天气怎么样"}
服务端 → 客户端：{"type": "bot_reply", "code": 0, "data": "今天天气晴朗..."}
服务端 → 客户端：发送 TTS 音频（二进制）
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"x": 95}}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"y": 90}}
...
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"x": 100}}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"y": 90}}
服务端 → 客户端：{"type": "tts_end", "code": 0, "data": "ok"}
```

### 舵机动画控制流程（循环播放）

```
客户端 → 服务端：{"type": "servo", "action": "start", "state": "speech_nod"}
服务端 → 客户端：{"type": "status", "code": 0, "data": "舵机动画开始: speech_nod"}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"x": 95}}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"y": 90}}
...
（循环播放动画）

客户端 → 服务端：{"type": "servo", "action": "stop"}
服务端 → 客户端：{"type": "status", "code": 0, "data": "舵机动画已停止"}
```

### 舵机动画播放流程（独占播放）

```
客户端 → 服务端：{"type": "state", "data": "speech_nod"}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"x": 10}}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"y": 150}}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"x": 38}}
服务端 → 客户端：{"type": "servo", "code": 0, "data": {"y": 184}}
...
（播放完成后自动停止）
```

---

## 客户端实现示例

### JavaScript 接收舵机数据

```javascript
// 维护当前舵机状态
let currentX = 0;
let currentY = 0;

ws.onmessage = (event) => {
    if (typeof event.data === 'string') {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'servo') {
                // 分别处理 x 和 y
                if (msg.data.x !== undefined && msg.data.x !== null) {
                    currentX = msg.data.x;
                    console.log(`更新 X 轴: ${currentX}`);
                    // TODO: 执行实际的舵机控制
                }
                if (msg.data.y !== undefined && msg.data.y !== null) {
                    currentY = msg.data.y;
                    console.log(`更新 Y 轴: ${currentY}`);
                    // TODO: 执行实际的舵机控制
                }
            }
        } catch (e) {
            console.error('解析消息失败:', e);
        }
    }
};
```

### 发送舵机动画请求

```javascript
// 循环播放
ws.send(JSON.stringify({
    type: 'servo',
    action: 'start',
    state: 'speech_nod'
}));

// 独占播放（一次性）
ws.send(JSON.stringify({
    type: 'state',
    data: 'speech_nod'
}));
```