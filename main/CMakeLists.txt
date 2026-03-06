idf_component_register(
    SRCS
        "app_main"
        "ble/ble.c"
        "servo/servo.c"
        "action/action.c"
        "command/command.c"
        "uart/uart_handler.c"
    INCLUDE_DIRS
        "."
        "servo"
        "action"
        "command"
        "ble"
        "uart"
    REQUIRES bt driver nvs_flash)
