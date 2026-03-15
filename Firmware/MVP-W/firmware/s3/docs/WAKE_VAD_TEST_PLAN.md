# Wake Word & VAD Testing Plan (唤醒词与 VAD 测试计划)

## Branch: WAKE_VAD_TESTING

**Created**: 2026-03-04
**Target**: 验证唤醒词检测和语音活动检测 (VAD) 功能

---

## 1. 当前状态分析

### 1.1 代码实现状态

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 唤醒词 HAL | `hal_wake_word.c` | ✅ 已实现 | ESP-SR AFE 封装 |
| 唤醒词接口 | `hal_wake_word.h` | ✅ 已定义 | 完整 API |
| 状态机集成 | `button_voice.c` | ✅ 已集成 | VOICE_EVENT_WAKE_WORD 支持 |
| 配置选项 | `Kconfig.projbuild` | ✅ 已定义 | CONFIG_ENABLE_WAKE_WORD |
| 分区表 | `partitions.csv` | ✅ 已配置 | model 分区 0x50000 |

### 1.2 当前配置状态

```bash
# 当前 sdkconfig 状态
CONFIG_ENABLE_WAKE_WORD=n              # 默认关闭
CONFIG_SR_WN_WN9_NIHAOXIAOZHI_TTS=y    # "你好小智" 模型
```

### 1.3 资源需求

| 资源 | 需求 | 说明 |
|------|------|------|
| PSRAM | ~200KB | AFE buffers |
| Flash | ~500KB | 模型文件 |
| CPU | ~15% | 检测时 |

---

## 2. 测试环境配置

### 2.1 启用唤醒词功能

**方法 1: menuconfig (推荐)**
```bash
cd firmware/s3
idf.py menuconfig
```

导航到:
```
Component Config
  └── Wake Word Configuration
        └── [*] Enable Wake Word Detection
```

**方法 2: 直接修改 sdkconfig**
```bash
# 在 firmware/s3 目录下执行
sed -i 's/# CONFIG_ENABLE_WAKE_WORD is not set/CONFIG_ENABLE_WAKE_WORD=y/' sdkconfig
```

### 2.2 确认 ESP-SR 模型

检查模型分区是否烧录:
```bash
# 查看模型分区内容
esptool.py --port COM3 read_flash 0x410000 0x50000 model_partition.bin

# 或者重新烧录模型（如果需要）
esptool.py --port COM3 write_flash 0x410000 model.bin
```

### 2.3 构建和烧录

```powershell
# 在 ESP-IDF PowerShell 中执行
C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1
cd D:\GithubRep\WatcherProject\MVP-W\firmware\s3

# 清理并重新配置
idf.py fullclean
idf.py reconfigure

# 编译
idf.py build

# 烧录
idf.py -p COM3 flash monitor
```

---

## 3. 测试用例

### Test 1: 唤醒词初始化验证

**目的**: 验证 ESP-SR 模型加载成功

**步骤**:
1. 烧录固件
2. 观察启动日志

**预期日志**:
```
I (xxx) HAL_WAKE_WORD: Initializing wake word detector...
I (xxx) HAL_WAKE_WORD: Total models loaded: 1
I (xxx) HAL_WAKE_WORD: Model 0: wn9_nihaoxiaozhi_tts
I (xxx) HAL_WAKE_WORD: Parsed 1 wake words
I (xxx) HAL_WAKE_WORD:   [0] nihaoxiaozhi
I (xxx) HAL_WAKE_WORD: AFE initialized, feed chunk size: XXX samples
I (xxx) HAL_WAKE_WORD: Wake word detector initialized successfully
I (xxx) HAL_WAKE_WORD: Wake word detection started
I (xxx) VOICE: Wake word detection enabled
```

**失败排查**:
- `Failed to initialize wakenet model` → 检查 model 分区是否烧录
- `Failed to allocate` → 检查 PSRAM 配置
- `No wakenet model found` → 检查 ESP-SR 组件是否正确下载

---

### Test 2: 唤醒词检测验证

**目的**: 验证 "你好小智" 能正确触发

