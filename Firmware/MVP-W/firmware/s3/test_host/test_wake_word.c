/**
 * @file test_wake_word.c
 * @brief TDD Tests for Wake Word Detection Module
 *
 * Test Strategy:
 * 1. Mock hal_wake_word interface (Host test doesn't have ESP-SR)
 * 2. Test state machine: VOICE_EVENT_WAKE_WORD triggers recording
 * 3. Test audio flow: IDLE feeds wake word, RECORDING sends to WebSocket
 * 4. Test wake word + button equivalence
 */

#include "unity.h"
#include "button_voice.h"
#include <string.h>

/* ------------------------------------------------------------------ */
/* Mock HAL Wake Word Interface                                       */
/* ------------------------------------------------------------------ */

static int wake_word_init_count = 0;
static int wake_word_start_count = 0;
static int wake_word_stop_count = 0;
static int wake_word_feed_count = 0;
static int wake_word_deinit_count = 0;
static bool wake_word_supported = true;
static wake_word_callback_t saved_callback = NULL;
static void *saved_user_data = NULL;

/* Mock: Check if wake word is supported */
bool hal_wake_word_is_supported(void)
{
    return wake_word_supported;
}

/* Mock: Initialize wake word detector */
wake_word_ctx_t *hal_wake_word_init(const wake_word_config_t *config)
{
    wake_word_init_count++;
    if (config && config->callback) {
        saved_callback = config->callback;
        saved_user_data = config->user_data;
    }
    /* Return non-NULL to indicate success */
    return (wake_word_ctx_t *)0x12345678;
}

/* Mock: Start wake word detection */
void hal_wake_word_start(wake_word_ctx_t *ctx)
{
    wake_word_start_count++;
}

/* Mock: Stop wake word detection */
void hal_wake_word_stop(wake_word_ctx_t *ctx)
{
    wake_word_stop_count++;
}

/* Mock: Feed audio samples */
void hal_wake_word_feed(wake_word_ctx_t *ctx, const int16_t *samples, size_t num_samples)
{
    wake_word_feed_count++;
}

/* Mock: Deinitialize */
void hal_wake_word_deinit(wake_word_ctx_t *ctx)
{
    wake_word_deinit_count++;
}

size_t hal_wake_word_get_feed_size(wake_word_ctx_t *ctx)
{
    return 512;  /* Mock value */
}

const char *hal_wake_word_get_last_detected(wake_word_ctx_t *ctx)
{
    return "nihaoxiaozhi";
}

int hal_wake_word_get_available_list(wake_word_ctx_t *ctx, char *out_buf, size_t buf_size)
{
    const char *list = "nihaoxiaozhi;xiaoweixiaowei";
    strncpy(out_buf, list, buf_size - 1);
    out_buf[buf_size - 1] = '\0';
    return strlen(list);
}

/* ------------------------------------------------------------------ */
/* Mock HAL Audio / WebSocket functions                               */
/* ------------------------------------------------------------------ */

static int audio_start_count = 0;
static int audio_stop_count = 0;
static int audio_read_count = 0;
static int ws_send_audio_count = 0;
static int ws_send_audio_end_count = 0;
static int mock_error = 0;

int hal_audio_start(void)
{
    if (mock_error) return -1;
    audio_start_count++;
    return 0;
}

int hal_audio_read(uint8_t *out_buf, int max_len)
{
    if (mock_error) return -1;
    audio_read_count++;
    /* Fill with dummy data */
    if (max_len > 0) {
        memset(out_buf, 0xAA, max_len > 100 ? 100 : max_len);
        return max_len > 100 ? 100 : max_len;
    }
    return 0;
}

int hal_audio_stop(void)
{
    if (mock_error) return -1;
    audio_stop_count++;
    return 0;
}

int hal_opus_encode(const uint8_t *pcm_in, int pcm_len,
                    uint8_t *opus_out, int out_max)
{
    if (mock_error) return -1;
    int out_len = pcm_len / 10;
    if (out_len > out_max) out_len = out_max;
    memset(opus_out, 0xBB, out_len);
    return out_len;
}

int ws_send_audio(const uint8_t *data, int len)
{
    if (mock_error) return -1;
    ws_send_audio_count++;
    return 0;
}

int ws_send_audio_end(void)
{
    if (mock_error) return -1;
    ws_send_audio_end_count++;
    return 0;
}

/* Stub for hal_button_init */
int hal_button_init(void *callback)
{
    return 0;
}

void hal_button_deinit(void)
{
}

void hal_button_poll(void)
{
}

/* Stub for display_update */
int display_update(const char *text, const char *emoji, int font_size, void *out_result)
{
    return 0;
}

/* ------------------------------------------------------------------ */
/* Helper: Simulate wake word detection                               */
/* ------------------------------------------------------------------ */

static void simulate_wake_word_detection(const char *wake_word)
{
    if (saved_callback) {
        saved_callback(wake_word, saved_user_data);
    }
}

/* ------------------------------------------------------------------ */
/* Reset Mocks                                                        */
/* ------------------------------------------------------------------ */

