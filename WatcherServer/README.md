[English](README.md) | [中文](README_CN.md)

# Watcher Server

WebSocket Voice Dialogue Server

## Quick Start

```bash
# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
python main.py
```

## Features

- Receive audio binary data from clients
- Real-time speech recognition (ASR)
- Dialog with OpenClaw
- Speech synthesis (TTS) return to client
- Complete thread management and logging system

## Quick Start

### 1. Environment Requirements

- Python 3.10+
- Conda/Miniconda

### 2. Create Conda Environment

```bash
# Create environment from environment.yml (recommended)
conda env create -f environment.yml

# Or create manually
conda create -n watcher-server python=3.10
conda activate watcher-server
```

### 3. Activate Environment

```bash
conda activate watcher-server
```

### 4. Install Dependencies

If you used `environment.yml` to create the environment, dependencies are already installed.

If you created the environment manually, install dependencies:

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
# Copy config template
cp .env.example .env

# Edit .env file with your actual configuration
# notepad .env  # Windows
# vim .env      # Linux/Mac
```

Main configuration items:
```bash
# Aliyun ASR Configuration
ALIYUN_AK_ID=           # Your AccessKey ID
ALIYUN_AK_SECRET=     # Your AccessKey SECRET
ALIYUN_APPKEY=  # Aliyun AppKey (obtained from console)
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1  # Gateway URL
# Get AppKey: https://nls-portal.console.aliyun.com/applist
# Get AccessKey: https://ram.console.aliyun.com/profile/access-keys


# Huoshan TTS Configuration https://console.volcengine.com/speech/app
HUOSHAN_APP_KEY=     # Huoshan Speech Synthesis Project App ID
HUOSHAN_ACCESS_KEY=  # Huoshan Speech Synthesis Project Access Token
HUOSHAN_VOICE_TYPE=ICL_zh_male_nuanxintitie_tob  # Voice type


```

### 6. Start the Server

Make sure the openclaw gateway service is running before starting.

```bash
# Ensure environment is activated
conda activate watcher-server

# Start the server
python main.py
```

After successful startup, you will see:
```
2026-02-28 10:00:00 | INFO     | __main__:initialize:15 - Starting Watcher Server initialization...
2026-02-28 10:00:00 | INFO     | __main__:initialize:42 - Watcher Server initialization complete
2026-02-28 10:00:00 | INFO     | __main__:start:46 - Starting Watcher Server...
2026-02-28 10:00:00 | INFO     | websocket_server:start:95 - Starting WebSocket server: ws://0.0.0.0:8765
2026-02-28 10:00:00 | INFO     | websocket_server:start:99 - WebSocket server started successfully
```

### 7. Stop the Server

Press `Ctrl+C` to gracefully stop the server

## Common Commands

```bash
# Activate environment
conda activate watcher-server

# Deactivate environment
conda deactivate

# List installed packages
conda list

# Update environment (after modifying environment.yml)
conda env update -f environment.yml --prune

# Remove environment
conda env remove -n watcher-server

# Export current environment
conda env export > environment.yml
```

## Project Structure

```
watcher_server/
├── src/
│   ├── main.py              # Server entry point
│   ├── config/              # Configuration module
│   ├── core/                # Core modules (WebSocket, thread pool)
│   ├── modules/             # Business modules (ASR, OpenClaw, TTS)
│   ├── utils/               # Utilities (logging, etc.)
│   └── models/              # Data models
├── tests/                   # Test directory
├── logs/                    # Log output directory
└── requirements.txt         # Dependencies file
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure the relevant parameters

```bash
cp .env.example .env
```

Then edit the `.env` file with your actual configuration.

## Run

```bash
python main.py
```

## Dependencies

- **websockets**: WebSocket server
- **pydantic-settings**: Configuration management (supports loading from .env file)
- **loguru**: Logging system
- **alibabacloud-nls-python-sdk**: Aliyun speech recognition SDK
- **httpx**: Async HTTP client
- **aiohttp**: Async HTTP client (backup)