**步骤**:
1. 等待设备进入 IDLE 状态
2. 清晰说出 "你好小智"
3. 观察屏幕和日志

**预期结果**:
- 屏幕显示 "Listening..."
- 日志显示:
  ```
  I (xxx) HAL_WAKE_WORD: Wake word detected: nihaoxiaozhi
  I (xxx) VOICE: Wake word detected: nihaoxiaozhi
  I (xxx) VOICE: Wake word triggered recording
  I (xxx) VOICE: start_recording: state -> RECORDING
  ```
- 设备开始录制音频

**测试距离**:
| 距离 | 预期结果 |
|------|----------|
| 0.5m | 应该成功 |
| 1.0m | 应该成功 |
| 2.0m | 可能需要提高音量 |
| 3.0m+ | 可能失败 |

---

### Test 3: 音频数据流验证

**目的**: 验证唤醒后音频正确发送到云端

**步骤**:
1. 触发唤醒词
2. 说一段话 (如 "今天天气怎么样")
3. 观察日志中的音频帧发送

**预期日志**:
```
I (xxx) VOICE: Audio: frame#1, rms=XXX, peak=XXX, zeros=XX/960
I (xxx) VOICE: Audio: frame#10, rms=XXX, peak=XXX, zeros=XX/960
I (xxx) WS_CLIENT: Sent audio frame: 1920 bytes
```

**失败排查**:
- `rms=0` 或 `peak=0` → 检查麦克风连接
- `zeros=960/960` → 麦克风静音或配置错误

---

### Test 4: 录音超时验证

**目的**: 验证长录音自动停止

**步骤**:
1. 触发唤醒词
2. 持续说话超过 30 秒（或配置的超时时间)

**预期结果**:
- 超时后自动停止录音
- 发送 audio_end 标记
- 返回 IDLE 状态

---

### Test 9: VAD 静音检测验证

**目的**: 验证静音后自动停止录音

**步骤**:
1. 启用唤醒词功能 (`CONFIG_ENABLE_WAKE_WORD=y`)
2. 触发唤醒词开始录音
3. 说一句话（如 "今天天气怎么样")
4. 停止说话，5. 等待静音超时（默认 3 秒）

**预期结果**:
- VAD 检测到静音
- 静音持续 3 秒后自动停止录音
- 日志显示 "VAD: Silence timeout detected!"
- 发送 audio_end 标记
- 屏幕显示 "Processing..." / "thinking"

