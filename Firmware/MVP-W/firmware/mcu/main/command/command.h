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
