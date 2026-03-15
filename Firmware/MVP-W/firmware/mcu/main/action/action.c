#include "action.h"
#include "servo.h"
#include <string.h>
#include <stdio.h>
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

static const char* TAG = "action";

static action_t actions[MAX_ACTIONS];
static uint8_t current_action_id = INVALID_ACTION_ID;
static bool playing = false;

// 队列命令结构（与servo.c中的定义一致）
typedef struct {
    uint8_t servo_id;
    uint8_t angle;
    uint16_t duration_ms;
} queue_cmd_t;

// X轴和Y轴队列任务句柄
static TaskHandle_t queue_task_handles[2] = {NULL, NULL};
static bool queue_tasks_running = false;

// 队列处理任务 - 每个舵机独立运行
static void queue_task(void* param) {
    uint8_t servo_id = (uint32_t)param;  // 0=X轴, 1=Y轴
    QueueHandle_t queue = servo_get_queue(servo_id);
    const char* axis_name = (servo_id == 0) ? "X" : "Y";

    ESP_LOGI(TAG, "queue[%s] task started", axis_name);

    while (1) {
        queue_cmd_t cmd;

        // 从队列取命令（阻塞等待）
        if (xQueueReceive(queue, &cmd, portMAX_DELAY) == pdTRUE) {
            ESP_LOGI(TAG, "queue[%s] exec: servo%u -> %u deg (%ums)",
                     axis_name,
                     (unsigned int)cmd.servo_id,
                     (unsigned int)cmd.angle,
                     (unsigned int)cmd.duration_ms);

            // 执行命令
            servo_set_angle(cmd.servo_id, cmd.angle, cmd.duration_ms);

            // 等待舵机实际到达目标位置（而不是仅仅等待时间）
            while (servo_is_moving(cmd.servo_id)) {
                vTaskDelay(pdMS_TO_TICKS(10));  // 每10ms检查一次
            }

            ESP_LOGI(TAG, "queue[%s] finished", axis_name);
        }
    }
}

void action_init(void) {
    memset(actions, 0, sizeof(actions));

    // 创建X轴队列处理任务
    xTaskCreatePinnedToCore(
        queue_task,
        "servo_queue_x",
        3072,
        (void*)0,  // servo_id = 0 (X轴)
        5,
        &queue_task_handles[0],
        0
    );

    // 创建Y轴队列处理任务
    xTaskCreatePinnedToCore(
        queue_task,
        "servo_queue_y",
        3072,
        (void*)1,  // servo_id = 1 (Y轴)
        5,
        &queue_task_handles[1],
        0
    );

    queue_tasks_running = true;
    ESP_LOGI(TAG, "action system initialized with %d queue tasks", 2);

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
