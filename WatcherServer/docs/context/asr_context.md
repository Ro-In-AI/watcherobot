# ASR Module Context

> **Last Updated**: 2026-03-04
> **Main Implementation**: AliyunASR (Aliyun Real-time Speech Recognition)

## Module Overview

The ASR (Automatic Speech Recognition) module is responsible for converting audio streams to text. Currently uses Aliyun real-time speech recognition SDK.

## File Structure

```
src/modules/asr/
├── __init__.py
├── base.py              # ASRProvider abstract base class
├── aliyun_asr.py        # AliyunASR implementation
└── factory.py           # ASR factory (currently not used)
```

## Core Classes

### ASRProvider (Abstract Base Class)

**File**: [src/modules/asr/base.py](../../src/modules/asr/base.py)

Defines the unified interface for ASR providers:

```python
class ASRProvider(ABC):
    @abstractmethod
    async def initialize(self): ...

    @abstractmethod
    async def process_audio(self, audio_data: bytes) -> ASRResult: ...

    @abstractmethod
    async def reset(self): ...

    @abstractmethod
    async def cleanup(self): ...
```

**Note**: `get_final_result()` and `stop()` methods are specific to `AliyunASR` implementation and not defined in the base class.

### AliyunASR

**File**: [src/modules/asr/aliyun_asr.py](../../src/modules/asr/aliyun_asr.py)

#### Initialization Parameters

```python
AliyunASR(
    appkey: str,                    # Aliyun AppKey (required)
    token: str = "",                # Temporary Token (deprecated)
    url: str = "wss://...",         # Gateway URL
    sample_rate: int = 16000,       # Sample rate
    channels: int = 1,              # Number of channels
    enable_intermediate_result: bool = True,
    enable_punctuation_prediction: bool = True,
    enable_inverse_text_normalization: bool = True,
    ak_id: str = "",                # AccessKeyId (recommended)
    ak_secret: str = "",            # AccessKeySecret (recommended)
)
```

#### Authentication Method

**Recommended**: AK/SK auto Token retrieval

```python
asr = AliyunASR(
    appkey="your_appkey",
    ak_id="your_access_key_id",
    ak_secret="your_access_key_secret",
)
```

System will automatically:
- Use AK/SK to get Token
- Automatically refresh Token 5 minutes before expiration

**Old method** (deprecated): Pass Token directly

```python
asr = AliyunASR(
    appkey="your_appkey",
    token="your_temp_token",
)
```

#### Workflow

```
1. initialize()          → Initialize ASR engine
2. process_audio(bytes)  → First call automatically starts session
3. process_audio(bytes)  → Continuously send audio data
4. stop()                → Stop recognition session (AliyunASR specific)
5. get_final_result()    → Get final recognition result (AliyunASR specific)
6. reset()               → Reset state (prepare for next recognition)
7. cleanup()             → Cleanup resources (when program exits)
```

**Note**: `stop()` and `get_final_result()` are methods specific to `AliyunASR` implementation and not defined in the base class.

#### Key Implementation Details

**Running in Background Thread**:

Aliyun SDK's `transcriber.start()` is a blocking call and must run in an independent background thread:

```python
# Start session
async def _start_session() -> bool:
    self._session_ready_event.clear()
    # Run start() in background thread
    self._session_thread = threading.Thread(target=_run, daemon=True)
    self._session_thread.start()
    # Wait for _on_start callback to confirm connection is ready
    await loop.run_in_executor(None, lambda: self._session_ready_event.wait(timeout=10))
```

**Sentence Accumulation Recognition**:

Recognition results are accumulated through `on_sentence_end` callback, not from `on_completed`:

```python
def _on_sentence_end(self, message: str, *args):
    result = payload.get("result", "")
    if result:
        # Accumulate all sentences
        if self._current_text:
            self._current_text += result
        else:
            self._current_text = result
```

**SDK Start Flag Wait**:

SDK sets `__start_flag` only after `on_start` callback returns, need brief sleep to ensure timing:

```python
def _on_start(self, message: str, *args):
    self._is_started = True
    # Wait for SDK to set __start_flag
    time.sleep(0.05)
    self._session_ready_event.set()
```

