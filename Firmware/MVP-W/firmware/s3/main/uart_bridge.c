#include "uart_bridge.h"
#include "hal_uart.h"
#include "esp_log.h"
#include <stdio.h>
#include <string.h>

#define TAG "UART_BRIDGE"

/* Default duration for smooth movement (ms) */
#define DEFAULT_DURATION_MS 100

/* ------------------------------------------------------------------ */
/* Private: Statistics                                                */
/* ------------------------------------------------------------------ */

static uart_bridge_t g_stats = {0};

/* ------------------------------------------------------------------ */
/* Private: Clamp angle to valid range                                */
/* ------------------------------------------------------------------ */

static int clamp_angle(int angle)
{
    if (angle < 0) return 0;
    if (angle > 180) return 180;
    return angle;
}

/* ------------------------------------------------------------------ */
/* Public: Initialize                                                 */
/* ------------------------------------------------------------------ */

void uart_bridge_init(void)
{
    memset(&g_stats, 0, sizeof(g_stats));

    /* Initialize HAL UART */
    if (hal_uart_init() != 0) {
        ESP_LOGE(TAG, "HAL UART init failed");
        /* Continue anyway - may be tested separately */
    }

    ESP_LOGI(TAG, "UART bridge initialized");
}

/* ------------------------------------------------------------------ */
/* Public: Reset statistics                                           */
/* ------------------------------------------------------------------ */

void uart_bridge_reset_stats(void)
{
    g_stats.tx_count = 0;
    g_stats.error_count = 0;
}

/* ------------------------------------------------------------------ */
/* Public: Get statistics                                             */
/* ------------------------------------------------------------------ */

void uart_bridge_get_stats(uart_bridge_t *out_stats)
{
    if (out_stats) {
        *out_stats = g_stats;
    }
}

/* ------------------------------------------------------------------ */
/* Public: Send single servo command (v2.1 format)                   */
/* ------------------------------------------------------------------ */

/**
 * Send single servo command
 * Protocol: "X:<angle>:<duration>\r\n" or "Y:<angle>:<duration>\r\n"
 *
 * Examples:
 *   - "X:90:500\r\n" (X-axis to 90 degrees, 500ms)
 *   - "Y:45:300\r\n" (Y-axis to 45 degrees, 300ms)
 */
int uart_bridge_send_servo_single(const char *id, int angle, int duration_ms)
{
    if (!id) {
        g_stats.error_count++;
        return -1;
    }

    /* Clamp angle to valid range */
    angle = clamp_angle(angle);

    /* Use default duration if not specified */
    if (duration_ms < 0) {
        duration_ms = DEFAULT_DURATION_MS;
    }

    /* Convert id to uppercase for protocol */
    char axis = (id[0] == 'x' || id[0] == 'X') ? 'X' : 'Y';

    /* Format: "X:<angle>:<duration>\r\n" or "Y:<angle>:<duration>\r\n" */
    char buf[24];
    int len = snprintf(buf, sizeof(buf), "%c:%d:%d\r\n", axis, angle, duration_ms);

    if (len < 0 || len >= (int)sizeof(buf)) {
        g_stats.error_count++;
        return -1;
    }

    ESP_LOGI(TAG, "UART servo single: %s", buf);

    /* Send via HAL */
    int sent = hal_uart_send((uint8_t *)buf, len);
    if (sent != len) {
        g_stats.error_count++;
        return -1;
    }

    g_stats.tx_count++;
    return 0;
}

/* ------------------------------------------------------------------ */
/* Public: Send dual servo command (legacy format)                   */
/* ------------------------------------------------------------------ */

/**
 * Send dual servo command
 * Protocol: "X:<x>:<duration>\r\nY:<y>:<duration>\r\n"
 *
 * Examples:
 *   - X:90:100\r\nY:45:100\r\n (both axes, 100ms)
 */
int uart_bridge_send_servo(int x, int y, int duration_ms)
{
    /* Clamp values to valid range */
    x = clamp_angle(x);
    y = clamp_angle(y);

    /* Use default duration if not specified */
    if (duration_ms < 0) {
        duration_ms = DEFAULT_DURATION_MS;
    }

    /* Format: "X:<x>:<duration>\r\nY:<y>:<duration>\r\n" */
    char buf[48];
    int len = snprintf(buf, sizeof(buf), "X:%d:%d\r\nY:%d:%d\r\n",
                       x, duration_ms, y, duration_ms);

    if (len < 0 || len >= (int)sizeof(buf)) {
        g_stats.error_count++;
        return -1;
    }

    ESP_LOGD(TAG, "UART servo dual: %s", buf);

    /* Send via HAL */
    int sent = hal_uart_send((uint8_t *)buf, len);
    if (sent != len) {
        g_stats.error_count++;
        return -1;
    }

    g_stats.tx_count++;
    return 0;
}
