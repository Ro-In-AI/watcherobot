#include "servo.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char* TAG = "servo";

// 当前实际角度（舵机当前位置）
static uint8_t current_angles[SERVO_COUNT] = {0, 0};
// 目标角度（由BLE命令更新）
static uint8_t target_angles[SERVO_COUNT] = {0, 0};
// 起始角度（时间控制模式专用）
static uint8_t start_angles[SERVO_COUNT] = {0, 0};
// 移动方向（摇杆模式）：1 = 正向, -1 = 反向, 0 = 停止
static int8_t move_directions[SERVO_COUNT] = {0, 0};

// 时间控制模式参数
static uint16_t move_durations[SERVO_COUNT] = {0, 0};    // 移动持续时间（毫秒）
static uint32_t move_start_times[SERVO_COUNT] = {0, 0};  // 移动开始时间戳

// FreeRTOS 任务句柄
static TaskHandle_t servo_task_handle = NULL;

// GPIO 配置
#define SERVO_GPIO_1 12  // X轴舵机
#define SERVO_GPIO_2 15  // Y轴舵机
#define SERVO_FREQ 50

// 角度限位配置
#define SERVO_X_MIN 30   // X轴最小角度
#define SERVO_X_MAX 150  // X轴最大角度
#define SERVO_Y_MIN 95   // Y轴最小角度
#define SERVO_Y_MAX 150  // Y轴最大角度
#define SERVO_RESOLUTION LEDC_TIMER_16_BIT
#define SERVO_RESOLUTION_BITS 16
#define SERVO_MIN_PULSE 500   // 0.5ms
#define SERVO_MAX_PULSE 2500  // 2.5ms
#define SERVO_PERIOD_US 20000 // 20ms

// 平滑跟踪参数
#define SERVO_TRACK_PERIOD_MS 15   // 跟踪周期 15ms
#define SERVO_STEP_SIZE 1           // 每步移动1度（平滑跟踪模式）
#define SERVO_MIN_DURATION 50       // 最小时间控制时间（毫秒）
#define SERVO_MAX_DURATION 5000     // 最大时间控制时间（毫秒）

// 获取角度限位
static void get_angle_limits(uint8_t servo_id, uint8_t *min_angle, uint8_t *max_angle) {
    // 防御性检查：确保 servo_id 有效
    if (servo_id >= SERVO_COUNT) {
        servo_id = 0;  // 默认使用第一个舵机的范围
    }

    if (servo_id == 0) {
        if (min_angle) *min_angle = SERVO_X_MIN;
        if (max_angle) *max_angle = SERVO_X_MAX;
    } else {
        if (min_angle) *min_angle = SERVO_Y_MIN;
        if (max_angle) *max_angle = SERVO_Y_MAX;
    }
}

// 角度转换为占空比
static uint32_t angle_to_duty(uint8_t angle) {
    uint32_t pulse_us = SERVO_MIN_PULSE + (angle * (SERVO_MAX_PULSE - SERVO_MIN_PULSE) / 180);
    return (pulse_us * (1 << SERVO_RESOLUTION_BITS)) / SERVO_PERIOD_US;
}

