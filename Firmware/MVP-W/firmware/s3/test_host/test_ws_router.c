#include "unity.h"
#include "ws_router.h"
#include <string.h>

/* ------------------------------------------------------------------ */
/* Mock handlers - track if they were called and with what arguments  */
/* ------------------------------------------------------------------ */

static bool servo_called = false;
static bool display_called = false;
static bool status_called = false;
static bool capture_called = false;
static bool reboot_called = false;
static bool asr_result_called = false;
static bool bot_reply_called = false;
static bool tts_end_called = false;
static bool error_called = false;

static ws_servo_cmd_t last_servo;
static ws_display_cmd_t last_display;
static ws_status_cmd_t last_status;
static ws_capture_cmd_t last_capture;
static ws_asr_result_cmd_t last_asr_result;
static ws_bot_reply_cmd_t last_bot_reply;
static ws_error_cmd_t last_error;

void mock_servo_handler(const ws_servo_cmd_t *cmd) {
    servo_called = true;
    last_servo = *cmd;
}

void mock_display_handler(const ws_display_cmd_t *cmd) {
    display_called = true;
    last_display = *cmd;
}

void mock_status_handler(const ws_status_cmd_t *cmd) {
    status_called = true;
    last_status = *cmd;
}

void mock_capture_handler(const ws_capture_cmd_t *cmd) {
    capture_called = true;
    last_capture = *cmd;
}

void mock_reboot_handler(void) {
    reboot_called = true;
}

void mock_asr_result_handler(const ws_asr_result_cmd_t *cmd) {
    asr_result_called = true;
    last_asr_result = *cmd;
}

void mock_bot_reply_handler(const ws_bot_reply_cmd_t *cmd) {
    bot_reply_called = true;
    last_bot_reply = *cmd;
}

void mock_tts_end_handler(void) {
    tts_end_called = true;
}

void mock_error_handler(const ws_error_cmd_t *cmd) {
    error_called = true;
    last_error = *cmd;
}

void reset_mocks(void) {
    servo_called = false;
    display_called = false;
    status_called = false;
    capture_called = false;
    reboot_called = false;
    asr_result_called = false;
    bot_reply_called = false;
    tts_end_called = false;
    error_called = false;
    memset(&last_servo, 0, sizeof(last_servo));
    memset(&last_display, 0, sizeof(last_display));
    memset(&last_status, 0, sizeof(last_status));
    memset(&last_capture, 0, sizeof(last_capture));
    memset(&last_asr_result, 0, sizeof(last_asr_result));
    memset(&last_bot_reply, 0, sizeof(last_bot_reply));
    memset(&last_error, 0, sizeof(last_error));
}

/* ------------------------------------------------------------------ */
/* Setup / Teardown                                                   */
/* ------------------------------------------------------------------ */

void setUp(void) {
    reset_mocks();

    ws_router_t router = {
        .on_servo   = mock_servo_handler,
        .on_display = mock_display_handler,
        .on_status  = mock_status_handler,
        .on_capture = mock_capture_handler,
        .on_reboot  = mock_reboot_handler,
        .on_asr_result = mock_asr_result_handler,
        .on_bot_reply  = mock_bot_reply_handler,
        .on_tts_end    = mock_tts_end_handler,
        .on_error      = mock_error_handler,
    };
    ws_router_init(&router);
}

void tearDown(void) {
}

/* ------------------------------------------------------------------ */
/* Test: Message Type Detection (v2.0 format)                         */
/* ------------------------------------------------------------------ */

void test_route_servo_message_v2(void) {
    const char *json = "{\"type\":\"servo\",\"code\":0,\"data\":{\"x\":90,\"y\":45}}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_SERVO, type);
    TEST_ASSERT_TRUE(servo_called);
    TEST_ASSERT_EQUAL_INT(90, last_servo.x);
    TEST_ASSERT_EQUAL_INT(45, last_servo.y);
}

