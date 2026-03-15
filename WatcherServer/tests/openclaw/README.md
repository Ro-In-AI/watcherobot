# OpenClaw 本地接入调研

## 概述

OpenClaw 是一个本地运行的 AI 网关服务，支持多种模型（GLM、Claude 等）。本项目已在 `127.0.0.1:18789` 启动。

## 本地环境

| 配置项 | 值 |
|--------|-----|
| WebSocket 地址 | `ws://127.0.0.1:18789` |
| Token | `c8a603498d06f46f871e6971f184f296e5046c8568bed5ab` |
| 已配置模型 | `zai/glm-4.7`, `zai/glm-5` |
| 默认 Agent | `main` |

## 接入方式

### 方式一：CLI 命令（最简单）

```bash
openclaw agent --agent main --message "你好" --json
```

**参数说明：**
- `--agent`: Agent ID（默认 `main`）
- `--message`: 发送的消息
- `--json`: 输出 JSON 格式

**返回格式：**
```json
{
  "runId": "xxx",
  "status": "ok",
  "summary": "completed",
  "result": {
    "payloads": [
      {
        "text": "AI 回复内容",
        "mediaUrl": null
      }
    ],
    "meta": {
      "durationMs": 17188,
      "agentMeta": {
        "provider": "zai",
        "model": "glm-4.7",
        "usage": {
          "input": 121464,
          "output": 433,
          "total": 128829
        }
      }
    }
  }
}
```

### 方式二：Python 调用 CLI

在 Python 中通过子进程调用 CLI：

```python
import asyncio
import json

async def chat(message: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "openclaw", "agent", "--agent", "main",
        "--message", message, "--json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    result = json.loads(stdout)
    return result["result"]["payloads"][0]["text"]
```

### 方式三：WebSocket API（高级）

连接到 `ws://127.0.0.1:18789` 进行更复杂的交互。

## 项目集成

### 配置项（.env）

```bash
OPENCLAW_API_URL=ws://127.0.0.1:18789
OPENCLAW_TOKEN=c8a603498d06f46f871e6971f184f296e5046c8568bed5ab
OPENCLAW_AGENT=main
```

### 实现建议

1. **简单方案**：使用 `asyncio.subprocess` 调用 CLI 命令
2. **完整方案**：实现 WebSocket 客户端连接网关

## 测试命令

```bash
# 测试 CLI
openclaw agent --agent main --message "你好" --json

# 查看网关状态
openclaw gateway status

# 查看健康状态
openclaw gateway call health --json
```