// 平滑跟踪任务 - 每15ms执行一次
static void servo_tracking_task(void *param) {
    (void)param;

    while (1) {
        uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;

        for (int i = 0; i < SERVO_COUNT; i++) {
            // 1. 摇杆模式（持续移动）优先级最高
            if (move_directions[i] != 0) {
                if (move_directions[i] > 0) {
                    // 正向移动
                    current_angles[i] += SERVO_STEP_SIZE;
                } else {
                    // 反向移动
                    current_angles[i] -= SERVO_STEP_SIZE;
                }

                // 限位检查
                uint8_t min_angle, max_angle;
                get_angle_limits(i, &min_angle, &max_angle);
                if (current_angles[i] > max_angle) {
                    current_angles[i] = max_angle;
                } else if (current_angles[i] < min_angle) {
                    current_angles[i] = min_angle;
                }
            }
            // 2. 时间控制模式（指定时间到达）
            else if (move_durations[i] > 0) {
                uint32_t elapsed = now - move_start_times[i];

                if (elapsed >= move_durations[i]) {
                    // 时间到达，直接设置到目标位置
                    current_angles[i] = target_angles[i];
                    move_durations[i] = 0;
                } else {
                    // 计算当前位置（使用固定的起始角度）
                    float t = (float)elapsed / (float)move_durations[i];
                    int16_t start_angle = (int16_t)start_angles[i];
                    int16_t diff = (int16_t)target_angles[i] - start_angle;
                    int16_t new_angle = start_angle + (int16_t)(diff * t);

                    // 限位检查
                    uint8_t min_angle, max_angle;
                    get_angle_limits(i, &min_angle, &max_angle);
                    if (new_angle > (int16_t)max_angle) new_angle = max_angle;
                    if (new_angle < (int16_t)min_angle) new_angle = min_angle;

                    current_angles[i] = (uint8_t)new_angle;
                }
            }
            // 3. 平滑跟踪模式（无时间参数，固定步长）
            else {
                int16_t diff = (int16_t)target_angles[i] - (int16_t)current_angles[i];

                // 如果有差距，按固定步长移动
                if (abs(diff) >= SERVO_STEP_SIZE) {
                    if (diff > 0) {
                        current_angles[i] += SERVO_STEP_SIZE;
                    } else {
                        current_angles[i] -= SERVO_STEP_SIZE;
                    }
                } else {
                    // 差距小于步长，直接到达目标
                    current_angles[i] = target_angles[i];
                }
            }

            // 写入舵机
            uint32_t duty = angle_to_duty(current_angles[i]);
            ledc_set_duty(LEDC_LOW_SPEED_MODE, i, duty);
            ledc_update_duty(LEDC_LOW_SPEED_MODE, i);
        }

        vTaskDelay(pdMS_TO_TICKS(SERVO_TRACK_PERIOD_MS));
    }
}

esp_err_t servo_init(void) {
    // 配置 LEDC 定时器
    ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_num = LEDC_TIMER_0,
        .duty_resolution = SERVO_RESOLUTION,
        .freq_hz = SERVO_FREQ,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ledc_timer_config(&timer);

    // 配置两个舵机通道
    ledc_channel_config_t channel1 = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .intr_type = LEDC_INTR_DISABLE,
        .gpio_num = SERVO_GPIO_1,
        .duty = 0,
        .hpoint = 0
    };
    ledc_channel_config(&channel1);

    ledc_channel_config_t channel2 = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1,
        .timer_sel = LEDC_TIMER_0,
        .intr_type = LEDC_INTR_DISABLE,
        .gpio_num = SERVO_GPIO_2,
        .duty = 0,
        .hpoint = 0
    };
    ledc_channel_config(&channel2);

    // 初始位置设置为限位中间值
    current_angles[0] = (SERVO_X_MIN + SERVO_X_MAX) / 2;
    current_angles[1] = (SERVO_Y_MIN + SERVO_Y_MAX) / 2;
    target_angles[0] = current_angles[0];
    target_angles[1] = current_angles[1];

    // 设置初始位置
    for (int i = 0; i < SERVO_COUNT; i++) {
        uint32_t duty = angle_to_duty(current_angles[i]);
        ledc_set_duty(LEDC_LOW_SPEED_MODE, i, duty);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, i);
    }

    // 创建平滑跟踪任务
    BaseType_t ret = xTaskCreatePinnedToCore(
        servo_tracking_task,
        "servo_track",
        3072,
        NULL,
        5,
        &servo_task_handle,
        0
    );

    if (ret != pdPASS) {
        ESP_LOGE(TAG, "failed to create servo task");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "initialized (track: %dms/%ddeg, time_ctrl: %d~%dms)",
             SERVO_TRACK_PERIOD_MS, SERVO_STEP_SIZE,
             SERVO_MIN_DURATION, SERVO_MAX_DURATION);
    return ESP_OK;
}

