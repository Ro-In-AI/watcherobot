#ifndef SERVO_H
#define SERVO_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

// 舵机数量
#define SERVO_COUNT 2

// 舵机初始化
esp_err_t servo_init(void);

// 设置舵机角度
// angle: 目标角度值
// duration_ms: 移动时间（毫秒）
//   = 0: 平滑跟踪模式（固定步长，约67°/s）
//   > 0: 时间控制模式（指定时间到达）
esp_err_t servo_set_angle(uint8_t servo_id, uint8_t angle, uint16_t duration_ms);

// 获取当前角度
esp_err_t servo_get_angle(uint8_t servo_id, uint8_t *angle);

// 获取目标角度
esp_err_t servo_get_target_angle(uint8_t servo_id, uint8_t *angle);

// 检查舵机是否正在移动
bool servo_is_moving(uint8_t servo_id);

// 开始持续移动（摇杆模式）
// direction: 1 = 正向(角度增加), -1 = 反向(角度减少)
esp_err_t servo_start_move(uint8_t servo_id, int8_t direction);

// 停止移动
esp_err_t servo_stop(uint8_t servo_id);

// 舵机任务处理
void servo_task(void);

#endif
