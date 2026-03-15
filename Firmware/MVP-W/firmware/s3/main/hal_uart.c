#include "hal_uart.h"
#include "driver/uart.h"
#include "esp_log.h"

#define TAG "HAL_UART"

/* UART configuration (from PRD.md) */
#define UART_NUM        UART_NUM_1
#define UART_TX         19
#define UART_RX         20
#define UART_BAUD       115200
#define UART_BUF_SIZE   256

static bool is_initialized = false;

int hal_uart_init(void)
{
    if (is_initialized) {
        return 0;
    }

    uart_config_t uart_cfg = {
        .baud_rate  = UART_BAUD,
        .data_bits  = UART_DATA_8_BITS,
        .parity     = UART_PARITY_DISABLE,
        .stop_bits  = UART_STOP_BITS_1,
        .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    esp_err_t ret = uart_param_config(UART_NUM, &uart_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Param config failed: %s", esp_err_to_name(ret));
        return -1;
    }

    ret = uart_set_pin(UART_NUM, UART_TX, UART_RX, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Set pin failed: %s", esp_err_to_name(ret));
        return -1;
    }

    ret = uart_driver_install(UART_NUM, UART_BUF_SIZE * 2, 0, 0, NULL, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Driver install failed: %s", esp_err_to_name(ret));
        return -1;
    }

    is_initialized = true;
    ESP_LOGI(TAG, "UART initialized (TX:%d RX:%d @ %d)", UART_TX, UART_RX, UART_BAUD);
    return 0;
}

int hal_uart_send(const uint8_t *data, int len)
{
    if (!is_initialized) {
        ESP_LOGE(TAG, "UART not initialized");
        return -1;
    }

    int sent = uart_write_bytes(UART_NUM, (const char *)data, len);
    if (sent < 0) {
        ESP_LOGE(TAG, "Send failed");
        return -1;
    }

    return sent;
}
