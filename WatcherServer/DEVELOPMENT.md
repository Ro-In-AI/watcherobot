[English](DEVELOPMENT.md) | [中文](DEVELOPMENT_CN.md)

# Development Documentation

## Environment Management

This project uses Conda for environment management.

### Environment Information

- **Environment Name**: `watcher-server`
- **Python Version**: 3.10
- **Config File**: `environment.yml`

### Create Environment

```bash
# Method 1: Create from environment.yml (recommended)
conda env create -f environment.yml

# Method 2: Create manually and install dependencies
conda create -n watcher-server python=3.10
conda activate watcher-server
pip install -r requirements.txt
```

### Environment Management Commands

```bash
# Activate environment
conda activate watcher-server

# Deactivate environment
conda deactivate

# List environments
conda env list

# List packages in current environment
conda list

# Update environment (after modifying environment.yml)
conda env update -f environment.yml --prune

# Export current environment to environment.yml
conda env export > environment.yml

# Remove environment
conda env remove -n watcher-server
```

## Project Structure

```
Server/
├── src/
│   ├── main.py                    # Server entry point
│   ├── config/                    # Configuration module
│   │   └── env.py                 # Configuration management using Pydantic
│   ├── core/                      # Core modules
│   │   ├── websocket_server.py    # WebSocket server
│   │   └── thread_pool.py         # Thread pool management (singleton pattern)
│   ├── modules/                   # Business modules
│   │   ├── asr/                   # Speech recognition
│   │   │   └── base.py            # ASR abstract base class
│   │   ├── openclaw/              # AI dialogue
│   │   │   └── base.py            # OpenClaw abstract base class
│   │   └── tts/                   # Speech synthesis
│   │       └── base.py            # TTS abstract base class
│   ├── utils/                     # Utility modules
│   │   └── logger.py              # Logging system (loguru)
│   └── models/                    # Data models
├── tests/                         # Test directory
├── logs/                          # Log output
├── .env.example                   # Configuration template
├── environment.yml                # Conda environment configuration
├── requirements.txt               # Python dependencies
├── start.bat                      # Windows startup script
├── start.sh                       # Linux/Mac startup script
└── README.md                      # Project documentation
```

## Configuration

### Environment Variables (.env)

All configuration is managed via environment variables, loaded from the `.env` file:

```bash
# WebSocket configuration
WS_HOST=0.0.0.0              # Server address
WS_PORT=8765                 # Server port
WS_MAX_SIZE=10485760         # Maximum message size (10MB)

# ASR configuration
ASR_PROVIDER=aliyun          # ASR provider
ASR_SAMPLE_RATE=16000        # Sample rate
ASR_CHANNELS=1               # Number of channels

# OpenClaw configuration
OPENCLAW_API_KEY=xxx         # API key
OPENCLAW_API_URL=https://... # API URL
OPENCLAW_MODEL=gpt-4         # Model name

# TTS configuration
TTS_PROVIDER=aliyun          # TTS provider
TTS_SAMPLE_RATE=16000        # Sample rate
TTS_CHANNELS=1               # Number of channels

# Thread pool configuration
THREAD_POOL_MAX_WORKERS=10   # Maximum worker threads
THREAD_POOL_MIN_WORKERS=2    # Minimum worker threads

# Log configuration
LOG_LEVEL=INFO              # Log level
LOG_DIR=logs                # Log directory
```

## Development Guide

### Implementing a New ASR Provider

1. Create a new implementation file under `src/modules/asr/` (e.g., `aliyun_asr.py`)
2. Inherit from `ASRProvider` base class
3. Implement abstract methods:
   - `initialize()`: Initialize ASR engine
   - `process_audio()`: Process audio data
   - `reset()`: Reset state
   - `cleanup()`: Clean up resources

Example:
```python
from src.modules.asr.base import ASRProvider, ASRResult

class AliyunASR(ASRProvider):
    async def initialize(self):
        # Initialize Aliyun ASR
        pass

    async def process_audio(self, audio_data: bytes) -> ASRResult:
        # Process audio
        pass
```

### Implementing a New TTS Provider

Similarly, create an implementation under `src/modules/tts/`, inheriting from the `TTSProvider` base class.

### Integration with WebSocket Service

In `WatcherServer.initialize()` of `src/main.py`:

```python
# Create and initialize provider
asr_provider = AliyunASR()
await asr_provider.initialize()

# Pass to WebSocket server
self.ws_server = WebSocketServer(
    asr_provider=asr_provider,
    # ...
)
```

## Logging System

Using loguru for log management:

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Info log")
logger.debug("Debug log")
logger.warning("Warning log")
logger.error("Error log")
```

Log file locations:
- `logs/watcher_YYYY-MM-DD.log` - All logs
- `logs/watcher_error_YYYY-MM-DD.log` - Error logs only

## Thread Management

Using thread pool to execute async tasks:

```python
from src.core.thread_pool import get_thread_pool

thread_pool = get_thread_pool()
future = thread_pool.submit(your_function, arg1, arg2)
result = future.result()
```

## Testing

```bash
# Activate environment
conda activate watcher-server

# Run tests (need to implement first)
pytest tests/
```

## Troubleshooting

### Service Cannot Start

1. Check if port is already in use:
   ```bash
   # Windows
   netstat -ano | findstr :8765

   # Linux/Mac
   lsof -i :8765
   ```

2. Check if `.env` configuration is correct

3. Check log file `logs/watcher_*.log`

### Dependency Installation Failed

```bash
# Update conda
conda update conda

# Clean cache
conda clean --all

# Recreate environment
conda env remove -n watcher-server
conda env create -f environment.yml
```

## Contributing

1. Fork this project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