void test_route_display_message_v2(void) {
    const char *json = "{\"type\":\"display\",\"code\":0,\"data\":{\"text\":\"Hello\",\"emoji\":\"happy\",\"size\":32}}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_DISPLAY, type);
    TEST_ASSERT_TRUE(display_called);
    TEST_ASSERT_EQUAL_STRING("Hello", last_display.text);
    TEST_ASSERT_EQUAL_STRING("happy", last_display.emoji);
    TEST_ASSERT_EQUAL_INT(32, last_display.size);
}

void test_route_display_without_optional_fields_v2(void) {
    const char *json = "{\"type\":\"display\",\"code\":0,\"data\":{\"text\":\"Test\"}}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_DISPLAY, type);
    TEST_ASSERT_TRUE(display_called);
    TEST_ASSERT_EQUAL_STRING("Test", last_display.text);
    /* emoji and size are optional, should be empty/0 */
    TEST_ASSERT_EQUAL_STRING("", last_display.emoji);
    TEST_ASSERT_EQUAL_INT(0, last_display.size);
}

void test_route_status_message_v2(void) {
    const char *json = "{\"type\":\"status\",\"code\":0,\"data\":\"[thinking] 正在思考...\"}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_STATUS, type);
    TEST_ASSERT_TRUE(status_called);
    TEST_ASSERT_EQUAL_STRING("[thinking] 正在思考...", last_status.data);
}

void test_route_asr_result_message(void) {
    const char *json = "{\"type\":\"asr_result\",\"code\":0,\"data\":\"今天天气怎么样\"}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_ASR_RESULT, type);
    TEST_ASSERT_TRUE(asr_result_called);
    TEST_ASSERT_EQUAL_STRING("今天天气怎么样", last_asr_result.text);
}

void test_route_bot_reply_message(void) {
    const char *json = "{\"type\":\"bot_reply\",\"code\":0,\"data\":\"今天天气晴朗\"}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_BOT_REPLY, type);
    TEST_ASSERT_TRUE(bot_reply_called);
    TEST_ASSERT_EQUAL_STRING("今天天气晴朗", last_bot_reply.text);
}

void test_route_tts_end_message(void) {
    const char *json = "{\"type\":\"tts_end\",\"code\":0,\"data\":\"ok\"}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_TTS_END, type);
    TEST_ASSERT_TRUE(tts_end_called);
}

void test_route_error_message(void) {
    const char *json = "{\"type\":\"error\",\"code\":1,\"data\":\"连接失败\"}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_ERROR_MSG, type);
    TEST_ASSERT_TRUE(error_called);
    TEST_ASSERT_EQUAL_INT(1, last_error.code);
    TEST_ASSERT_EQUAL_STRING("连接失败", last_error.message);
}

void test_route_capture_message_v2(void) {
    const char *json = "{\"type\":\"capture\",\"code\":0,\"data\":{\"quality\":80}}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_CAPTURE, type);
    TEST_ASSERT_TRUE(capture_called);
    TEST_ASSERT_EQUAL_INT(80, last_capture.quality);
}

void test_route_reboot_message_v2(void) {
    const char *json = "{\"type\":\"reboot\",\"code\":0,\"data\":null}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_REBOOT, type);
    TEST_ASSERT_TRUE(reboot_called);
}

void test_route_unknown_type(void) {
    const char *json = "{\"type\":\"unknown\",\"code\":0,\"data\":null}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_UNKNOWN, type);
    TEST_ASSERT_FALSE(servo_called);
}

void test_route_invalid_json(void) {
    const char *json = "not a json";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_UNKNOWN, type);
}

void test_route_missing_type(void) {
    const char *json = "{\"code\":0,\"data\":{\"x\":90,\"y\":45}}";

    ws_msg_type_t type = ws_route_message(json);

    TEST_ASSERT_EQUAL(WS_MSG_UNKNOWN, type);
}

void test_route_null_input(void) {
    ws_msg_type_t type = ws_route_message(NULL);

    TEST_ASSERT_EQUAL(WS_MSG_UNKNOWN, type);
}

