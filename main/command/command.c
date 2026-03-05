#include "command.h"
#include <stdio.h>
#include <string.h>

static command_callback_t g_callback = NULL;

void command_init(void) {
    printf("[command] init\n");
    g_callback = NULL;
}

void command_register_callback(command_callback_t callback) {
    g_callback = callback;
    printf("[command] callback registered\n");
}

void command_process(const uint8_t* data, uint16_t len) {
    if (data == NULL || len == 0) {
        return;
    }

    // 复制数据并添加字符串结束符
    static char buffer[128];
    uint16_t copy_len = (len < sizeof(buffer) - 1) ? len : sizeof(buffer) - 1;

    // 移除可能的换行符
    while (copy_len > 0 && (data[copy_len - 1] == '\n' || data[copy_len - 1] == '\r')) {
        copy_len--;
    }

    memcpy(buffer, data, copy_len);
    buffer[copy_len] = '\0';

    printf("[command] received: %s\n", buffer);

    // 查找命令分隔符
    char* cmd = buffer;
    char* params = strchr(buffer, ':');

    if (params != NULL) {
        *params = '\0';
        params++;  // params 指向冒号后面的内容
    }

    if (cmd[0] == '\0') {
        return;  // 空命令
    }

    if (g_callback != NULL) {
        g_callback(cmd, params ? params : "");
    }
}
