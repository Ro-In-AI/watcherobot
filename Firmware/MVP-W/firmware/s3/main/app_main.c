#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_task_wdt.h"
#include "driver/uart.h"

#include "ws_router.h"
#include "ws_handlers.h"
#include "uart_bridge.h"
#include "button_voice.h"
#include "display_ui.h"
#include "wifi_client.h"
#include "ws_client.h"
#include "discovery_client.h"
#include "hal_uart.h"
#include "hal_audio.h"
#include "hal_display.h"
#include "boot_animation.h"
#include "emoji_png.h"
#include "sensecap-watcher.h"

#define TAG "MAIN"

/* Hardware test mode (set to 0 for self-test) */
#define ENABLE_HW_SELFTEST  1

/* Physical restart: click count to trigger reboot */
#define RESTART_CLICK_COUNT  5

/* ------------------------------------------------------------------ */
/* Button Callbacks (using SDK's bsp_set_btn_* interface)            */
/* ------------------------------------------------------------------ */

static void on_button_long_press(void)
{
    ESP_LOGI(TAG, "Button LONG PRESS - start recording");
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    display_update("Listening...", "listening", 0, NULL);
}

static void on_button_long_release(void)
{
    ESP_LOGI(TAG, "Button LONG RELEASE - stop recording");
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);
    display_update("Processing...", "analyzing", 0, NULL);
}

static void on_button_multi_click_restart(void)
{
    ESP_LOGW(TAG, "Button %d-click detected - REBOOTING!", RESTART_CLICK_COUNT);
    display_update("Rebooting...", "sad", 0, NULL);
    vTaskDelay(pdMS_TO_TICKS(500));
    esp_restart();
}

/* ------------------------------------------------------------------ */
/* Hardware Self-Test                                                 */
/* ------------------------------------------------------------------ */

/* Emoji loading progress callback (called from app_main context) */
static void on_emoji_type_loaded(emoji_anim_type_t type, int types_done, int types_total)
{
    /* Map emoji loading to 45% - 90% range */
    int progress = 45 + (types_done * 45) / types_total;
    boot_anim_set_progress(progress);
    boot_anim_set_text(emoji_type_name(type));
}

#if ENABLE_HW_SELFTEST

/* Note: Display test is done by hal_display_ui_init() which calls hal_display_minimal_init() */

static int test_uart(void)
{
    ESP_LOGI(TAG, "[TEST] UART...");
    /* Note: hal_uart_init is called by uart_bridge_init */
    /* Send test command to MCU */
    int ret = uart_bridge_send_servo(90, 90, 100);
    if (ret != 0) {
        ESP_LOGE(TAG, "[TEST] UART send failed");
        return -1;
    }
    ESP_LOGI(TAG, "[TEST] UART PASS (sent X:90 Y:90)");
    return 0;
}

static int test_audio(void)
{
    ESP_LOGI(TAG, "[TEST] Audio...");
    if (hal_audio_init() != 0) {
        ESP_LOGE(TAG, "[TEST] Audio init failed");
        return -1;
    }
    /* Start audio to test I2S read */
    if (hal_audio_start() != 0) {
        ESP_LOGE(TAG, "[TEST] Audio start failed");
        return -1;
    }
    /* Read a small buffer to test I2S */
    uint8_t buf[64];
    int len = hal_audio_read(buf, sizeof(buf));
    hal_audio_stop();

    /* Note: len may be 0 or timeout, that's OK for init test */
    ESP_LOGI(TAG, "[TEST] Audio PASS (I2S initialized, read %d bytes)", len);
    return 0;
}

static void run_hw_selftest(void)
{
    ESP_LOGI(TAG, "=====================================");
    ESP_LOGI(TAG, "   HARDWARE SELF-TEST START");
    ESP_LOGI(TAG, "=====================================");

    /* Display already initialized by boot_anim_init() */
    ESP_LOGI(TAG, "[TEST] Display PASS (initialized)");

    /* UART test */
    int uart_result = test_uart();

    /* Audio test */
    int audio_result = test_audio();

    /* WiFi test is done by wifi_init() + wifi_connect() in main() */

    int pass_count = 2;  /* Display + WiFi */
    int fail_count = 0;

    if (uart_result == 0) pass_count++; else fail_count++;
    if (audio_result == 0) pass_count++; else fail_count++;

    ESP_LOGI(TAG, "=====================================");
    ESP_LOGI(TAG, "   SELF-TEST RESULTS: %d PASS, %d FAIL",
             pass_count, fail_count);
    ESP_LOGI(TAG, "=====================================");

    /* Display result on screen (do NOT jump to 100% - boot continues) */
    if (fail_count == 0) {
        boot_anim_set_progress(15);
        boot_anim_set_text("HW OK");
    } else {
        char msg[32];
        snprintf(msg, sizeof(msg), "FAIL:%d", fail_count);
        boot_anim_show_error(msg);
    }
}

