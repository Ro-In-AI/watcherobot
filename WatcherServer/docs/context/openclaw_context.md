# OpenClaw 模块上下文

> **最后更新**: 2026-03-05
> **主要实现**: LocalOpenClawProvider + TmuxOpenClawProvider (自动选择)

## 模块概述

OpenClaw 模块负责与 AI 对话服务通信，获取 AI 回复。支持两种连接方式：
- **CLI 方式**：通过命令行调用 OpenClaw Gateway
- **TMUX 方式**：通过 tmux 运行命令，获取实时日志

## 文件结构

```
src/modules/openclaw/
├── __init__.py              # 工厂函数和导出
├── base.py                  # OpenClawProvider 抽象基类
├── local_claw.py            # LocalOpenClawProvider (CLI 方式)
└── tmux_claw.py            # TmuxOpenClawProvider (TMUX 方式)
```

## 连接方式对比

| 功能 | CLI 方式 | TMUX 方式 |
|------|----------|-----------|
| 执行状态 (thinking/processing) | ✅ | ✅ |
| 实时日志 | ❌ | ✅ |
| 跨平台兼容 | ✅ (所有系统) | ❌ (仅 Unix-like) |

## 工厂函数

推荐使用 `create_openclaw_provider()` 自动选择合适的实现：

```python
from src.modules.openclaw import create_openclaw_provider, is_tmux_available

# 检测 tmux 是否可用
print(is_tmux_available())  # True/False

# 创建实例（自动选择）
provider = create_openclaw_provider(
    agent="main",
    poll_interval=3,
    log_poll_interval=2,  # 仅 TMUX 方式有效
    prefer_tmux=True,      # 是否优先使用 tmux
    on_status_change=callback,
    on_log=log_callback,  # 仅 TMUX 方式有效
)
```

## 核心类

### OpenClawProvider (抽象基类)

**文件**: [src/modules/openclaw/base.py](../../src/modules/openclaw/base.py)

定义了 OpenClaw 提供商的统一接口：

```python
class OpenClawProvider(ABC):
    @abstractmethod
    async def initialize(self): ...

    @abstractmethod
    async def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse: ...

    @abstractmethod
    async def cleanup(self): ...
```

### 数据模型

```python
class ChatMessage(TypedDict):
    role: str      # "system", "user", "assistant"
    content: str   # 消息内容

class ChatResponse(TypedDict):
    content: str           # 回复内容
    model: str             # 使用的模型
    finish_reason: str     # 结束原因
    usage: dict            # Token 使用情况
```

### LocalOpenClawProvider

**文件**: [src/modules/openclaw/local_claw.py](../../src/modules/openclaw/local_claw.py)

#### 初始化参数

```python
LocalOpenClawProvider(
    agent: str = "main",                      # Agent ID
    poll_interval: int = 3,                   # 状态轮询间隔（秒）
    on_status_change: Callable = None         # 状态变化回调
)
```

#### 状态类型

```python
class Status:
    IDLE = "idle"             # 空闲
    THINKING = "thinking"     # 思考中
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed"   # 完成
    ERROR = "error"          # 错误
```

#### 工作流程

```
1. initialize()           → 检查 CLI 和 Gateway 可用性
2. chat(messages)         → 发送聊天请求
3. _chat_with_status()    → 轮询状态并获取结果
4. cleanup()              → 清理资源
```

#### 关键实现细节

**CLI 可用性检查**：

```python
async def initialize(self):
    # 检查 CLI
    proc = await asyncio.create_subprocess_exec("openclaw", "--version", ...)
    if proc.returncode != 0:
        raise RuntimeError("OpenClaw CLI 不可用")

    # 检查 Gateway 状态
    proc = await asyncio.create_subprocess_exec("openclaw", "gateway", "status", ...)
    if "running" not in output.lower():
        raise RuntimeError("OpenClaw Gateway 未运行")
```

**聊天请求**：

通过 `openclaw agent` 命令发送请求：

```bash
openclaw agent \
    --agent main \
    --message "用户消息" \
    --json
```

**状态轮询机制**：

在等待响应时，定期查询 Session 状态：

```python
while True:
    # 查询状态
    status = await self._get_session_status()

    # 根据 age 判断状态
    if age < 5000:
        current_status = Status.THINKING
    else:
        current_status = Status.PROCESSING

    # 状态变化时发送回调
    if current_status != last_status:
        await self._call_status_callback(current_status, {...})

    await asyncio.sleep(self.poll_interval)

    # 检查进程是否完成
    if proc.returncode is not None:
        break
```

**状态回调**：

支持同步和异步回调函数：

```python
async def _call_status_callback(self, status: str, data: dict):
    if self.on_status_change:
        if inspect.iscoroutinefunction(self.on_status_change):
            await self.on_status_change(status, data)
        else:
            self.on_status_change(status, data)
```

