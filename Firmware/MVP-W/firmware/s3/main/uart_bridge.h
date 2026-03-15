#ifndef UART_BRIDGE_H
#define UART_BRIDGE_H

#include <stdint.h>
#include <stdbool.h>

/* UART bridge context */
typedef struct {
    int tx_count;       /* Number of commands sent */
    int error_count;    /* Number of errors */
} uart_bridge_t;

/**
 * Initialize UART bridge
 */
void uart_bridge_init(void);

/**
 * Send single servo command (v2.1 format)
 *
 * Protocol: "X:<angle>:<duration>\r\n" or "Y:<angle>:<duration>\r\n"
 *
 * @param id Servo identifier ("x" or "y")
 * @param angle Angle value (0-180)
 * @param duration_ms Movement duration in milliseconds (0 = smooth mode)
 * @return 0 on success, -1 on error
 */
int uart_bridge_send_servo_single(const char *id, int angle, int duration_ms);

/**
 * Send dual servo command (legacy format)
 *
 * Protocol: "X:<x>:<duration>\r\nY:<y>:<duration>\r\n"
 *
 * @param x X-axis angle (0-180)
 * @param y Y-axis angle (0-180)
 * @param duration_ms Movement duration in milliseconds
 * @return 0 on success, -1 on error
 */
int uart_bridge_send_servo(int x, int y, int duration_ms);

/**
 * Get bridge statistics
 */
void uart_bridge_get_stats(uart_bridge_t *out_stats);

/**
 * Reset statistics
 */
void uart_bridge_reset_stats(void);

/* ------------------------------------------------------------------ */
/* HAL Interface (to be implemented by hardware layer)                */
/* ------------------------------------------------------------------ */

/**
 * Send data via UART (HAL function)
 * @param data Pointer to data buffer
 * @param len Length of data
 * @return Number of bytes sent, or -1 on error
 */
int hal_uart_send(const uint8_t *data, int len);

#endif /* UART_BRIDGE_H */
