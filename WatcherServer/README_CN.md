[English](README.md) | [中文](README_CN.md)

# Watcher Server

WebSocket语音对话服务器

## 快速启动

```bash
# 创建虚拟环境（首次使用）
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖（首次使用）
pip install -r requirements.txt

# 启动服务
python main.py
```

## 功能描述

- 接收客户端音频二进制数据
- 实时语音识别（ASR）
- 调用OpenClaw进行对话
- 语音合成（TTS）返回客户端
- 完整的线程管理和日志系统

## 快速开始

### 1. 环境要求

- Python 3.10+
- Conda/Miniconda

### 2. 创建 Conda 环境

```bash
# 从 environment.yml 创建环境（推荐）
conda env create -f environment.yml

# 或手动创建环境
conda create -n watcher-server python=3.10
conda activate watcher-server
```

### 3. 激活环境

```bash
conda activate watcher-server
```

### 4. 安装依赖

如果使用 `environment.yml` 创建环境，依赖已自动安装。

如果手动创建环境，请安装依赖：

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入实际的配置信息
# notepad .env  # Windows
# vim .env      # Linux/Mac
```

主要配置项：
```bash
# 阿里云ASR配置
ALIYUN_AK_ID=           #用户的AccessKeyID
ALIYUN_AK_SECRET=     #用户的AccessKeySECRET
ALIYUN_APPKEY=  # 阿里云AppKey (从控制台获取)
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1  # 网关URL
# 获取AppKey: https://nls-portal.console.aliyun.com/applist
# 获取AccessKEY：https://ram.console.aliyun.com/profile/access-keys


# 火山引擎TTS配置https://console.volcengine.com/speech/app
HUOSHAN_APP_KEY=     # 火山引擎语音合成项目的App ID
HUOSHAN_ACCESS_KEY=  # 火山引擎语音合成项目Access Toekn
HUOSHAN_VOICE_TYPE=ICL_zh_male_nuanxintitie_tob  # 声音类型


```

### 6. 启动服务

为了使用正常，请确保运行环境中有openclaw getway服务已经在线

```bash
# 确保已激活环境
conda activate watcher-server

# 启动服务
python main.py
```

服务启动成功后，你会看到：
```
2026-02-28 10:00:00 | INFO     | __main__:initialize:15 - 开始初始化Watcher Server...
2026-02-28 10:00:00 | INFO     | __main__:initialize:42 - Watcher Server初始化完成
2026-02-28 10:00:00 | INFO     | __main__:start:46 - 启动Watcher Server...
2026-02-28 10:00:00 | INFO     | websocket_server:start:95 - 启动WebSocket服务器: ws://0.0.0.0:8765
2026-02-28 10:00:00 | INFO     | websocket_server:start:99 - WebSocket服务器启动成功
```

### 7. 停止服务

按 `Ctrl+C` 优雅停止服务

## 常用命令

```bash
# 激活环境
conda activate watcher-server

# 停用环境
conda deactivate

# 查看已安装的包
conda list

# 更新环境（修改environment.yml后）
conda env update -f environment.yml --prune

# 删除环境
conda env remove -n watcher-server

# 导出当前环境
conda env export > environment.yml
```

## 项目结构

```
watcher_server/
├── src/
│   ├── main.py              # 服务入口
│   ├── config/              # 配置模块
│   ├── core/                # 核心模块（WebSocket、线程池）
│   ├── modules/             # 业务模块（ASR、OpenClaw、TTS）
│   ├── utils/               # 工具模块（日志等）
│   └── models/              # 数据模型
├── tests/                   # 测试目录
├── logs/                    # 日志输出目录
└── requirements.txt         # 依赖文件
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env` 并配置相关参数

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，填入实际的配置信息。

## 运行

```bash
python main.py
```

## 依赖说明

- **websockets**: WebSocket服务器
- **pydantic-settings**: 配置管理（支持从.env文件加载配置）
- **loguru**: 日志系统
- **alibabacloud-nls-python-sdk**: 阿里云语音识别SDK
- **httpx**: 异步HTTP客户端
- **aiohttp**: 异步HTTP客户端（备用）
