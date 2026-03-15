[English](openclaw_tmux_design.md) | [中文](openclaw_tmux_design_CN.md)

# OpenClaw TMUX Support Architecture Design

> **Created**: 2026-03-05
> **Purpose**: Support tmux mode to connect to OpenClaw, get real-time logs

## 1. Requirements Overview

### 1.1 Goals

- Automatically detect if system supports tmux
- Has tmux: Use tmux method (get real-time logs + execution status)
- No tmux: Use CLI method (get execution status only)
- Real-time logs sent to client via WebSocket

### 1.2 Comparison

| Feature | CLI Mode | TMUX Mode |
|---------|----------|-----------|
| Execution Status (thinking/processing) | ✅ | ✅ |
| Real-time Logs | ❌ | ✅ |
| Cross-platform Compatibility | ✅ (All systems) | ❌ (Unix-like only) |

---

## 2. Architecture Design

### 2.1 File Structure

```
src/modules/openclaw/
├── __init__.py                 # Export factory function
├── base.py                     # OpenClawProvider abstract base class
├── local_claw.py               # LocalOpenClawProvider (CLI mode)
└── tmux_claw.py               # TmuxOpenClawProvider (TMUX mode) [NEW]
```

### 2.2 Class Diagram

```
                    ┌─────────────────────────┐
                    │   OpenClawProvider      │
                    │      (ABC)              │
                    ├─────────────────────────┤
                    │ + initialize()          │
                    │ + chat()                │
                    │ + cleanup()             │
                    └───────────┬─────────────┘
                                │
           ┌────────────────────┴────────────────────┐
           │                                         │
           ▼                                         ▼
┌─────────────────────┐              ┌─────────────────────────┐
│LocalOpenClawProvider│              │ TmuxOpenClawProvider    │
│  (CLI mode)        │              │   (TMUX mode)          │
├─────────────────────┤              ├─────────────────────────┤
│ - poll_interval     │              │ - session_name         │
│ - on_status_change │              │ - on_status_change     │
│ - on_log           │◄─────────────│ - on_log               │
├─────────────────────┤  (NEW)     │ - _log_callback        │
│ + _get_session_    │              ├─────────────────────────┤
│   status()         │              │ + _capture_pane()      │
└─────────────────────┘              │ + _poll_log()          │
                                     └───────────┬─────────────┘
                                                 │
                                     ┌───────────┴─────────────┐
                                     │                         │
                                     ▼                         ▼
                            ┌──────────────┐      ┌─────────────────┐
                            │LocalOpenClaw │      │TmuxOpenClawProvider│
                            │Provider      │      │                  │
                            └──────────────┘      └─────────────────┘
```

### 2.3 Message Type Extension

Add new type in `MessageHandler.MsgType`:

```python
class MsgType:
    # ... existing types ...
    OPENCLAW_LOG = "openclaw_log"   # OpenClaw real-time logs [NEW]
```

### 2.4 Message Format

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

---

## 3. Implementation Details

### 3.1 Tmux Detection

```python
import shutil

def is_tmux_available() -> bool:
    """Check if system supports tmux"""
    return shutil.which("tmux") is not None
```

### 3.2 Factory Function

```python
# src/modules/openclaw/__init__.py

def create_openclaw_provider(
    agent: str = "main",
    poll_interval: int = 3,
    on_status_change: Callable = None,
    on_log: Callable = None,  # NEW: log callback
) -> OpenClawProvider:
    """Create OpenClaw provider instance

    Automatically detect and select appropriate implementation:
    - Has tmux: TmuxOpenClawProvider
    - No tmux: LocalOpenClawProvider
    """
    if is_tmux_available():
        return TmuxOpenClawProvider(
            agent=agent,
            poll_interval=poll_interval,
            on_status_change=on_status_change,
            on_log=on_log,
        )
    else:
        return LocalOpenClawProvider(
            agent=agent,
            poll_interval=poll_interval,
            on_status_change=on_status_change,
        )
```

### 3.3 TmuxOpenClawProvider

Inherit from `LocalOpenClawProvider` and override key methods:

