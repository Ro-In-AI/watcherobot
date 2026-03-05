idf_component_register(
    SRCS
        "app_main"
        "ble/ble.c"
        "servo/servo.c"
        "action/action.c"
        "command/command.c"
    INCLUDE_DIRS
        "."
        "servo"
        "action"
        "command"
        "ble"
    REQUIRES bt driver nvs_flash)
