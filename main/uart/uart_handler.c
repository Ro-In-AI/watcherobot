/**
 * @file uart_handler.c
 * @brief UART receiver for MVP-W communication
 */

#include "uart_handler.h"
#include "../command/command.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define TAG "UART_HANDLER"

/* UART configuration */
#define UART_PORT_NUM      UART_NUM_2
#define UART_TX_PIN        17
#define UART_RX_PIN        16
#define UART_BAUD_RATE     115200
#define UART_BUFFER_SIZE   256

/* ------------------------------------------------------------------ */
/* Private: UART receiver task                                         */
/* ------------------------------------------------------------------ */

static void uart_receive_task(void *arg)
{
    /* RX buffer */
    uint8_t data[UART_BUFFER_SIZE];

    while (1) {
        /* Read data from UART */
        int len = uart_read_bytes(UART_PORT_NUM, data, UART_BUFFER_SIZE, 20 / portTICK_PERIOD_MS);

        if (len > 0) {
            /* Process received data */
            printf("[uart] received %d bytes: ", len);
            for (int i = 0; i < len; i++) {
                printf("%02x ", data[i]);
            }
            printf("\n");

            /* Send to command processor */
            command_process(data, len);
        }
    }
}

/* ------------------------------------------------------------------ */
/* Public: Initialize UART receiver                                    */
/* ------------------------------------------------------------------ */

void uart_handler_init(void)
{
    /* UART configuration */
    uart_config_t uart_config = {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    };

    /* Install UART driver */
    ESP_ERROR_CHECK(uart_param_config(UART_PORT_NUM, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT_NUM, UART_TX_PIN, UART_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT_NUM, UART_BUFFER_SIZE * 2, UART_BUFFER_SIZE * 2, 0, NULL, 0));

    ESP_LOGI(TAG, "UART initialized: TX=GPIO%d, RX=GPIO%d, baud=%d",
             UART_TX_PIN, UART_RX_PIN, UART_BAUD_RATE);

    /* Create receiver task */
    xTaskCreate(uart_receive_task, "uart_rx", 8192, NULL, 10, NULL);
}