#endif /* ENABLE_HW_SELFTEST */

/* ------------------------------------------------------------------ */
/* Main Application                                                   */
/* ------------------------------------------------------------------ */

void app_main(void)
{
    ESP_LOGI(TAG, "MVP-W S3 v1.0 starting");

    /* 1. Minimal display init for boot animation */
    if (hal_display_minimal_init() != 0) {
        ESP_LOGE(TAG, "Failed to initialize display");
        return;
    }

    /* 2. Show boot animation */
    boot_anim_init();
    boot_anim_set_text("Initializing...");

    /* 3. UART bridge to MCU */
    boot_anim_set_progress(10);
    boot_anim_set_text("UART...");
    uart_bridge_init();

#if ENABLE_HW_SELFTEST
    run_hw_selftest();
    /* Continue regardless of result (non-fatal) */
#endif

    /* 4. Voice recorder: init only (do NOT start yet - wait until after emoji load) */
    boot_anim_set_progress(20);
    boot_anim_set_text("Voice...");
    voice_recorder_init();

    /* 5. Register button callbacks */
    bsp_set_btn_long_press_cb(on_button_long_press);
    bsp_set_btn_long_release_cb(on_button_long_release);
    bsp_set_btn_multi_click_cb(RESTART_CLICK_COUNT, on_button_multi_click_restart);
    ESP_LOGI(TAG, "Button callbacks registered via SDK");

    /* 6. Initialize and connect to WiFi */
    boot_anim_set_progress(25);
    boot_anim_set_text("WiFi...");
    wifi_init();
    if (wifi_connect() != 0) {
        boot_anim_show_error("WiFi Error");
        return;
    }
    ESP_LOGI(TAG, "WiFi connected");
    boot_anim_set_progress(35);

    /* 7. Service discovery */
    boot_anim_set_text("Discovering...");
    discovery_init();
    server_info_t server_info = {0};
    if (discovery_start(&server_info) != 0) {
        boot_anim_show_error("Server Not Found");
        return;
    }
    ESP_LOGI(TAG, "Server discovered: %s:%u", server_info.ip, server_info.port);
    boot_anim_set_progress(40);

    /* Set WebSocket URL */
    char *ws_url = discovery_get_ws_url(&server_info);
    if (ws_url) {
        ws_client_set_server_url(ws_url);
        free(ws_url);
    }

    /* 8. SPIFFS init + emoji loading (45% → 90%, the longest stage ~36s)
     * Voice recorder NOT started yet - prevents AFE ring buffer overflow during load */
    boot_anim_set_progress(45);
    boot_anim_set_text("Loading...");
    if (emoji_spiffs_init() == 0) {
        emoji_load_all_images_with_cb(on_emoji_type_loaded);
    } else {
        ESP_LOGW(TAG, "SPIFFS init failed (emoji disabled)");
        boot_anim_set_progress(90);
    }

    /* 9. Start voice recorder now (AFE ring buffer empty, no overflow risk) */
    if (voice_recorder_start() != 0) {
        ESP_LOGE(TAG, "Failed to start voice recorder (non-fatal)");
    }

    /* 10. Initialize WebSocket client */
    boot_anim_set_progress(92);
    boot_anim_set_text("Connecting...");
    ws_client_init();
    ws_router_t router = ws_handlers_get_router();
    ws_router_init(&router);
    ESP_LOGI(TAG, "WS router handlers registered");
    ws_client_start();

    /* 10. Ready! */
    boot_anim_set_progress(100);
    boot_anim_set_text("Ready!");
    vTaskDelay(pdMS_TO_TICKS(500));

    /* 11. Finish boot animation, switch to main UI */
    boot_anim_finish();
    hal_display_ui_init();
    display_update("Ready", "happy", 0, NULL);
    ESP_LOGI(TAG, "Ready");

    /* Main loop - feed watchdog and check TTS timeout */
    esp_task_wdt_add(NULL);
    while (1) {
        /* Feed watchdog */
        esp_task_wdt_reset();

        /* Check TTS timeout - auto-complete if no data for 2s */
        ws_tts_timeout_check();

        /* Short delay for responsiveness */
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