```python
class TmuxOpenClawProvider(LocalOpenClawProvider):
    """OpenClaw provider using tmux"""

    SESSION_NAME = "openclaw_client"

    def __init__(self, on_log: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self.on_log = on_log
        self._log_callback = None

    def _ensure_session(self):
        """Ensure tmux session exists"""

    def _capture_pane(self) -> str:
        """Capture tmux pane content"""

    async def _chat_with_status(self, message: str) -> dict:
        """Chat with status and logs"""
        # 1. Start tmux session and run command
        # 2. Poll status (inherited from parent)
        # 3. Poll logs (NEW)
        while True:
            # ... status polling ...

            # NEW: Log capture
            log_content = self._capture_pane()
            if log_content and self.on_log:
                await self._call_log_callback(log_content)

            await asyncio.sleep(self.poll_interval)
```

### 3.4 Callback Mechanism

```python
async def _call_log_callback(self, content: str):
    """Call log callback"""
    if self.on_log:
        try:
            if inspect.iscoroutinefunction(self.on_log):
                await self.on_log(content, self._current_status)
            else:
                self.on_log(content, self._current_status)
        except Exception as e:
            logger.warning(f"Log callback failed: {e}")
```

---

## 4. Usage Examples

### 4.1 Using in WebSocket Service

```python
# websocket_server.py

async def _call_ai(self, text: str) -> Optional[str]:
    from src.modules.openclaw import create_openclaw_provider

    # Status callback
    async def on_status_change(status: str, data: dict):
        await self.msg_handler.send_info(f"[{status}] {data.get('message', '')}")

    # Log callback (TMUX mode specific)
    async def on_log(content: str, status: str):
        await self.msg_handler.send_openclaw_log(content, status)

    # Auto-select implementation
    openclaw = create_openclaw_provider(
        agent="main",
        on_status_change=on_status_change,
        on_log=on_log,  # Used in TMUX mode
    )

    await openclaw.initialize()
    # ... subsequent logic unchanged ...
```

### 4.2 Client Receive Handling

```javascript
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    switch (msg.type) {
        case 'status':
            // Execution status: thinking, processing, completed
            console.log('Status:', msg.data);
            break;

        case 'openclaw_log':
            // Real-time logs
            console.log('Log:', msg.data.content);
            console.log('Associated status:', msg.data.status);
            break;

        case 'bot_reply':
            // Final reply
            console.log('Reply:', msg.data);
            break;
    }
};
```

---

## 5. Configuration

### 5.1 Environment Variables

```bash
# OpenClaw Configuration
OPENCLAW_AGENT=main                     # Agent ID
OPENCLAW_STATUS_POLL_INTERVAL=3         # Status polling interval (seconds)
OPENCLAW_LOG_POLL_INTERVAL=2             # Log polling interval (seconds) [NEW]
OPENCLAW_PROMPT_FILE=config/openclaw_prompt.txt
```

---

## 6. Error Handling

| Scenario | Handling |
|---------|---------|
| tmux command not found | Fallback to CLI mode |
| tmux session creation failed | Fallback to CLI mode |
| Log capture failed | Log only, don't interrupt execution |

---

## 7. Files to Implement

| File | Action | Description |
|------|--------|-------------|
| `src/modules/openclaw/tmux_claw.py` | NEW | TmuxOpenClawProvider implementation |
| `src/modules/openclaw/__init__.py` | MODIFY | Add factory function and exports |
| `src/utils/message_handler.py` | MODIFY | Add `send_openclaw_log` method |
| `docs/websocket_message_protocol.md` | MODIFY | Add new message type documentation |
| `docs/context/openclaw_context.md` | MODIFY | Update architecture documentation |

---

## 8. Notes

1. **tmux session management**: Each client request creates independent tmux session to avoid conflicts
2. **Log deduplication**: Since polling captures may send duplicate logs, need deduplication at callback layer
3. **Status association**: Logs should be associated with current execution status (thinking/processing)
4. **Cleanup mechanism**: Must cleanup tmux session after request completes