**响应解析**：

```python
result = json.loads(stdout)

if result.get("status") == "ok":
    payloads = result.get("result", {}).get("payloads", [])
    content = payloads[0].get("text", "")

    # model 在 agentMeta 里面
    agent_meta = result.get("result", {}).get("meta", {}).get("agentMeta", {})
    usage = agent_meta.get("usage", {})
    model = agent_meta.get("model", "")
```

## 配置

### 环境变量

```bash
# OpenClaw 配置（本地 CLI 模式）
OPENCLAW_AGENT=main                     # Agent ID
OPENCLAW_STATUS_POLL_INTERVAL=3         # 状态轮询间隔（秒）
OPENCLAW_PROMPT_FILE=config/openclaw_prompt.txt  # 提示词文件
```

### 提示词配置

提示词存储在 `config/openclaw_prompt.txt`：

```
TTS_PROMPT=请用简洁的纯文本回复，不要使用 Markdown 格式（如 #、**、*、` 等符号），不要使用列表，直接用自然段落回复。回复内容将用于语音合成。
```

提示词会自动加载并作为 system 消息发送：

```python
# websocket_server.py
tts_prompt = settings.get_openclaw_prompt()
response = await openclaw_client.chat([
    ChatMessage(role="system", content=tts_prompt),
    ChatMessage(role="user", content=recognized_text)
])
```

## 使用示例

### 基本使用

```python
from src.modules.openclaw.local_claw import LocalOpenClawProvider
from src.modules.openclaw.base import ChatMessage

# 创建 OpenClaw 实例
async def on_status_change(status: str, data: dict):
    print(f"状态: {status}, 数据: {data}")

openclaw = LocalOpenClawProvider(
    agent="main",
    poll_interval=3,
    on_status_change=on_status_change
)

# 初始化
await openclaw.initialize()

# 发送聊天请求
messages = [
    ChatMessage(role="system", content="你是一个助手"),
    ChatMessage(role="user", content="你好")
]
response = await openclaw.chat(messages)

print(f"回复: {response['content']}")
print(f"模型: {response['model']}")
print(f"Token 使用: {response['usage']}")

# 清理资源
await openclaw.cleanup()
```

### 在 WebSocket 服务中使用

```python
# websocket_server.py

# 创建状态回调
async def on_status_change(status: str, data: dict):
    await msg_handler.send_info(f"[{status}] {data.get('message', '')}")

# 创建 OpenClaw 客户端
openclaw_client = LocalOpenClawProvider(
    on_status_change=on_status_change
)
await openclaw_client.initialize()

# 加载提示词
tts_prompt = settings.get_openclaw_prompt()

# 发送聊天请求
response = await openclaw_client.chat([
    ChatMessage(role="system", content=tts_prompt),
    ChatMessage(role="user", content=recognized_text)
])

bot_reply_text = response['content']
```

## OpenClaw CLI 命令

### 常用命令

```bash
# 检查版本
openclaw --version

# Gateway 管理
openclaw gateway start    # 启动 Gateway
openclaw gateway status   # 查看状态
openclaw gateway stop     # 停止 Gateway

# 发送聊天请求
openclaw agent --agent main --message "你好"

# 获取 JSON 格式响应
openclaw agent --agent main --message "你好" --json

# 查看状态
openclaw gateway call status --json
```

### Session 状态响应

```json
{
  "sessions": {
    "recent": [
      {
        "id": "session_id",
        "age": 1234,           // 会话年龄（毫秒）
        "status": "running"
      }
    ]
  }
}
```

根据 `age` 判断状态：
- `age < 5000`: THINKING（思考中）
- `age >= 5000`: PROCESSING（处理中）

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| CLI 未安装 | openclaw 命令不存在 | 安装 OpenClaw CLI |
| Gateway 未运行 | Gateway 服务未启动 | `openclaw gateway start` |
| Agent 不存在 | 配置的 Agent ID 无效 | 检查 `OPENCLAW_AGENT` |
| 回调失败 | 回调函数抛出异常 | 检查回调函数实现 |

### 错误处理示例

```python
try:
    await openclaw.initialize()
except RuntimeError as e:
    if "未找到 openclaw 命令" in str(e):
        print("请先安装 OpenClaw CLI")
    elif "Gateway 未运行" in str(e):
        print("请先启动 Gateway: openclaw gateway start")
    raise
```

## 依赖

- OpenClaw CLI（外部工具）
- OpenClaw Gateway（外部服务）

## 最近修改记录

- **2026-03-04**: 添加状态变化回调支持（同步/异步）
- **2026-03-04**: 实现状态轮询机制
- **2026-03-04**: 添加提示词加载功能

---

**注意**: 修改此模块后，请更新本文档的"最近修改记录"部分。
