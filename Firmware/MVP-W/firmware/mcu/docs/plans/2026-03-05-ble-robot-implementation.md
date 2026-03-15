# BLE 遥控机器人实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将单个 gatts_table_creat_demo.c 文件重构为分层架构的模块化项目，支持 BLE 控制 2 个 PWM 舵机、速度平滑移动和预设动作。

**Architecture:** 采用分层架构，命令解析层统一处理 BLE 和后续 UART 指令，舵机层使用 MCPWM/LEDC 实现平滑移动，动作层管理预设序列。

**Tech Stack:** ESP-IDF, BLE GATT, MCPWM/LEDC, FreeRTOS

---

## Task 1: 创建项目目录结构

**Files:**
- Create: `main/command/command.h`
- Create: `main/command/command.c`
- Create: `main/servo/servo.h`
- Create: `main/servo/servo.c`
- Create: `main/action/action.h`
- Create: `main/action/action.c`
- Create: `main/ble/ble.h`
- Create: `main/ble/ble.c`

**Step 1: 创建各模块目录**

```bash
mkdir -p main/command main/servo main/action main/ble
```

**Step 2: 创建 servo.h 舵机控制头文件**

```c
#ifndef SERVO_H
#define SERVO_H

#include <stdint.h>

// 舵机数量
#define SERVO_COUNT 2

// 舵机初始化
void servo_init(void);

// 设置舵机角度
// angle: 角度值 (0-180)
// duration_ms: 移动时间 (毫秒)
void servo_set_angle(uint8_t servo_id, uint8_t angle, uint16_t duration_ms);

// 获取当前角度
uint8_t servo_get_angle(uint8_t servo_id);

// 舵机任务处理 (在 FreeRTOS 任务中调用)
void servo_task(void);

#endif
```

**Step 3: 创建 action.h 动作管理头文件**

```c
#ifndef ACTION_H
#define ACTION_H

#include <stdint.h>

// 预设动作数量
#define MAX_ACTIONS 10
// 每个动作的最大步骤
#define MAX_ACTION_STEPS 20

typedef struct {
    uint8_t servo_id;
    uint8_t angle;
    uint16_t duration_ms;
} servo_step_t;

typedef struct {
    char name[32];
    uint8_t step_count;
    servo_step_t steps[MAX_ACTION_STEPS];
} action_t;

// 初始化动作系统
void action_init(void);

// 注册预设动作
void action_register(uint8_t id, const char* name, action_t* action);

// 播放动作
void action_play(uint8_t action_id);

// 停止当前动作
void action_stop(void);

// 动作是否正在播放
bool action_is_playing(void);

#endif
```

**Step 4: 创建 command.h 命令解析头文件**

```c
#ifndef COMMAND_H
#define COMMAND_H

#include <stdint.h>

// 命令回调类型
typedef void (*command_callback_t)(const char* cmd, const char* params);

// 初始化命令系统
void command_init(void);

// 注册命令回调
void command_register_callback(command_callback_t callback);

// 处理接收到的数据
void command_process(const uint8_t* data, uint16_t len);

#endif
```

**Step 5: 创建 ble.h BLE 通信头文件**

```c
#ifndef BLE_H
#define BLE_H

#include <stdint.h>

// BLE 初始化
void ble_init(void);

// 发送通知
void ble_send_notification(const uint8_t* data, uint16_t len);

// 注册数据接收回调
typedef void (*ble_receive_callback_t)(const uint8_t* data, uint16_t len);
void ble_register_receive_callback(ble_receive_callback_t callback);

#endif
```

**Step 6: 创建各模块空实现文件**

```c
// main/servo/servo.c
#include "servo.h"
#include <stdio.h>

void servo_init(void) {
    printf("[servo] init\n");
}

void servo_set_angle(uint8_t servo_id, uint8_t angle, uint16_t duration_ms) {
    printf("[servo] id=%d angle=%d duration=%dms\n", servo_id, angle, duration_ms);
}

uint8_t servo_get_angle(uint8_t servo_id) {
    return 0;
}

void servo_task(void) {
    // TODO: 实现平滑移动
}
```

类似创建 command.c, action.c, ble.c 空实现。

---

## Task 2: 重构 app_main.c

**Files:**
- Modify: `main/app_main.c`

**Step 1: 创建 app_main.c**

```c
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "esp_bt.h"

#include "ble.h"
#include "servo.h"
#include "action.h"
#include "command.h"

// 命令处理回调
static void on_command_received(const char* cmd, const char* params) {
    printf("[app] cmd: %s, params: %s\n", cmd, params);

    if (strcmp(cmd, "SET_SERVO") == 0) {
        // 解析: SET_SERVO_1:90,TIME:500
        uint8_t id, angle;
        uint16_t duration;
        sscanf(params, "%hhu:%hu,TIME:%hu", &id, &angle, &duration);
        servo_set_angle(id, angle, duration);
    } else if (strcmp(cmd, "PLAY_ACTION") == 0) {
        uint8_t action_id = atoi(params);
        action_play(action_id);
    }
}

void app_main(void) {
    // NVS 初始化
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // 释放经典蓝牙内存
    ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT));

    // 初始化各模块
    servo_init();
    action_init();
    command_init();

    // 注册命令回调
    command_register_callback(on_command_received);

    // 初始化 BLE (传入命令处理函数)
    ble_init();

    printf("[app] BLE Robot initialized\n");
}
```

---

## Task 3: 实现舵机控制层 (servo)

**Files:**
- Modify: `main/servo/servo.c`

**Step 1: 使用 LEDC 实现 PWM**

