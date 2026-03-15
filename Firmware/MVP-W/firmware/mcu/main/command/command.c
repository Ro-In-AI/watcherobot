#include "command.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static command_callback_t g_callback = NULL;

/* ------------------------------------------------------------------ */
/* Private: Parse single X/Y format from MVP-W protocol                */
/* ------------------------------------------------------------------ */

/**
 * Parse MVP-W UART protocol format: X:angle:duration or Y:angle:duration
 * Examples:
 *   "X:90"       -> servo_id=0, angle=90, duration=0
 *   "X:90:500"   -> servo_id=0, angle=90, duration=500ms
 *   "Y:45"       -> servo_id=1, angle=45, duration=0
 *   "Y:45:300"   -> servo_id=1, angle=45, duration=300ms
 */
static int parse_xy_format_single(const char *cmd_str) {
    uint8_t servo_id;
    uint8_t angle = 0;
    uint16_t duration = 0;

    if (strncmp(cmd_str, "X:", 2) == 0) {
        servo_id = 0;
    } else if (strncmp(cmd_str, "Y:", 2) == 0) {
        servo_id = 1;
    } else {
        return -1;  /* Not X or Y format */
    }

    /* Parse angle and optional duration */
    const char *ptr = cmd_str + 2;  /* Skip "X:" or "Y:" */
    char *endptr = NULL;

    /* Parse angle */
    long val = strtol(ptr, &endptr, 10);
    if (endptr == ptr || val < 0 || val > 180) {
        return -1;  /* Invalid angle */
    }
    angle = (uint8_t)val;

    /* Parse optional duration */
    if (*endptr == ':') {
        ptr = endptr + 1;
        val = strtol(ptr, &endptr, 10);
        if (endptr != ptr && val >= 0 && val <= 65535) {
            duration = (uint16_t)val;
        }
    }

    /* Build SET_SERVO command: "servo_id:angle:duration" */
    static char cmd_buffer[32];
    snprintf(cmd_buffer, sizeof(cmd_buffer), "%d:%d:%d", servo_id, angle, duration);

    printf("[command] XY format: servo=%d, angle=%d, duration=%d\n", servo_id, angle, duration);

    if (g_callback != NULL) {
        g_callback("SET_SERVO", cmd_buffer);
    }

    return 0;
}

/* ------------------------------------------------------------------ */
/* Public: Command processing                                          */
/* ------------------------------------------------------------------ */

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

    /* Copy data to buffer */
    static char buffer[256];
    uint16_t copy_len = (len < sizeof(buffer) - 1) ? len : sizeof(buffer) - 1;
    memcpy(buffer, data, copy_len);
    buffer[copy_len] = '\0';

    printf("[command] received: %s\n", buffer);

    /* Parse each command separated by \r\n or \n */
    char *ptr = buffer;
    char *line_start = buffer;

    while (*ptr != '\0') {
        /* Find end of line */
        while (*ptr != '\0' && *ptr != '\r' && *ptr != '\n') {
            ptr++;
        }

        /* Terminate current line */
        char save_char = *ptr;
        if (*ptr != '\0') {
            *ptr = '\0';
        }

        /* Skip empty lines */
        if (line_start[0] != '\0') {
            /* Try X/Y format first */
            if (parse_xy_format_single(line_start) != 0) {
                /* Fallback: original command format */
                char *cmd = line_start;
                char *params = strchr(line_start, ':');

                if (params != NULL) {
                    *params = '\0';
                    params++;  /* params points to content after ":" */

                    if (cmd[0] != '\0' && g_callback != NULL) {
                        g_callback(cmd, params);
                    }
                }
            }
        }

        /* Move to next line */
        if (save_char == '\0') {
            break;
        }
        ptr++;  /* Skip \r or \n */

        /* Handle \r\n sequence */
        if (*ptr == '\n' || *ptr == '\r') {
            ptr++;
        }

        line_start = ptr;
    }
}
