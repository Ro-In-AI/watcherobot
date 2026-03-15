#include "unity.h"
#include "uart_bridge.h"
#include <string.h>

/* ------------------------------------------------------------------ */
/* Mock HAL UART                                                       */
/* ------------------------------------------------------------------ */

static char last_sent[64] = {0};
static int last_sent_len = 0;
static int send_call_count = 0;
static int mock_error = 0;  /* Simulate error when non-zero */

int hal_uart_send(const uint8_t *data, int len)
{
    if (mock_error) {
        return -1;
    }

    send_call_count++;
    last_sent_len = len;

    /* Copy data for verification */
    memset(last_sent, 0, sizeof(last_sent));
    if (len > 0 && len < (int)sizeof(last_sent)) {
        memcpy(last_sent, data, len);
        last_sent[len] = '\0';
    }

    return len;
}

void reset_mock(void)
{
    memset(last_sent, 0, sizeof(last_sent));
    last_sent_len = 0;
    send_call_count = 0;
    mock_error = 0;
}

/* ------------------------------------------------------------------ */
/* Setup / Teardown                                                   */
/* ------------------------------------------------------------------ */

void setUp(void)
{
    reset_mock();
    uart_bridge_init();
    uart_bridge_reset_stats();
}

void tearDown(void)
{
}

/* ------------------------------------------------------------------ */
/* Test: Basic servo command conversion                               */
/* ------------------------------------------------------------------ */

void test_send_servo_center(void)
{
    int ret = uart_bridge_send_servo(90, 90);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(1, send_call_count);
    TEST_ASSERT_EQUAL_STRING("X:90\r\nY:90\r\n", last_sent);
}

void test_send_servo_min(void)
{
    int ret = uart_bridge_send_servo(0, 0);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(1, send_call_count);
    TEST_ASSERT_EQUAL_STRING("X:0\r\nY:0\r\n", last_sent);
}

void test_send_servo_max(void)
{
    int ret = uart_bridge_send_servo(180, 180);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(1, send_call_count);
    TEST_ASSERT_EQUAL_STRING("X:180\r\nY:180\r\n", last_sent);
}

void test_send_servo_asymmetric(void)
{
    int ret = uart_bridge_send_servo(45, 135);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(1, send_call_count);
    TEST_ASSERT_EQUAL_STRING("X:45\r\nY:135\r\n", last_sent);
}

/* ------------------------------------------------------------------ */
/* Test: Boundary clamping                                            */
/* ------------------------------------------------------------------ */

void test_send_servo_clamp_negative(void)
{
    int ret = uart_bridge_send_servo(-10, -5);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_STRING("X:0\r\nY:0\r\n", last_sent);
}

void test_send_servo_clamp_over_180(void)
{
    int ret = uart_bridge_send_servo(200, 255);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_STRING("X:180\r\nY:180\r\n", last_sent);
}

void test_send_servo_clamp_mixed(void)
{
    int ret = uart_bridge_send_servo(-10, 200);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_STRING("X:0\r\nY:180\r\n", last_sent);
}

/* ------------------------------------------------------------------ */
/* Test: Statistics                                                   */
/* ------------------------------------------------------------------ */

void test_stats_increment(void)
{
    uart_bridge_send_servo(90, 90);
    uart_bridge_send_servo(45, 45);

    uart_bridge_t stats;
    uart_bridge_get_stats(&stats);

    TEST_ASSERT_EQUAL_INT(2, stats.tx_count);
    TEST_ASSERT_EQUAL_INT(0, stats.error_count);
}

void test_stats_error_count(void)
{
    mock_error = 1;  /* Simulate UART error */

    int ret = uart_bridge_send_servo(90, 90);
    TEST_ASSERT_EQUAL_INT(-1, ret);

    uart_bridge_t stats;
    uart_bridge_get_stats(&stats);

    TEST_ASSERT_EQUAL_INT(0, stats.tx_count);
    TEST_ASSERT_EQUAL_INT(1, stats.error_count);
}

void test_stats_reset(void)
{
    uart_bridge_send_servo(90, 90);

    uart_bridge_reset_stats();

    uart_bridge_t stats;
    uart_bridge_get_stats(&stats);

    TEST_ASSERT_EQUAL_INT(0, stats.tx_count);
    TEST_ASSERT_EQUAL_INT(0, stats.error_count);
}

/* ------------------------------------------------------------------ */
/* Test: Protocol format validation                                   */
/* ------------------------------------------------------------------ */

void test_protocol_format_length(void)
{
    /* "X:90\r\nY:90\r\n" = 12 chars */
    uart_bridge_send_servo(90, 90);
    TEST_ASSERT_EQUAL_INT(12, last_sent_len);

    reset_mock();

    /* "X:180\r\nY:180\r\n" = 14 chars */
    uart_bridge_send_servo(180, 180);
    TEST_ASSERT_EQUAL_INT(14, last_sent_len);

    reset_mock();

    /* "X:0\r\nY:0\r\n" = 10 chars */
    uart_bridge_send_servo(0, 0);
    TEST_ASSERT_EQUAL_INT(10, last_sent_len);
}

void test_protocol_has_crlf(void)
{
    uart_bridge_send_servo(90, 90);

    /* Check for \r\n at correct positions */
    TEST_ASSERT_EQUAL('\r', last_sent[4]);
    TEST_ASSERT_EQUAL('\n', last_sent[5]);
    TEST_ASSERT_EQUAL('\r', last_sent[10]);
    TEST_ASSERT_EQUAL('\n', last_sent[11]);
}

/* ------------------------------------------------------------------ */
/* Main                                                               */
/* ------------------------------------------------------------------ */

int main(void)
{
    UNITY_BEGIN();

    /* Basic conversion */
    RUN_TEST(test_send_servo_center);
    RUN_TEST(test_send_servo_min);
    RUN_TEST(test_send_servo_max);
    RUN_TEST(test_send_servo_asymmetric);

    /* Boundary clamping */
    RUN_TEST(test_send_servo_clamp_negative);
    RUN_TEST(test_send_servo_clamp_over_180);
    RUN_TEST(test_send_servo_clamp_mixed);

    /* Statistics */
    RUN_TEST(test_stats_increment);
    RUN_TEST(test_stats_error_count);
    RUN_TEST(test_stats_reset);

    /* Protocol format */
    RUN_TEST(test_protocol_format_length);
    RUN_TEST(test_protocol_has_crlf);

    return UNITY_END();
}