// 设置舵机角度
// duration_ms = 0: 平滑跟踪模式（固定步长）
// duration_ms > 0: 时间控制模式（指定时间到达）
esp_err_t servo_set_angle(uint8_t servo_id, uint8_t angle, uint16_t duration_ms) {
    if (servo_id >= SERVO_COUNT) {
        ESP_LOGW(TAG, "invalid servo_id: %d", servo_id);
        return ESP_ERR_INVALID_ARG;
    }

    // 角度限位检查
    uint8_t min_angle, max_angle;
    get_angle_limits(servo_id, &min_angle, &max_angle);

    if (angle < min_angle || angle > max_angle) {
        ESP_LOGE(TAG, "servo %d angle out of range: %d (valid: %d~%d)",
                 servo_id, angle, min_angle, max_angle);
        return ESP_ERR_INVALID_ARG;
    }

    // 停止摇杆模式
    move_directions[servo_id] = 0;

    // 设置目标角度
    target_angles[servo_id] = angle;

    // 根据duration选择模式
    if (duration_ms > 0 && duration_ms >= SERVO_MIN_DURATION) {
        // 时间控制模式
        if (duration_ms > SERVO_MAX_DURATION) {
            duration_ms = SERVO_MAX_DURATION;
        }
        // 记录起始角度（用于时间控制计算）
        start_angles[servo_id] = current_angles[servo_id];
        move_durations[servo_id] = duration_ms;
        move_start_times[servo_id] = xTaskGetTickCount() * portTICK_PERIOD_MS;

        ESP_LOGI(TAG, "servo %d (%s) %d->%d deg (time_ctrl: %dms)",
                 servo_id, (servo_id == 0) ? "X" : "Y",
                 start_angles[servo_id], angle, duration_ms);
    } else {
        // 平滑跟踪模式
        move_durations[servo_id] = 0;
        ESP_LOGI(TAG, "servo %d (%s) -> %d deg (tracking)",
                 servo_id, (servo_id == 0) ? "X" : "Y", angle);
    }

    return ESP_OK;
}

esp_err_t servo_get_angle(uint8_t servo_id, uint8_t *angle) {
    if (servo_id >= SERVO_COUNT) {
        ESP_LOGW(TAG, "invalid servo_id: %d", servo_id);
        return ESP_ERR_INVALID_ARG;
    }
    if (angle == NULL) {
        ESP_LOGW(TAG, "angle pointer is NULL");
        return ESP_ERR_INVALID_ARG;
    }
    *angle = current_angles[servo_id];
    return ESP_OK;
}

esp_err_t servo_get_target_angle(uint8_t servo_id, uint8_t *angle) {
    if (servo_id >= SERVO_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }
    if (angle == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    *angle = target_angles[servo_id];
    return ESP_OK;
}

bool servo_is_moving(uint8_t servo_id) {
    if (servo_id >= SERVO_COUNT) {
        return false;
    }
    return current_angles[servo_id] != target_angles[servo_id] ||
           move_directions[servo_id] != 0 ||
           move_durations[servo_id] > 0;
}

// 开始持续移动（摇杆模式）
esp_err_t servo_start_move(uint8_t servo_id, int8_t direction) {
    if (servo_id >= SERVO_COUNT) {
        ESP_LOGW(TAG, "invalid servo_id: %d", servo_id);
        return ESP_ERR_INVALID_ARG;
    }

    if (direction != 1 && direction != -1) {
        ESP_LOGW(TAG, "invalid direction: %d (must be 1 or -1)", direction);
        return ESP_ERR_INVALID_ARG;
    }

    // 停止时间控制和平滑跟踪
    move_durations[servo_id] = 0;
    move_directions[servo_id] = direction;

    // 同时更新目标角度
    if (direction > 0) {
        uint8_t max_angle;
        get_angle_limits(servo_id, NULL, &max_angle);
        target_angles[servo_id] = max_angle;
    } else {
        uint8_t min_angle;
        get_angle_limits(servo_id, &min_angle, NULL);
        target_angles[servo_id] = min_angle;
    }

    ESP_LOGI(TAG, "servo %d start moving: direction=%d", servo_id, direction);
    return ESP_OK;
}

// 停止移动
esp_err_t servo_stop(uint8_t servo_id) {
    if (servo_id >= SERVO_COUNT) {
        ESP_LOGW(TAG, "invalid servo_id: %d", servo_id);
        return ESP_ERR_INVALID_ARG;
    }

    // 停止所有模式
    move_directions[servo_id] = 0;
    move_durations[servo_id] = 0;
    // 设置当前角度为目标角度
    target_angles[servo_id] = current_angles[servo_id];

    ESP_LOGI(TAG, "servo %d stopped at angle %d", servo_id, current_angles[servo_id]);
    return ESP_OK;
}

void servo_task(void) {
    // 任务在 servo_init 中创建
}
