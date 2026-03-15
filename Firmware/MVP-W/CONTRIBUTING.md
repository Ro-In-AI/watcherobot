# 贡献指南

感谢你对 MVP-W 项目的关注！

## 开发环境配置

### 前置要求

- ESP-IDF v5.2.1
- Python 3.8+
- Git

### 克隆与构建

```powershell
# 克隆仓库
git clone https://github.com/your-org/WatcherProject.git
cd WatcherProject/MVP-W/firmware/s3

# 设置 ESP-IDF 环境
C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1

# 配置并构建
idf.py set-target esp32s3
idf.py build
```

## 项目结构

```
MVP-W/
├── firmware/
│   ├── s3/          # ESP32-S3 固件 (主开发)
│   └── mcu/         # ESP32 舵机控制
├── docs/            # 技术文档
└── server/          # 边缘服务器 (旧版)
```

## 代码风格

### C 代码

- 遵循 ESP-IDF 编码规范
- 函数命名: `{模块}_{动词}_{名词}`
- 返回 `esp_err_t` 进行错误处理

### 提交信息

遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-CN/):

```
feat(ws_client): 添加自动重连功能
fix(hal_audio): 修复 24kHz 播放采样率
docs(README): 更新构建说明
```

## 测试

### Host 单元测试

```powershell
cd firmware/s3/test_host
cmake -B build -G "MinGW Makefiles"
cmake --build build
ctest --test-dir build -V
```

### 硬件测试

```powershell
idf.py -p COM3 flash monitor
```

## 提交 PR

1. 从 `master` 创建功能分支
2. 编写清晰的提交信息
3. 确保代码编译无警告
4. 更新相关文档
5. 提交 PR 并描述变更内容

## 问题反馈

使用 GitHub Issues 报告问题，请包含：
- 固件版本
- ESP-IDF 版本
- 硬件型号
- 复现步骤
- 相关日志
