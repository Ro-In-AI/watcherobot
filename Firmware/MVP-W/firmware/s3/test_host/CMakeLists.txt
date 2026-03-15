cmake_minimum_required(VERSION 3.16)
project(MVP-W_S3_Test C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Unity test framework
include(FetchContent)
FetchContent_Declare(
    Unity
    GIT_REPOSITORY https://github.com/ThrowTheSwitch/Unity.git
    GIT_TAG        v2.5.2
)
FetchContent_MakeAvailable(Unity)

# Common include directories
set(INCLUDE_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}/../main
    ${CMAKE_CURRENT_SOURCE_DIR}/..
    ${unity_SOURCE_DIR}/src
)

# ------------------------------------------------------------------ #
# Test: WS Router
# ------------------------------------------------------------------ #
add_executable(test_ws_router
    ../main/ws_router.c
    ../main/cJSON.c
    test_ws_router.c
)
target_include_directories(test_ws_router PRIVATE ${INCLUDE_DIRS})
target_link_libraries(test_ws_router PRIVATE unity)

# ------------------------------------------------------------------ #
# Test: UART Bridge
# ------------------------------------------------------------------ #
add_executable(test_uart_bridge
    ../main/uart_bridge.c
    test_uart_bridge.c
)
target_include_directories(test_uart_bridge PRIVATE ${INCLUDE_DIRS})
target_link_libraries(test_uart_bridge PRIVATE unity)

# ------------------------------------------------------------------ #
# Test: Button Voice (Audio State Machine)
# ------------------------------------------------------------------ #
add_executable(test_button_voice
    ../main/button_voice.c
    test_button_voice.c
)
target_include_directories(test_button_voice PRIVATE ${INCLUDE_DIRS})
target_link_libraries(test_button_voice PRIVATE unity)

# ------------------------------------------------------------------ #
# Test: Display UI (LVGL State Mapping)
# ------------------------------------------------------------------ #
add_executable(test_display_ui
    ../main/display_ui.c
    test_display_ui.c
)
target_include_directories(test_display_ui PRIVATE ${INCLUDE_DIRS})
target_link_libraries(test_display_ui PRIVATE unity)

# ------------------------------------------------------------------ #
# Test: Wake Word Detection
# ------------------------------------------------------------------ #
add_executable(test_wake_word
    ../main/button_voice.c
    test_wake_word.c
)
target_include_directories(test_wake_word PRIVATE ${INCLUDE_DIRS})
target_link_libraries(test_wake_word PRIVATE unity)

# ------------------------------------------------------------------ #
# CTest
# ------------------------------------------------------------------ #
enable_testing()
add_test(NAME WS_Router      COMMAND test_ws_router)
add_test(NAME UART_Bridge    COMMAND test_uart_bridge)
add_test(NAME Button_Voice   COMMAND test_button_voice)
add_test(NAME Display_UI     COMMAND test_display_ui)
add_test(NAME Wake_Word      COMMAND test_wake_word)

# Run all tests
add_custom_target(test_all
    COMMAND ctest --output-on-failure
    DEPENDS test_ws_router test_uart_bridge test_button_voice test_display_ui test_wake_word
)
