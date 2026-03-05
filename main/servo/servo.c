#include "servo.h"
#include "driver/ledc.h"
#include "esp_log.h"

static const char* TAG = "servo";

// 当前角度
static uint8_t current_angles[SERVO_COUNT] = {0, 0};

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

// 获取角度限位
static void get_angle_limits(uint8_t servo_id, uint8_t *min_angle, uint8_t *max_angle) {
    if (servo_id == 0) {
        *min_angle = SERVO_X_MIN;
        *max_angle = SERVO_X_MAX;
    } else {
        *min_angle = SERVO_Y_MIN;
        *max_angle = SERVO_Y_MAX;
    }
}

// 角度转换为占空比
static uint32_t angle_to_duty(uint8_t angle) {
    uint32_t pulse_us = SERVO_MIN_PULSE + (angle * (SERVO_MAX_PULSE - SERVO_MIN_PULSE) / 180);
    // 占空比 = pulse_us / period_us * 2^duty_resolution
    return (pulse_us * (1 << SERVO_RESOLUTION_BITS)) / SERVO_PERIOD_US;
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

    // 设置初始位置
    for (int i = 0; i < SERVO_COUNT; i++) {
        uint32_t duty = angle_to_duty(current_angles[i]);
        ledc_set_duty(LEDC_LOW_SPEED_MODE, i, duty);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, i);
    }

    ESP_LOGI(TAG, "initialized");
    return ESP_OK;
}

esp_err_t servo_set_angle(uint8_t servo_id, uint8_t angle, uint16_t duration_ms) {
    (void)duration_ms;  // 暂时不使用

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

    uint32_t duty = angle_to_duty(angle);
    ledc_set_duty(LEDC_LOW_SPEED_MODE, servo_id, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, servo_id);

    current_angles[servo_id] = angle;
    ESP_LOGI(TAG, "servo %d (%s) -> %d deg", servo_id,
             (servo_id == 0) ? "X" : "Y", angle);
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

void servo_task(void) {
    // 暂时不需要
}
