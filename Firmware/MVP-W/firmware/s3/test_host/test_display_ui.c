#include "unity.h"
#include "display_ui.h"
#include <string.h>

/* ------------------------------------------------------------------ */
/* Mock HAL functions                                                 */
/* ------------------------------------------------------------------ */

static char last_text[128] = {0};
static int last_font_size = 0;
static int last_emoji_id = -1;
static int set_text_count = 0;
static int set_emoji_count = 0;
static int mock_error = 0;

int hal_display_set_text(const char *text, int font_size)
{
    if (mock_error) return -1;
    set_text_count++;
    last_font_size = font_size;
    if (text) {
        strncpy(last_text, text, sizeof(last_text) - 1);
        last_text[sizeof(last_text) - 1] = '\0';
    } else {
        last_text[0] = '\0';
    }
    return 0;
}

int hal_display_set_emoji(int emoji_id)
{
    if (mock_error) return -1;
    set_emoji_count++;
    last_emoji_id = emoji_id;
    return 0;
}

void reset_mocks(void)
{
    memset(last_text, 0, sizeof(last_text));
    last_font_size = 0;
    last_emoji_id = -1;
    set_text_count = 0;
    set_emoji_count = 0;
    mock_error = 0;
}

/* ------------------------------------------------------------------ */
/* Setup / Teardown                                                   */
/* ------------------------------------------------------------------ */

void setUp(void)
{
    reset_mocks();
    display_ui_init();
}

void tearDown(void)
{
}

/* ------------------------------------------------------------------ */
/* Test: Emoji string mapping                                         */
/* ------------------------------------------------------------------ */

void test_emoji_from_string_happy(void)
{
    TEST_ASSERT_EQUAL(EMOJI_HAPPY, display_emoji_from_string("happy"));
}

void test_emoji_from_string_sad(void)
{
    TEST_ASSERT_EQUAL(EMOJI_SAD, display_emoji_from_string("sad"));
}

void test_emoji_from_string_surprised(void)
{
    TEST_ASSERT_EQUAL(EMOJI_SURPRISED, display_emoji_from_string("surprised"));
}

void test_emoji_from_string_angry(void)
{
    TEST_ASSERT_EQUAL(EMOJI_ANGRY, display_emoji_from_string("angry"));
}

void test_emoji_from_string_normal(void)
{
    TEST_ASSERT_EQUAL(EMOJI_NORMAL, display_emoji_from_string("normal"));
}

void test_emoji_from_string_unknown(void)
{
    TEST_ASSERT_EQUAL(EMOJI_UNKNOWN, display_emoji_from_string("invalid"));
    TEST_ASSERT_EQUAL(EMOJI_UNKNOWN, display_emoji_from_string("foo"));
}

void test_emoji_from_string_null(void)
{
    TEST_ASSERT_EQUAL(EMOJI_UNKNOWN, display_emoji_from_string(NULL));
}

void test_emoji_from_string_case_insensitive(void)
{
    TEST_ASSERT_EQUAL(EMOJI_HAPPY, display_emoji_from_string("HAPPY"));
    TEST_ASSERT_EQUAL(EMOJI_HAPPY, display_emoji_from_string("Happy"));
    TEST_ASSERT_EQUAL(EMOJI_SAD, display_emoji_from_string("SAD"));
}

/* ------------------------------------------------------------------ */
/* Test: Display update                                               */
/* ------------------------------------------------------------------ */

void test_display_update_text_only(void)
{
    display_result_t result;
    int ret = display_update("Hello", NULL, 0, &result);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(1, set_text_count);
    TEST_ASSERT_EQUAL_INT(0, set_emoji_count);
    TEST_ASSERT_EQUAL_STRING("Hello", last_text);
    TEST_ASSERT_TRUE(result.text_updated);
    TEST_ASSERT_FALSE(result.emoji_updated);
}