**VAD 参数**:
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CONFIG_VAD_SILENCE_TIMEOUT_MS` | 3000 | 静音超时 (3秒) |
| `CONFIG_VAD_RMS_THRESHOLD` | 100 | RMS 阈值 |
| `CONFIG_VAD_MIN_SPEECH_MS` | 300 | 最小语音时长 |

**测试距离**:
| 距离 | 预期结果 |
|------|----------|
| 0.5m | 应该成功 |
| 1.0m | 应该成功 |
| 2.0m | 可能需要提高音量 |

---

### Test 10: VAD 参数调优测试

**目的**: 验证不同 VAD 参数的效果

**步骤**:
1. 尝试不同的 `CONFIG_VAD_RMS_THRESHOLD` 值 (50, 100, 200, 500)
2. 尝试不同的 `CONFIG_VAD_SILENCE_TIMEOUT_MS` 值 (1000, 2000, 3000, 5000)

**预期结果**:
- 阈值过低 → 容易误触发
- 阈值过高 → 需要更长静音才能停止
- 超时过短 → 停止太快
- 超时过长 → 响应慢

---

## 6. 问题排查指南

### Test 5: 按键与唤醒词共存验证

**目的**: 验证按键触发仍然工作

**步骤**:
1. 长按旋钮按钮
2. 观察录音开始

**预期结果**:
- 屏幕显示 "Recording..."
- 日志显示按钮触发
- 录音功能正常

---

### Test 6: 连续唤醒验证

**目的**: 验证多次唤醒的稳定性

**步骤**:
1. 说出 "你好小智" → 触发录音
2. 等待处理完成
3. 重复 10 次

**预期结果**:
- 每次都能正确触发
- 无内存泄漏
- 无崩溃

---

### Test 7: 噪音环境测试

**目的**: 验证噪音环境下的检测率

**步骤**:
1. 播放背景噪音 (电视/音乐)
2. 在不同噪音级别下测试唤醒

**噪音级别**:
| 环境 | 预期检测率 |
|------|-----------|
| 安静 (<40dB) | >95% |
| 轻度噪音 (40-60dB) | >80% |
| 中度噪音 (60-70dB) | >50% |
| 高噪音 (>70dB) | <30% |

---

### Test 8: 内存稳定性测试

**目的**: 验证长时间运行无内存泄漏

**步骤**:
1. 启动设备
2. 记录初始内存
3. 触发 50 次唤醒
4. 检查内存变化

**监控命令**:
```bash
# 在日志中查找内存信息
grep "Free heap" monitor.log
grep "Min free heap" monitor.log
```

**预期结果**:
- Free heap 稳定
- Min free heap 不持续下降

---

## 4. VAD (Voice Activity Detection) 测试

### 4.1 当前 VAD 实现状态

**注意**: 当前代码使用 ESP-SR AFE 内置的 VAD，没有独立的 VAD 模块。

ESP-SR AFE 提供:
- 自动静音过滤
- 音频前处理 (AEC, AGC, NS)

### 4.2 VAD 相关测试

**Test VAD-1: 静音抑制**
- 目的: 验证静音时不触发误报
- 步骤: 在安静环境下等待 5 分钟
- 预期: 无误触发

**Test VAD-2: 音频质量**
- 目的: 验证 AFE 处理后的音频质量
- 步骤: 录制音频并在云端检查
- 预期: 音频清晰，噪音抑制良好

---

## 5. 问题排查指南

### 5.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 唤醒词不响应 | 模型未加载 | 检查 model 分区 |
| 检测率低 | 麦克风灵敏度 | 调整 AFE 参数 |
| 内存不足 | PSRAM 配置 | 检查 sdkconfig |
| 崩溃 | 栈溢出 | 增加 Task 栈大小 |
| 延迟高 | CPU 占用高 | 调整任务优先级 |

### 5.2 调试命令

```bash
# 检查 PSRAM
grep "SPIRAM" sdkconfig

# 检查唤醒词配置
grep "ENABLE_WAKE_WORD" sdkconfig

# 检查模型配置
grep "SR_WN" sdkconfig

# 检查内存配置
grep "SPIRAM_MALLOC" sdkconfig
```

### 5.3 日志级别调整

```bash
# 在 menuconfig 中调整
Component Config -> Log output -> Default log verbosity -> Debug
```

---

## 6. 测试检查清单

### Pre-Test Checklist
- [ ] PSRAM 已启用 (Octal, 80MHz)
- [ ] CONFIG_ENABLE_WAKE_WORD=y
- [ ] 模型分区已烧录
- [ ] WiFi 已连接
- [ ] WebSocket 服务可用

### Test Execution Checklist
- [ ] Test 1: 初始化验证
- [ ] Test 2: 唤醒词检测
- [ ] Test 3: 音频数据流
- [ ] Test 4: 录音超时
- [ ] Test 5: 按键共存
- [ ] Test 6: 连续唤醒
- [ ] Test 7: 噪音环境
- [ ] Test 8: 内存稳定性

### Post-Test Checklist
- [ ] 记录所有测试结果
- [ ] 记录发现的问题
- [ ] 更新文档

---

## 7. 测试结果记录模板

```
## Test Session: [日期]

### 环境信息
- 固件版本: [commit hash]
- ESP-IDF 版本: v5.2.1
- 硬件: ESP32-S3 Watcher

### Test 1: 初始化
- 结果: [PASS/FAIL]
- 日志: [粘贴关键日志]

### Test 2: 唤醒词检测
- 结果: [PASS/FAIL]
- 检测次数: X/Y
- 备注: [任何观察]

...

### 发现的问题
1. [问题描述]
2. [问题描述]

### 建议
1. [改进建议]
```

---

*Document Version: 1.0*
*Created: 2026-03-04*
