[English](ALIYUN_ASR.md) | [中文](ALIYUN_ASR_CN.md)

# 阿里云ASR模块使用说明

## 概述

阿里云ASR模块基于阿里云实时语音识别SDK，提供流式语音识别功能。

## 配置

在 `.env` 文件中添加以下配置：

```bash
# ASR提供商
ASR_PROVIDER=aliyun

# 阿里云ASR配置
ALIYUN_TOKEN=your_token_here
ALIYUN_APPKEY=your_appkey_here
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1

# 可选配置
ALIYUN_ASR_ENABLE_INTERMEDIATE_RESULT=true  # 返回中间结果
ALIYUN_ASR_ENABLE_PUNCTUATION_PREDICTION=true  # 标点预测
ALIYUN_ASR_ENABLE_INVERSE_TEXT_NORMALIZATION=true  # ITN转换
```

### 获取Token和AppKey

1. **获取AppKey**:
   - 访问 [阿里云智能语音交互控制台](https://nls-portal.console.aliyun.com/applist)
   - 创建项目并获取AppKey

2. **获取Token**:
   - 参考 [Token获取文档](https://help.aliyun.com/document_detail/450255.html)
   - 使用API Key和Secret Key生成Token

## 使用示例

### 基本使用

```python
from src.modules.asr.aliyun_asr import AliyunASR

# 创建ASR实例
asr = AliyunASR(
    appkey="your_appkey",
    token="your_token",
    sample_rate=16000,
    channels=1,
)

# 初始化
await asr.initialize()

# 处理音频数据
result = await asr.process_audio(audio_bytes)
print(f"识别文本: {result.text}")

# 停止识别
await asr.stop()

# 清理资源
await asr.cleanup()
```

### 在WebSocket服务中使用

```python
from src.modules.asr.factory import ASRFactory

# 创建ASR实例
asr = ASRFactory.create_provider()
await asr.initialize()

# 处理客户端音频流
async for message in websocket:
    if isinstance(message, bytes):
        result = await asr.process_audio(message)
        # 处理识别结果...

    elif message == "over":
        # 客户端结束录音
        await asr.stop()
        final_result = await asr.get_final_result()
        # 使用识别结果...
```

### 实时语音识别流程

1. **初始化**: 调用 `initialize()` 初始化ASR引擎
2. **启动会话**: 首次调用 `process_audio()` 时自动启动识别会话
3. **发送音频**: 持续调用 `process_audio()` 发送音频数据
4. **获取中间结果**: 每次调用 `process_audio()` 返回当前识别结果
5. **结束识别**: 调用 `stop()` 停止识别会话
6. **获取最终结果**: 调用 `get_final_result()` 获取完整识别结果
7. **重置状态**: 调用 `reset()` 准备下一次识别
8. **清理资源**: 调用 `cleanup()` 释放资源

## 测试

运行测试脚本：

```bash
# 使用音频文件测试
python tests/test_aliyun_asr.py --mode file --audio path/to/audio.pcm

# 测试实时模式（模拟音频流）
python tests/test_aliyun_asr.py --mode realtime
```

### 音频文件要求

- **格式**: PCM（无压缩）
- **采样率**: 16000 Hz
- **位深**: 16-bit
- **声道**: 单声道

如果使用其他格式，需要先转换：

```bash
# 使用ffmpeg转换
ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 output.pcm
```

## 注意事项

1. **线程安全**: 阿里云SDK使用同步回调，本模块使用线程池实现异步接口
2. **会话管理**: 每次识别需要调用 `reset()` 重置状态
3. **资源清理**: 使用完毕后务必调用 `cleanup()` 释放资源
4. **音频分块**: 建议每640字节（20ms@16kHz）发送一次
5. **超时处理**: 默认等待最终结果超时为10秒

## API参考

### AliyunASR

#### 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| appkey | str | 必填 | 阿里云AppKey |
| token | str | 必填 | 访问Token |
| url | str | wss://... | 网关URL |
| sample_rate | int | 16000 | 采样率 |
| channels | int | 1 | 声道数 |
| enable_intermediate_result | bool | True | 返回中间结果 |
| enable_punctuation_prediction | bool | True | 标点预测 |
| enable_inverse_text_normalization | bool | True | ITN转换 |

#### 主要方法

- `initialize()`: 初始化ASR引擎
- `process_audio(audio_data: bytes)`: 处理音频数据
- `stop()`: 停止识别会话
- `get_final_result()`: 获取最终识别结果
- `reset()`: 重置状态
- `cleanup()`: 清理资源

## 常见问题

### 1. 连接失败

检查网络连接和URL配置，确保可以访问阿里云网关。

### 2. 认证失败

确认Token和AppKey正确，且Token未过期。

### 3. 识别准确率低

- 确保音频格式正确（16kHz, 16bit, 单声道）
- 检查音频质量，减少背景噪音
- 在控制台选择合适的模型

### 4. 内存泄漏

确保每次识别结束后调用 `cleanup()` 释放资源。