**Rate Limiting**:

Minimum send interval 150ms to avoid QPS limit:

```python
if time_since_last_send < self._min_send_interval:
    await asyncio.sleep(self._min_send_interval - time_since_last_send)
```

## Configuration

### Environment Variables

```bash
# ASR Configuration
ASR_PROVIDER=aliyun
ASR_SAMPLE_RATE=16000
ASR_CHANNELS=1

# Aliyun ASR Configuration
ALIYUN_TOKEN=xxx                    # Temporary Token (deprecated)
ALIYUN_AK_ID=xxx                    # AccessKeyId (recommended)
ALIYUN_AK_SECRET=xxx                # AccessKeySecret (recommended)
ALIYUN_APPKEY=xxx                   # AppKey (required)
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1

# Optional Configuration
ALIYUN_ASR_ENABLE_INTERMEDIATE_RESULT=true
ALIYUN_ASR_ENABLE_PUNCTUATION_PREDICTION=true
ALIYUN_ASR_ENABLE_INVERSE_TEXT_NORMALIZATION=true
```

### Getting AK/SK

1. Visit [Aliyun Console](https://ram.console.aliyun.com/manage/ak)
2. Create AccessKey
3. Fill AccessKeyId and AccessKeySecret into `.env`

## Usage Examples

### Basic Usage

```python
from src.modules.asr.aliyun_asr import AliyunASR

# Create ASR instance
asr = AliyunASR(
    appkey="your_appkey",
    ak_id="your_access_key_id",
    ak_secret="your_access_key_secret",
)

# Initialize
await asr.initialize()

# Process audio stream
async for audio_chunk in audio_stream:
    result = await asr.process_audio(audio_chunk)
    print(f"Intermediate result: {result.text}")

# Stop recognition
await asr.stop()

# Get final result
final_result = await asr.get_final_result()
print(f"Final result: {final_result.text}")

# Reset state (prepare for next recognition)
await asr.reset()

# Cleanup resources
await asr.cleanup()
```

### Using in WebSocket Service

```python
# main.py or websocket_server.py
asr_provider = AliyunASR(
    appkey=settings.aliyun_appkey,
    ak_id=settings.aliyun_ak_id,
    ak_secret=settings.aliyun_ak_secret,
)

await asr_provider.initialize()

# Process client audio
async for message in websocket:
    if isinstance(message, bytes):
        await asr_provider.process_audio(message)
    elif message == "over":
        await asr_provider.stop()
        result = await asr_provider.get_final_result()
        # Process recognition result...
        await asr_provider.reset()
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Token invalid or expired | Token config error or expired | Use AK/SK method |
| Connection timeout | Network issue or gateway address error | Check `ALIYUN_ASR_URL` |
| QPS limit | Requests too frequent | Increase `_min_send_interval` |
| SDK not installed | Missing dependency | `pip install alibabacloud-nls-python-sdk` |

### Error Callback

```python
def _on_error(self, message: str, *args):
    data = json.loads(message)
    error_msg = data.get("message", "Unknown error")

    # Detect QPS limit
    if "TOO_MANY_REQUESTS" in data.get("status_text", ""):
        self._connect_retry_delay = min(self._connect_retry_delay * 2, 30)

    # Put error in queue
    self._result_queue.put({
        "text": "",
        "is_final": True,
        "status": "error",
        "error": error_msg
    })
```

## Audio Format Requirements

- **Format**: PCM (uncompressed)
- **Sample Rate**: 16000 Hz
- **Bit Depth**: 16-bit
- **Channels**: Mono

### Audio Conversion

```bash
# Convert using ffmpeg
ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 output.pcm
```

## Dependencies

```
alibabacloud-nls-python-sdk  # Aliyun NLS SDK
aliyun-python-sdk-core       # Aliyun SDK core (for getting Token)
```

## Recent Changes

- **2026-03-04**: Added AK/SK auto Token retrieval
- **2026-03-04**: Implemented sentence accumulation recognition
- **2026-03-04**: Added QPS limit error handling

---

**Note**: After modifying this module, please update the "Recent Changes" section of this document.