```c
#include "servo.h"
#include "driver/ledc.h"
#include "esp_log.h"

static const char* TAG = "servo";

// 当前角度
static uint8_t current_angles[SERVO_COUNT] = {0, 0};
// 目标角度
static uint8_t target_angles[SERVO_COUNT] = {0, 0};
// 移动结束时间
static uint32_t move_end_times[SERVO_COUNT] = {0, 0};

#define SERVO_GPIO_1 18
#define SERVO_GPIO_2 19
#define SERVO_FREQ 50
#define SERVO_RESOLUTION LEDC_RESOLUTION_16BIT
#define SERVO_MIN_PULSE 500   // 0.5ms
#define SERVO_MAX_PULSE 2500  // 2.5ms

void servo_init(void) {
    ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_num = LEDC_TIMER_0,
        .duty_resolution = SERVO_RESOLUTION,
        .freq_hz = SERVO_FREQ,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ledc_timer_config(&timer);

    // 配置两个舵机通道
    for (int i = 0; i < SERVO_COUNT; i++) {
        ledc_channel_config_t channel = {
            .speed_mode = LEDC_LOW_SPEED_MODE,
            .channel = i,
            .timer_sel = LEDC_TIMER_0,
            .intr_type = LEDC_INTR_DISABLE,
            .gpio_num = (i == 0) ? SERVO_GPIO_1 : SERVO_GPIO_2,
            .duty = 0,
            .hpoint = 0
        };
        ledc_channel_config(&channel);
    }

    ESP_LOGI(TAG, "initialized");
}

// 角度转换为占空比
static uint32_t angle_to_duty(uint8_t angle) {
    uint32_t pulse = SERVO_MIN_PULSE + (angle * (SERVO_MAX_PULSE - SERVO_MIN_PULSE) / 180);
    return (pulse * 65536) / 20000;  // 20ms period
}

void servo_set_angle(uint8_t servo_id, uint8_t angle, uint16_t duration_ms) {
    if (servo_id >= SERVO_COUNT || angle > 180) return;

    target_angles[servo_id] = angle;
    uint32_t duty = angle_to_duty(angle);
    ledc_set_duty(LEDC_LOW_SPEED_MODE, servo_id, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, servo_id);

    current_angles[servo_id] = angle;
    ESP_LOGI(TAG, "servo %d -> %d deg", servo_id, angle);
}

uint8_t servo_get_angle(uint8_t servo_id) {
    if (servo_id >= SERVO_COUNT) return 0;
    return current_angles[servo_id];
}
```

---

## Task 4: 实现 BLE 通信层

**Files:**
- Modify: `main/ble/ble.c`

**Step 1: 实现 GATT 服务**

参考原 gatts_table_creat_demo.c，保留 GATT 服务结构，添加数据接收和发送功能。

**关键修改**：
- 添加 `ble_register_receive_callback()`
- 在 `ESP_GATTS_WRITE_EVT` 事件中调用注册的回调

---

## Task 5: 实现命令解析层

**Files:**
- Modify: `main/command/command.c`

**Step 1: 实现命令解析**

```c
#include "command.h"
#include <string.h>
#include <stdio.h>

static command_callback_t callback = NULL;

void command_init(void) {
    // TODO: 初始化
}

void command_register_callback(command_callback_t cb) {
    callback = cb;
}

void command_process(const uint8_t* data, uint16_t len) {
    if (callback == NULL || len == 0) return;

    // 简单解析: CMD:PARAMS
    char buf[256] = {0};
    if (len >= sizeof(buf)) len = sizeof(buf) - 1;
    memcpy(buf, data, len);

    char* cmd = strtok(buf, ":");
    char* params = strtok(NULL, ":");

    if (cmd && params) {
        callback(cmd, params);
    }
}
```

---

## Task 6: 实现动作管理层

**Files:**
- Modify: `main/action/action.c`

**Step 1: 实现预设动作**

```c
#include "action.h"
#include "servo.h"
#include <string.h>

static action_t actions[MAX_ACTIONS];
static uint8_t current_action_id = 0xFF;
static uint8_t current_step = 0;
static bool playing = false;

void action_init(void) {
    memset(actions, 0, sizeof(actions));

    // 注册示例动作
    action_t wave = {
        .name = "wave",
        .step_count = 4,
        .steps = {
            {0, 90, 500},
            {0, 45, 300},
            {0, 90, 300},
            {0, 45, 300}
        }
    };
    actions[0] = wave;
}

void action_register(uint8_t id, const char* name, action_t* action) {
    if (id >= MAX_ACTIONS) return;
    actions[id] = *action;
    strncpy(actions[id].name, name, sizeof(actions[id].name) - 1);
}

void action_play(uint8_t action_id) {
    if (action_id >= MAX_ACTIONS || actions[action_id].step_count == 0) return;

    current_action_id = action_id;
    current_step = 0;
    playing = true;

    // 执行第一步
    servo_step_t* step = &actions[action_id].steps[0];
    servo_set_angle(step->servo_id, step->angle, step->duration_ms);
}

void action_stop(void) {
    playing = false;
    current_action_id = 0xFF;
}

bool action_is_playing(void) {
    return playing;
}
```

---

## Task 7: 更新 CMakeLists.txt

**Files:**
- Modify: `main/CMakeLists.txt`

**Step 1: 配置组件**

```cmake
idf_component_register(
    SRCS
        "app_main.c"
        "ble/ble.c"
        "servo/servo.c"
        "action/action.c"
        "command/command.c"
    INCLUDE_DIRS
        "."
        "ble"
        "servo"
        "action"
        "command"
)
```

---

## Task 8: 编译验证

**Step 1: 设置目标并编译**

```bash
idf.py set-target esp32
idf.py build
```

预期结果：编译成功，无错误

---

## 执行选项

**Plan complete and saved to `docs/plans/2026-03-05-ble-robot-implementation.md`. Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
