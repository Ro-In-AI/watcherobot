idf_component_register(
    SRCS
        "app_main.c"
        "ws_router.c"
        "ws_handlers.c"
        "uart_bridge.c"
        "button_voice.c"
        "display_ui.c"
        "hal_audio.c"
        "hal_display.c"
        "hal_uart.c"
        "hal_opus.c"
        "hal_button.c"
        "wifi_client.c"
        "ws_client.c"
        "discovery_client.c"
        "cJSON.c"
        # SPIFFS-based emoji animation system
        "emoji_png.c"
        "emoji_anim.c"
        # Boot animation system
        "boot_animation.c"
        # Wake word detection (conditional via Kconfig)
        "hal_wake_word.c"
    INCLUDE_DIRS "."
    REQUIRES esp_wifi esp_netif esp_event driver nvs_flash sensecap-watcher spiffs lwip
)
