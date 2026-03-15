#ifndef UART_HANDLER_H
#define UART_HANDLER_H

#include <stdint.h>

/**
 * Initialize UART receiver
 * - Baudrate: 115200
 * - Data: 8N1
 * - RX pin: configurable
 */
void uart_handler_init(void);

#endif /* UART_HANDLER_H */