void test_display_update_text_and_emoji(void)
{
    display_result_t result;
    int ret = display_update("Hi", "happy", 24, &result);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(1, set_text_count);
    TEST_ASSERT_EQUAL_INT(1, set_emoji_count);
    TEST_ASSERT_EQUAL_STRING("Hi", last_text);
    TEST_ASSERT_EQUAL_INT(24, last_font_size);
    TEST_ASSERT_EQUAL_INT(EMOJI_HAPPY, last_emoji_id);
    TEST_ASSERT_TRUE(result.text_updated);
    TEST_ASSERT_TRUE(result.emoji_updated);
    TEST_ASSERT_EQUAL(EMOJI_HAPPY, result.emoji_id);
}

void test_display_update_emoji_only(void)
{
    display_result_t result;
    int ret = display_update(NULL, "sad", 0, &result);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(0, set_text_count);  /* No text update */
    TEST_ASSERT_EQUAL_INT(1, set_emoji_count);
    TEST_ASSERT_EQUAL_INT(EMOJI_SAD, last_emoji_id);
    TEST_ASSERT_FALSE(result.text_updated);
    TEST_ASSERT_TRUE(result.emoji_updated);
}

void test_display_update_default_font_size(void)
{
    int ret = display_update("Test", NULL, 0, NULL);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(24, last_font_size);  /* Default font size */
}

void test_display_update_custom_font_size(void)
{
    int ret = display_update("Test", NULL, 32, NULL);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(32, last_font_size);
}

/* ------------------------------------------------------------------ */
/* Test: Get current state                                            */
/* ------------------------------------------------------------------ */

void test_get_text_after_update(void)
{
    display_update("Hello World", NULL, 0, NULL);

    char buf[64];
    int ret = display_get_text(buf, sizeof(buf));

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_STRING("Hello World", buf);
}

void test_get_emoji_after_update(void)
{
    display_update(NULL, "surprised", 0, NULL);

    TEST_ASSERT_EQUAL(EMOJI_SURPRISED, display_get_emoji());
}

void test_get_text_buffer_too_small(void)
{
    display_update("This is a long text string", NULL, 0, NULL);

    char buf[8];
    int ret = display_get_text(buf, sizeof(buf));

    /* Should still succeed but truncate */
    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_STRING_LEN("This is", buf, 7);
    TEST_ASSERT_EQUAL('\0', buf[7]);
}

/* ------------------------------------------------------------------ */
/* Test: Error handling                                               */
/* ------------------------------------------------------------------ */

void test_display_update_hal_error(void)
{
    mock_error = 1;

    int ret = display_update("Test", "happy", 0, NULL);

    TEST_ASSERT_EQUAL_INT(-1, ret);
}

/* ------------------------------------------------------------------ */
/* Main                                                               */
/* ------------------------------------------------------------------ */

int main(void)
{
    UNITY_BEGIN();

    /* Emoji string mapping */
    RUN_TEST(test_emoji_from_string_happy);
    RUN_TEST(test_emoji_from_string_sad);
    RUN_TEST(test_emoji_from_string_surprised);
    RUN_TEST(test_emoji_from_string_angry);
    RUN_TEST(test_emoji_from_string_normal);
    RUN_TEST(test_emoji_from_string_unknown);
    RUN_TEST(test_emoji_from_string_null);
    RUN_TEST(test_emoji_from_string_case_insensitive);

    /* Display update */
    RUN_TEST(test_display_update_text_only);
    RUN_TEST(test_display_update_text_and_emoji);
    RUN_TEST(test_display_update_emoji_only);
    RUN_TEST(test_display_update_default_font_size);
    RUN_TEST(test_display_update_custom_font_size);

    /* Get current state */
    RUN_TEST(test_get_text_after_update);
    RUN_TEST(test_get_emoji_after_update);
    RUN_TEST(test_get_text_buffer_too_small);

    /* Error handling */
    RUN_TEST(test_display_update_hal_error);

    return UNITY_END();
}
