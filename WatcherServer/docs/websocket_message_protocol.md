[English](websocket_message_protocol.md) | [中文](websocket_message_protocol_CN.md)

# WebSocket Message Protocol Documentation

## Message Format

All messages use unified JSON format:

```json
{
  "type": "message type",
  "code": 0,
  "data": "message data"
}
```

### Field Description

| Field | Type | Description |
|-------|------|-------------|
| type | string | Message type |
| code | int | Error code, `0` means success, `1` means error |
| data | any | Message data |

---

## Server → Client Messages

### 1. ASR Recognition Result (asr_result)

Text result after speech recognition completes.

```json
{"type": "asr_result", "code": 0, "data": "recognized text content"}
```

---

### 2. Bot Reply (bot_reply)

Reply text returned by AI dialogue.

```json
{"type": "bot_reply", "code": 0, "data": "AI reply content"}
```

---

### 3. Status Message (status)

System status change notification, such as OpenClaw thinking status, servo animation status, etc.

```json
{"type": "status", "code": 0, "data": "status description"}
```

**Example Scenarios**:
- OpenClaw thinking: `[thinking] Thinking...`
- Servo animation started: `Servo animation started: speech_nod`

---

### 4. Error Message (error)

System error or exception information.

```json
{"type": "error", "code": 1, "data": "error description"}
```

---

### 5. Servo Control (servo)

Real-time servo angle data for controlling robot movements.

**Important**: x and y may be sent separately (independent timelines).

#### Send x-axis data

```json
{"type": "servo", "code": 0, "data": {"x": 90}}
```

#### Send y-axis data

```json
{"type": "servo", "code": 0, "data": {"y": 45}}
```

#### Send x and y together (as two separate messages)

```json
{"type": "servo", "code": 0, "data": {"x": 90}}
{"type": "servo", "code": 0, "data": {"y": 45}}
```

**Field Description**:

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| x | int | 0-180 | X-axis angle, controls left/right (can be null) |
| y | int | 0-180 | Y-axis angle, controls up/down (can be null) |

**Client Receive Handling Suggestions**:
- Client should handle x and y data separately
- When receiving x data, only update x-axis, keep y-axis unchanged
- When receiving y data, only update y-axis, keep x-axis unchanged

---

### 6. TTS Audio End (tts_end)

TTS speech synthesis completed, all audio data has been sent.

```json
{"type": "tts_end", "code": 0, "data": "ok"}
```

---

### 7. TTS Audio Data (Binary)

Synthesized audio data from TTS, directly sent as binary content (PCM format).

- **Message Type**: Binary (not JSON)
- **Data Format**: PCM audio
- **Sample Rate**: 24000 Hz

---

### 8. OpenClaw Real-time Logs (openclaw_log)

Real-time log output during OpenClaw execution (only supported in TMUX mode).

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

**Field Description**:

| Field | Type | Description |
|-------|------|-------------|
| content | string | Log content |
| status | string | Current execution status (thinking/processing) |

**Example Scenarios**:
- Thinking: `{"type": "openclaw_log", "data": {"content": "◐  Waiting for agent reply…", "status": "thinking"}}`
- Processing: `{"type": "openclaw_log", "data": {"content": "Loading project context...", "status": "processing"}}`

---

## Client → Server Messages

### 1. Voice Audio Data

PCM audio stream data sent by client.

- **Message Type**: Binary
- **Sample Rate**: 16000 Hz
- **Channel**: Mono

---

### 2. End Marker (over)

End marker sent by client, indicates audio data has been sent and waiting for recognition result.

```json
"over"
```

---

### 3. Servo Animation Control (servo)

Control servo animation playback (loop mode).

```json
{"type": "servo", "action": "start", "state": "speech_nod"}
```

or

```json
{"type": "servo", "action": "stop"}
```

**Field Description**:

| Field | Type | Description |
|-------|------|-------------|
| action | string | Operation type: `start` to play animation, `stop` to stop animation |
| state | string | Animation state name, corresponds to JSON file name (without extension) |

---

### 4. Servo Animation Playback (state)

Trigger exclusive playback of servo animation (one-time playback, no loop, uninterruptible).

```json
{"type": "state", "data": "speech_nod"}
```

**Description**:
- Play complete animation data once
- Higher priority than loop playback, will interrupt current loop playback
- Cannot be stopped during playback
- x and y are sent separately on their respective timelines

**Field Description**:

| Field | Type | Description |
|-------|------|-------------|
| type | string | Fixed as `state` |
| data | string | Animation state name, corresponds to JSON file name (without extension) |

---

## Message Flow Examples

### Complete Voice Dialogue Flow

```
Client → Server: Send audio data (binary)
Client → Server: Send "over" marker
Server → Client: {"type": "asr_result", "code": 0, "data": "How is the weather today"}
Server → Client: {"type": "bot_reply", "code": 0, "data": "The weather is sunny today..."}
Server → Client: Send TTS audio (binary)
Server → Client: {"type": "servo", "code": 0, "data": {"x": 95}}
Server → Client: {"type": "servo", "code": 0, "data": {"y": 90}}
...
Server → Client: {"type": "servo", "code": 0, "data": {"x": 100}}
Server → Client: {"type": "servo", "code": 0, "data": {"y": 90}}
Server → Client: {"type": "tts_end", "code": 0, "data": "ok"}
```

### Servo Animation Control Flow (Loop Playback)

```
Client → Server: {"type": "servo", "action": "start", "state": "speech_nod"}
Server → Client: {"type": "status", "code": 0, "data": "Servo animation started: speech_nod"}
Server → Client: {"type": "servo", "code": 0, "data": {"x": 95}}
Server → Client: {"type": "servo", "code": 0, "data": {"y": 90}}
...
(Loop playback animation)

Client → Server: {"type": "servo", "action": "stop"}
Server → Client: {"type": "status", "code": 0, "data": "Servo animation stopped"}
```

### Servo Animation Playback Flow (Exclusive Playback)

```
Client → Server: {"type": "state", "data": "speech_nod"}
Server → Client: {"type": "servo", "code": 0, "data": {"x": 10}}
Server → Client: {"type": "servo", "code": 0, "data": {"y": 150}}
Server → Client: {"type": "servo", "code": 0, "data": {"x": 38}}
Server → Client: {"type": "servo", "code": 0, "data": {"y": 184}}
...
(Automatically stops after playback completes)
```

---

## Client Implementation Examples

### JavaScript Receive Servo Data

```javascript
// Maintain current servo state
let currentX = 0;
let currentY = 0;

ws.onmessage = (event) => {
    if (typeof event.data === 'string') {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'servo') {
                // Handle x and y separately
                if (msg.data.x !== undefined && msg.data.x !== null) {
                    currentX = msg.data.x;
                    console.log(`Update X axis: ${currentX}`);
                    // TODO: Execute actual servo control
                }
                if (msg.data.y !== undefined && msg.data.y !== null) {
                    currentY = msg.data.y;
                    console.log(`Update Y axis: ${currentY}`);
                    // TODO: Execute actual servo control
                }
            }
        } catch (e) {
            console.error('Failed to parse message:', e);
        }
    }
};
```

### Send Servo Animation Request

```javascript
// Loop playback
ws.send(JSON.stringify({
    type: 'servo',
    action: 'start',
    state: 'speech_nod'
}));

// Exclusive playback (one-time)
ws.send(JSON.stringify({
    type: 'state',
    data: 'speech_nod'
}));