void reset_mocks(void)
{
    wake_word_init_count = 0;
    wake_word_start_count = 0;
    wake_word_stop_count = 0;
    wake_word_feed_count = 0;
    wake_word_deinit_count = 0;
    wake_word_supported = true;
    saved_callback = NULL;
    saved_user_data = NULL;

    audio_start_count = 0;
    audio_stop_count = 0;
    audio_read_count = 0;
    ws_send_audio_count = 0;
    ws_send_audio_end_count = 0;
    mock_error = 0;
}

/* ------------------------------------------------------------------ */
/* Setup / Teardown                                                   */
/* ------------------------------------------------------------------ */

void setUp(void)
{
    reset_mocks();
    voice_recorder_init();
    voice_recorder_reset_stats();
}

void tearDown(void)
{
}

/* ------------------------------------------------------------------ */
/* Test: Wake Word Event Triggers Recording                           */
/* ------------------------------------------------------------------ */

void test_wake_word_event_starts_recording(void)
{
    /* Initial state is IDLE */
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());

    /* Wake word event should trigger recording */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);

    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_start_count);
}

void test_wake_word_event_in_recording_ignored(void)
{
    /* Start recording via wake word */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);

    /* Second wake word event should be ignored */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);

    /* Should still be recording, audio_start only called once */
    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_start_count);
}

/* ------------------------------------------------------------------ */
/* Test: Wake Word and Button Equivalence                             */
/* ------------------------------------------------------------------ */

void test_wake_word_and_button_produce_same_state(void)
{
    /* Test button press */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    voice_state_t state_button = voice_recorder_get_state();

    /* Reset */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);

    /* Test wake word */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);
    voice_state_t state_wake_word = voice_recorder_get_state();

    /* Both should result in RECORDING state */
    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, state_button);
    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, state_wake_word);
}

/* ------------------------------------------------------------------ */
/* Test: Complete Wake Word Flow                                      */
/* ------------------------------------------------------------------ */

void test_complete_wake_word_flow(void)
{
    /* Wake word triggers recording */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);
    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, voice_recorder_get_state());

    /* Simulate audio frames */
    for (int i = 0; i < 5; i++) {
        voice_recorder_tick();
    }

    /* Stop via timeout (wake word recording typically ends with timeout) */
    voice_recorder_process_event(VOICE_EVENT_TIMEOUT);

    /* Verify complete flow */
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_start_count);
    TEST_ASSERT_EQUAL_INT(1, audio_stop_count);
    TEST_ASSERT_EQUAL_INT(1, ws_send_audio_end_count);
}

/* ------------------------------------------------------------------ */
/* Test: Button Release Stops Wake Word Recording                     */
/* ------------------------------------------------------------------ */

void test_button_release_stops_wake_word_recording(void)
{
    /* Start via wake word */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);

    /* Stop via button release (user can interrupt wake word recording) */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);

    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_stop_count);
    TEST_ASSERT_EQUAL_INT(1, ws_send_audio_end_count);
}

/* ------------------------------------------------------------------ */
/* Test: Statistics for Wake Word Recording                           */
/* ------------------------------------------------------------------ */

void test_wake_word_recording_increments_stats(void)
{
    /* Start via wake word */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);

    /* Process some audio */
    voice_recorder_tick();
    voice_recorder_tick();
    voice_recorder_tick();

    /* Stop */
    voice_recorder_process_event(VOICE_EVENT_TIMEOUT);

    voice_stats_t stats;
    voice_recorder_get_stats(&stats);

    TEST_ASSERT_EQUAL_INT(1, stats.record_count);
    TEST_ASSERT_EQUAL_INT(3, stats.encode_count);
}

/* ------------------------------------------------------------------ */
/* Test: Mixed Trigger Scenarios                                      */
/* ------------------------------------------------------------------ */

void test_alternating_button_and_wake_word(void)
{
    /* First recording via button */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    voice_recorder_tick();
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());

    /* Second recording via wake word */
    voice_recorder_process_event(VOICE_EVENT_WAKE_WORD);
    voice_recorder_tick();
    voice_recorder_process_event(VOICE_EVENT_TIMEOUT);
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());

    /* Verify two complete recordings */
    voice_stats_t stats;
    voice_recorder_get_stats(&stats);
    TEST_ASSERT_EQUAL_INT(2, stats.record_count);
}

/* ------------------------------------------------------------------ */
/* Main                                                               */
/* ------------------------------------------------------------------ */

int main(void)
{
    UNITY_BEGIN();

    /* Wake word event tests */
    RUN_TEST(test_wake_word_event_starts_recording);
    RUN_TEST(test_wake_word_event_in_recording_ignored);

    /* Equivalence tests */
    RUN_TEST(test_wake_word_and_button_produce_same_state);

    /* Complete flow tests */
    RUN_TEST(test_complete_wake_word_flow);
    RUN_TEST(test_button_release_stops_wake_word_recording);

    /* Statistics tests */
    RUN_TEST(test_wake_word_recording_increments_stats);

    /* Mixed scenarios */
    RUN_TEST(test_alternating_button_and_wake_word);

    return UNITY_END();
}