/* ------------------------------------------------------------------ */
/* Test: Servo Command Parsing (v2.0 format)                          */
/* ------------------------------------------------------------------ */

void test_parse_servo_valid_v2(void) {
    const char *json = "{\"type\":\"servo\",\"code\":0,\"data\":{\"x\":0,\"y\":180}}";
    ws_servo_cmd_t cmd;

    int ret = ws_parse_servo(json, &cmd);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(0, cmd.x);
    TEST_ASSERT_EQUAL_INT(180, cmd.y);
}

void test_parse_servo_center_v2(void) {
    const char *json = "{\"type\":\"servo\",\"code\":0,\"data\":{\"x\":90,\"y\":90}}";
    ws_servo_cmd_t cmd;

    int ret = ws_parse_servo(json, &cmd);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(90, cmd.x);
    TEST_ASSERT_EQUAL_INT(90, cmd.y);
}

void test_parse_servo_null_output(void) {
    const char *json = "{\"type\":\"servo\",\"code\":0,\"data\":{\"x\":90,\"y\":90}}";

    int ret = ws_parse_servo(json, NULL);

    TEST_ASSERT_EQUAL_INT(-1, ret);
}

/* ------------------------------------------------------------------ */
/* Test: ASR Result Parsing (v2.0)                                    */
/* ------------------------------------------------------------------ */

void test_parse_asr_result_valid(void) {
    const char *json = "{\"type\":\"asr_result\",\"code\":0,\"data\":\"你好世界\"}";
    ws_asr_result_cmd_t cmd;

    int ret = ws_parse_asr_result(json, &cmd);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_STRING("你好世界", cmd.text);
}

/* ------------------------------------------------------------------ */
/* Test: Bot Reply Parsing (v2.0)                                     */
/* ------------------------------------------------------------------ */

void test_parse_bot_reply_valid(void) {
    const char *json = "{\"type\":\"bot_reply\",\"code\":0,\"data\":\"Hello back\"}";
    ws_bot_reply_cmd_t cmd;

    int ret = ws_parse_bot_reply(json, &cmd);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_STRING("Hello back", cmd.text);
}

/* ------------------------------------------------------------------ */
/* Test: Error Message Parsing (v2.0)                                 */
/* ------------------------------------------------------------------ */

void test_parse_error_valid(void) {
    const char *json = "{\"type\":\"error\",\"code\":500,\"data\":\"Internal error\"}";
    ws_error_cmd_t cmd;

    int ret = ws_parse_error(json, &cmd);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(500, cmd.code);
    TEST_ASSERT_EQUAL_STRING("Internal error", cmd.message);
}

/* ------------------------------------------------------------------ */
/* Main                                                               */
/* ------------------------------------------------------------------ */

int main(void) {
    UNITY_BEGIN();

    /* Message type detection (v2.0 format) */
    RUN_TEST(test_route_servo_message_v2);
    RUN_TEST(test_route_display_message_v2);
    RUN_TEST(test_route_display_without_optional_fields_v2);
    RUN_TEST(test_route_status_message_v2);
    RUN_TEST(test_route_asr_result_message);
    RUN_TEST(test_route_bot_reply_message);
    RUN_TEST(test_route_tts_end_message);
    RUN_TEST(test_route_error_message);
    RUN_TEST(test_route_capture_message_v2);
    RUN_TEST(test_route_reboot_message_v2);
    RUN_TEST(test_route_unknown_type);
    RUN_TEST(test_route_invalid_json);
    RUN_TEST(test_route_missing_type);
    RUN_TEST(test_route_null_input);

    /* Servo parsing (v2.0) */
    RUN_TEST(test_parse_servo_valid_v2);
    RUN_TEST(test_parse_servo_center_v2);
    RUN_TEST(test_parse_servo_null_output);

    /* ASR result parsing */
    RUN_TEST(test_parse_asr_result_valid);

    /* Bot reply parsing */
    RUN_TEST(test_parse_bot_reply_valid);

    /* Error parsing */
    RUN_TEST(test_parse_error_valid);

    return UNITY_END();
}
