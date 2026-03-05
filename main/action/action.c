#include "action.h"
#include "servo.h"
#include <string.h>
#include <stdio.h>
#include "esp_log.h"

static const char* TAG = "action";

static action_t actions[MAX_ACTIONS];
static uint8_t current_action_id = INVALID_ACTION_ID;
static bool playing = false;

void action_init(void) {
    memset(actions, 0, sizeof(actions));
    ESP_LOGI(TAG, "action system initialized");

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

    // 添加更多示例动作
    action_t greet = {
        .name = "greet",
        .step_count = 2,
        .steps = {
            {0, 0, 300},
            {0, 180, 500}
        }
    };
    actions[1] = greet;

    ESP_LOGI(TAG, "registered %d default actions", 2);
}

void action_register(uint8_t id, const char* name, action_t* action) {
    if (id >= MAX_ACTIONS || action == NULL || name == NULL) {
        ESP_LOGW(TAG, "invalid action id, null action, or null name");
        return;
    }
    if (action->step_count > MAX_ACTION_STEPS) {
        ESP_LOGW(TAG, "action step_count %d exceeds MAX_ACTION_STEPS %d",
                  action->step_count, MAX_ACTION_STEPS);
        return;
    }
    actions[id] = *action;
    strncpy(actions[id].name, name, sizeof(actions[id].name) - 1);
    actions[id].name[sizeof(actions[id].name) - 1] = '\0';
    ESP_LOGI(TAG, "registered action %d: %s", id, name);
}

void action_play(uint8_t action_id) {
    if (action_id >= MAX_ACTIONS) {
        ESP_LOGW(TAG, "invalid action id: %d", action_id);
        return;
    }
    if (actions[action_id].step_count == 0) {
        ESP_LOGW(TAG, "action %d not registered", action_id);
        return;
    }

    current_action_id = action_id;
    playing = true;

    ESP_LOGI(TAG, "playing action %d: %s", action_id, actions[action_id].name);

    // 执行第一步
    servo_step_t* step = &actions[action_id].steps[0];
    servo_set_angle(step->servo_id, step->angle, step->duration_ms);
}

void action_stop(void) {
    playing = false;
    current_action_id = INVALID_ACTION_ID;
    ESP_LOGI(TAG, "action stopped");
}

bool action_is_playing(void) {
    return playing;
}
