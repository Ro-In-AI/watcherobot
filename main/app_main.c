#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "esp_bt.h"
#include "esp_err.h"

#include "ble/ble.h"
#include "servo/servo.h"
#include "action/action.h"
#include "command/command.h"
#include "uart/uart_handler.h"

// 命令处理回调
static void on_command_received(const char* cmd, const char* params)
{
    printf("[app] cmd: %s, params: %s\n", cmd, params);

    // 修复 MEDIUM: params 可能为 NULL
    if (params == NULL) {
        return;
    }

    if (strcmp(cmd, "SET_SERVO") == 0) {
        // 解析: SET_SERVO:0:90 或 SET_SERVO:0:90:500
        uint8_t id, angle;
        uint16_t duration = 0;
        int parsed = sscanf(params, "%hhu:%hhu:%hu", &id, &angle, &duration);
        if (parsed < 2) {
            printf("[app] ERROR: Failed to parse SET_SERVO params\n");
            return;
        }
        servo_set_angle(id, angle, duration);
    }
    else if (strcmp(cmd, "SERVO_MOVE") == 0) {
        // 解析: SERVO_MOVE:0:1 (servo_id:direction)
        // direction: 1 = 正向, -1 = 反向, 0 = 停止
        int8_t id, direction;
        int parsed = sscanf(params, "%hhd:%hhd", &id, &direction);
        if (parsed != 2) {
            printf("[app] ERROR: Failed to parse SERVO_MOVE params\n");
            return;
        }
        if (id < 0 || id >= SERVO_COUNT) {
            printf("[app] ERROR: Invalid servo id: %d\n", id);
            return;
        }
        if (direction == 0) {
            servo_stop(id);
        } else {
            servo_start_move(id, direction);
        }
    }
    else if (strcmp(cmd, "PLAY_ACTION") == 0) {
        // 修复 MEDIUM: atoi() 不提供错误检测，使用 strtol() 代替
        errno = 0;
        char* endptr;
        long action_id_long = strtol(params, &endptr, 10);
        if (errno != 0 || *endptr != '\0' || action_id_long < 0 || action_id_long > 255) {
            printf("[app] ERROR: Invalid action_id\n");
            return;
        }
        uint8_t action_id = (uint8_t)action_id_long;
        action_play(action_id);
    }
    else if (strcmp(cmd, "QUEUE_ADD") == 0) {
        // 解析: QUEUE_ADD:servo_id:angle:duration_ms
        uint8_t servo_id, angle;
        uint16_t duration;
        int parsed = sscanf(params, "%hhu:%hhu:%hu", &servo_id, &angle, &duration);
        if (parsed < 3) {
            printf("[app] ERROR: Failed to parse QUEUE_ADD params\n");
            return;
        }
        // 加入队列，action模块会创建独立任务处理
        servo_set_angle_delayed(servo_id, angle, duration);
    }
    else if (strcmp(cmd, "QUEUE_CLEAR") == 0) {
        servo_queue_clear();
    }
}

// BLE 数据接收回调 - 将数据传给命令解析层
static void on_ble_data_received(const uint8_t* data, uint16_t len)
{
    command_process(data, len);
}

void app_main(void)
{
    // NVS 初始化
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // 初始化各模块
    ESP_ERROR_CHECK(servo_init());
    action_init();
    command_init();

    // 注册命令回调
    command_register_callback(on_command_received);

    // 初始化 UART 并注册数据接收回调 (MVP-W S3 通讯)
    uart_handler_init();

    // 初始化 BLE 并注册数据接收回调
    ESP_ERROR_CHECK(ble_init());
    ble_register_receive_callback(on_ble_data_received);

    printf("[app] BLE + UART Robot initialized\n");
}
