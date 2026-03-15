#ifndef ACTION_H
#define ACTION_H

#include <stdint.h>
#include <stdbool.h>

// 预设动作数量
#define MAX_ACTIONS 10
// 每个动作的最大步骤
#define MAX_ACTION_STEPS 20
// 无效动作ID
#define INVALID_ACTION_ID 0xFF

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
