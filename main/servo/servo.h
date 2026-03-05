#ifndef SERVO_H
#define SERVO_H

#include <stdint.h>
#include "esp_err.h"

// 舵机数量
#define SERVO_COUNT 2

// 舵机初始化
esp_err_t servo_init(void);

// 设置舵机角度
// angle: 角度值 (0-180)
// duration_ms: 移动时间 (毫秒) - 当前同步实现暂未使用
esp_err_t servo_set_angle(uint8_t servo_id, uint8_t angle, uint16_t duration_ms);

// 获取当前角度
esp_err_t servo_get_angle(uint8_t servo_id, uint8_t *angle);

// 舵机任务处理 (在 FreeRTOS 任务中调用)
void servo_task(void);

#endif
