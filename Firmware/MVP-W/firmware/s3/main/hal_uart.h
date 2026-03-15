#ifndef HAL_UART_H
#define HAL_UART_H

#include <stdint.h>

/**
 * Initialize UART for MCU communication
 */
int hal_uart_init(void);

/**
 * Send data via UART
 * @param data Data buffer
 * @param len Data length
 * @return Number of bytes sent, or -1 on error
 */
int hal_uart_send(const uint8_t *data, int len);

#endif /* HAL_UART_H */
