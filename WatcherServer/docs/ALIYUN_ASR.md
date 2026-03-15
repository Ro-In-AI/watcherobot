[English](ALIYUN_ASR.md) | [中文](ALIYUN_ASR_CN.md)

# Aliyun ASR Module Usage Guide

## Overview

The Aliyun ASR module is based on Aliyun's real-time speech recognition SDK, providing streaming speech recognition functionality.

## Configuration

Add the following configuration to your `.env` file:

```bash
# ASR provider
ASR_PROVIDER=aliyun

# Aliyun ASR configuration
ALIYUN_TOKEN=your_token_here
ALIYUN_APPKEY=your_appkey_here
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1

# Optional configuration
ALIYUN_ASR_ENABLE_INTERMEDIATE_RESULT=true  # Return intermediate results
ALIYUN_ASR_ENABLE_PUNCTUATION_PREDICTION=true  # Punctuation prediction
ALIYUN_ASR_ENABLE_INVERSE_TEXT_NORMALIZATION=true  # ITN conversion
```

### Getting Token and AppKey

1. **Get AppKey**:
   - Visit [Aliyun Intelligent Speech Interaction Console](https://nls-portal.console.aliyun.com/applist)
   - Create a project and get AppKey

2. **Get Token**:
   - Refer to [Token Getting Guide](https://help.aliyun.com/document_detail/450255.html)
   - Use API Key and Secret Key to generate Token

## Usage Examples

### Basic Usage

```python
from src.modules.asr.aliyun_asr import AliyunASR

# Create ASR instance
asr = AliyunASR(
    appkey="your_appkey",
    token="your_token",
    sample_rate=16000,
    channels=1,
)

# Initialize
await asr.initialize()

# Process audio data
result = await asr.process_audio(audio_bytes)
print(f"Recognized text: {result.text}")

# Stop recognition
await asr.stop()

# Cleanup resources
await asr.cleanup()
```

### Using in WebSocket Service

```python
from src.modules.asr.factory import ASRFactory

# Create ASR instance
asr = ASRFactory.create_provider()
await asr.initialize()

# Process client audio stream
async for message in websocket:
    if isinstance(message, bytes):
        result = await asr.process_audio(message)
        # Process recognition result...

    elif message == "over":
        # Client finished recording
        await asr.stop()
        final_result = await asr.get_final_result()
        # Use recognition result...
```

### Real-time Speech Recognition Flow

1. **Initialize**: Call `initialize()` to initialize the ASR engine
2. **Start Session**: First call to `process_audio()` automatically starts the recognition session
3. **Send Audio**: Continuously call `process_audio()` to send audio data
4. **Get Intermediate Results**: Each call to `process_audio()` returns the current recognition result
5. **End Recognition**: Call `stop()` to stop the recognition session
6. **Get Final Result**: Call `get_final_result()` to get the complete recognition result
7. **Reset State**: Call `reset()` to prepare for next recognition
8. **Cleanup Resources**: Call `cleanup()` to release resources

## Testing

Run the test script:

```bash
# Test with audio file
python tests/test_aliyun_asr.py --mode file --audio path/to/audio.pcm

# Test real-time mode (simulate audio stream)
python tests/test_aliyun_asr.py --mode realtime
```

### Audio File Requirements

- **Format**: PCM (uncompressed)
- **Sample Rate**: 16000 Hz
- **Bit Depth**: 16-bit
- **Channels**: Mono

If using other formats, conversion is required:

```bash
# Convert using ffmpeg
ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 output.pcm
```

## Important Notes

1. **Thread Safety**: Aliyun SDK uses synchronous callbacks; this module uses thread pool to implement async interface
2. **Session Management**: Each recognition requires calling `reset()` to reset state
3. **Resource Cleanup**: Be sure to call `cleanup()` to release resources after use
4. **Audio Chunking**: Recommended to send 640 bytes (20ms@16kHz) at a time
5. **Timeout Handling**: Default timeout for waiting for final result is 10 seconds

## API Reference

### AliyunASR

#### Initialization Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| appkey | str | Required | Aliyun AppKey |
| token | str | Required | Access Token |
| url | str | wss://... | Gateway URL |
| sample_rate | int | 16000 | Sample rate |
| channels | int | 1 | Number of channels |
| enable_intermediate_result | bool | True | Return intermediate results |
| enable_punctuation_prediction | bool | True | Punctuation prediction |
| enable_inverse_text_normalization | bool | True | ITN conversion |

#### Main Methods

- `initialize()`: Initialize ASR engine
- `process_audio(audio_data: bytes)`: Process audio data
- `stop()`: Stop recognition session
- `get_final_result()`: Get final recognition result
- `reset()`: Reset state
- `cleanup()`: Cleanup resources

## Common Issues

### 1. Connection Failed

Check network connection and URL configuration to ensure Aliyun gateway is accessible.

### 2. Authentication Failed

Confirm Token and AppKey are correct and Token has not expired.

### 3. Low Recognition Accuracy

- Ensure audio format is correct (16kHz, 16bit, mono)
- Check audio quality, reduce background noise
- Select appropriate model in console

### 4. Memory Leak

Make sure to call `cleanup()` to release resources after each recognition session.
