[English](openclaw_tmux_design.md) | [中文](openclaw_tmux_design_CN.md)

# OpenClaw TMUX 支持架构设计

> **创建日期**: 2026-03-05
> **目的**: 支持 tmux 方式连接 OpenClaw，获取实时日志

## 1. 需求概述

### 1.1 目标

- 自动检测系统是否支持 tmux
- 有 tmux：使用 tmux 方式（获得实时日志 + 执行状态）
- 无 tmux：使用 CLI 方式（仅获得执行状态）
- 实时日志通过 WebSocket 发送给客户端

### 1.2 对比

| 功能 | CLI 方式 | TMUX 方式 |
|------|----------|-----------|
| 执行状态 (thinking/processing) | ✅ | ✅ |
| 实时日志 | ❌ | ✅ |
| 跨平台兼容 | ✅ (所有系统) | ❌ (仅 Unix-like) |

---

## 2. 架构设计

### 2.1 文件结构

```
src/modules/openclaw/
├── __init__.py                 # 导出工厂函数
├── base.py                     # OpenClawProvider 抽象基类
├── local_claw.py               # LocalOpenClawProvider (CLI 方式)
└── tmux_claw.py               # TmuxOpenClawProvider (TMUX 方式) [新增]
```

### 2.2 类图

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
│  (CLI 方式)         │              │   (TMUX 方式)          │
├─────────────────────┤              ├─────────────────────────┤
│ - poll_interval     │              │ - session_name         │
│ - on_status_change │              │ - on_status_change     │
│ - on_log           │◄─────────────│ - on_log               │
├─────────────────────┤  (新增)     │ - _log_callback        │
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

### 2.3 消息类型扩展

在 `MessageHandler.MsgType` 中添加新类型：

```python
class MsgType:
    # ... 现有类型 ...
    OPENCLAW_LOG = "openclaw_log"   # OpenClaw 实时日志 [新增]
```

### 2.4 消息格式

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

## 3. 实现细节

### 3.1 tmux 检测

```python
import shutil

def is_tmux_available() -> bool:
    """检测系统是否支持 tmux"""
    return shutil.which("tmux") is not None
```

### 3.2 工厂函数

```python
# src/modules/openclaw/__init__.py

def create_openclaw_provider(
    agent: str = "main",
    poll_interval: int = 3,
    on_status_change: Callable = None,
    on_log: Callable = None,  # 新增：日志回调
) -> OpenClawProvider:
    """创建 OpenClaw 提供商实例

    自动检测并选择合适的实现：
    - 有 tmux: TmuxOpenClawProvider
    - 无 tmux: LocalOpenClawProvider
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

继承 `LocalOpenClawProvider` 并覆盖关键方法：

```python
class TmuxOpenClawProvider(LocalOpenClawProvider):
    """使用 tmux 的 OpenClaw 提供商"""

    SESSION_NAME = "openclaw_client"

    def __init__(self, on_log: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self.on_log = on_log
        self._log_callback = None

    def _ensure_session(self):
        """确保 tmux session 存在"""

    def _capture_pane(self) -> str:
        """捕获 tmux pane 内容"""

    async def _chat_with_status(self, message: str) -> dict:
        """带状态和日志的聊天"""
        # 1. 启动 tmux session 运行命令
        # 2. 轮询状态 (继承父类)
        # 3. 轮询日志 (新增)
        while True:
            # ... 状态轮询 ...

            # 新增：日志捕获
            log_content = self._capture_pane()
            if log_content and self.on_log:
                await self._call_log_callback(log_content)

            await asyncio.sleep(self.poll_interval)
```

### 3.4 回调机制

```python
async def _call_log_callback(self, content: str):
    """调用日志回调"""
    if self.on_log:
        try:
            if inspect.iscoroutinefunction(self.on_log):
                await self.on_log(content, self._current_status)
            else:
                self.on_log(content, self._current_status)
        except Exception as e:
            logger.warning(f"日志回调失败: {e}")
```

---

## 4. 使用示例

### 4.1 WebSocket 服务中使用

```python
# websocket_server.py

async def _call_ai(self, text: str) -> Optional[str]:
    from src.modules.openclaw import create_openclaw_provider

    # 状态回调
    async def on_status_change(status: str, data: dict):
        await self.msg_handler.send_info(f"[{status}] {data.get('message', '')}")

    # 日志回调 (TMUX 方式特有)
    async def on_log(content: str, status: str):
        await self.msg_handler.send_openclaw_log(content, status)

    # 自动选择实现
    openclaw = create_openclaw_provider(
        agent="main",
        on_status_change=on_status_change,
        on_log=on_log,  # TMUX 方式会使用
    )

    await openclaw.initialize()
    # ... 后续逻辑不变 ...
```

### 4.2 客户端接收处理

```javascript
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    switch (msg.type) {
        case 'status':
            // 执行状态: thinking, processing, completed
            console.log('状态:', msg.data);
            break;

        case 'openclaw_log':
            // 实时日志
            console.log('日志:', msg.data.content);
            console.log('关联状态:', msg.data.status);
            break;

        case 'bot_reply':
            // 最终回复
            console.log('回复:', msg.data);
            break;
    }
};
```

---

## 5. 配置

### 5.1 环境变量

```bash
# OpenClaw 配置
OPENCLAW_AGENT=main                     # Agent ID
OPENCLAW_STATUS_POLL_INTERVAL=3         # 状态轮询间隔（秒）
OPENCLAW_LOG_POLL_INTERVAL=2             # 日志轮询间隔（秒）[新增]
OPENCLAW_PROMPT_FILE=config/openclaw_prompt.txt
```

---

## 6. 错误处理

| 场景 | 处理 |
|------|------|
| tmux 命令不存在 | 回退到 CLI 方式 |
| tmux session 创建失败 | 回退到 CLI 方式 |
| 日志捕获失败 | 仅记录日志，不中断执行 |

---

## 7. 待实现文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/modules/openclaw/tmux_claw.py` | 新增 | TmuxOpenClawProvider 实现 |
| `src/modules/openclaw/__init__.py` | 修改 | 添加工厂函数和导出 |
| `src/utils/message_handler.py` | 修改 | 添加 `send_openclaw_log` 方法 |
| `docs/websocket_message_protocol.md` | 修改 | 添加新消息类型说明 |
| `docs/context/openclaw_context.md` | 修改 | 更新架构文档 |

---

## 8. 注意事项

1. **tmux session 管理**：每个客户端请求创建独立的 tmux session，避免冲突
2. **日志去重**：由于轮询捕获，可能重复发送相同日志，需要在回调层去重
3. **状态关联**：日志应关联当前执行状态 (thinking/processing)
4. **清理机制**：请求完成后必须清理 tmux session
