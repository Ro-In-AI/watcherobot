#ifndef BLE_H
#define BLE_H

#include <stdint.h>
#include "esp_err.h"

// BLE 初始化
esp_err_t ble_init(void);

// 发送通知
void ble_send_notification(const uint8_t* data, uint16_t len);

// 注册数据接收回调
typedef void (*ble_receive_callback_t)(const uint8_t* data, uint16_t len);
void ble_register_receive_callback(ble_receive_callback_t callback);

#endif
