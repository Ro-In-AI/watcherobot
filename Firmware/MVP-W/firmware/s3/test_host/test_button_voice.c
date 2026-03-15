#include "unity.h"
#include "button_voice.h"
#include <string.h>

/* ------------------------------------------------------------------ */
/* Mock HAL / WebSocket functions                                     */
/* ------------------------------------------------------------------ */

static int audio_start_count = 0;
static int audio_stop_count = 0;
static int audio_read_count = 0;
static int opus_encode_count = 0;
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
    opus_encode_count++;
    /* Simulate encoding: output is smaller than input */
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

void reset_mocks(void)
{
    audio_start_count = 0;
    audio_stop_count = 0;
    audio_read_count = 0;
    opus_encode_count = 0;
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
/* Test: Initial state                                                */
/* ------------------------------------------------------------------ */

void test_initial_state_is_idle(void)
{
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());
}

void test_tick_in_idle_does_nothing(void)
{
    int ret = voice_recorder_tick();

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_INT(0, audio_read_count);
    TEST_ASSERT_EQUAL_INT(0, opus_encode_count);
}

/* ------------------------------------------------------------------ */
/* Test: Button press starts recording                                */
/* ------------------------------------------------------------------ */

void test_button_press_starts_recording(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_start_count);
}

void test_button_press_in_recording_ignored(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);  /* Second press */

    /* Should still be recording, audio_start only called once */
    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_start_count);
}

/* ------------------------------------------------------------------ */
/* Test: Button release stops recording                               */
/* ------------------------------------------------------------------ */

void test_button_release_stops_recording(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);

    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_stop_count);
    TEST_ASSERT_EQUAL_INT(1, ws_send_audio_end_count);
}

void test_button_release_in_idle_ignored(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);

    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(0, audio_stop_count);
}

/* ------------------------------------------------------------------ */
/* Test: Recording tick flow                                          */
/* ------------------------------------------------------------------ */

void test_tick_in_recording_processes_audio(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    int ret = voice_recorder_tick();

    TEST_ASSERT_GREATER_THAN(0, ret);
    TEST_ASSERT_EQUAL_INT(1, audio_read_count);
    TEST_ASSERT_EQUAL_INT(1, opus_encode_count);
    TEST_ASSERT_EQUAL_INT(1, ws_send_audio_count);
}

void test_multiple_ticks_in_recording(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    voice_recorder_tick();
    voice_recorder_tick();
    voice_recorder_tick();

    TEST_ASSERT_EQUAL_INT(3, audio_read_count);
    TEST_ASSERT_EQUAL_INT(3, opus_encode_count);
    TEST_ASSERT_EQUAL_INT(3, ws_send_audio_count);
}

void test_complete_recording_flow(void)
{
    /* Start recording */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    /* Simulate 5 audio frames */
    for (int i = 0; i < 5; i++) {
        voice_recorder_tick();
    }

    /* Stop recording */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);

    /* Verify complete flow */
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_start_count);
    TEST_ASSERT_EQUAL_INT(5, audio_read_count);
    TEST_ASSERT_EQUAL_INT(5, opus_encode_count);
    TEST_ASSERT_EQUAL_INT(5, ws_send_audio_count);
    TEST_ASSERT_EQUAL_INT(1, audio_stop_count);
    TEST_ASSERT_EQUAL_INT(1, ws_send_audio_end_count);
}

/* ------------------------------------------------------------------ */
/* Test: Statistics                                                   */
/* ------------------------------------------------------------------ */

void test_stats_record_count(void)
{
    /* Complete one recording */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    voice_recorder_tick();
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);

    /* Complete another recording */
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    voice_recorder_tick();
    voice_recorder_process_event(VOICE_EVENT_BUTTON_RELEASE);

    voice_stats_t stats;
    voice_recorder_get_stats(&stats);

    TEST_ASSERT_EQUAL_INT(2, stats.record_count);
    TEST_ASSERT_EQUAL_INT(2, stats.encode_count);
}

void test_stats_encode_count(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    voice_recorder_tick();
    voice_recorder_tick();
    voice_recorder_tick();

    voice_stats_t stats;
    voice_recorder_get_stats(&stats);

    TEST_ASSERT_EQUAL_INT(3, stats.encode_count);
}

void test_stats_current_state(void)
{
    voice_stats_t stats;

    voice_recorder_get_stats(&stats);
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, stats.current_state);

    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    voice_recorder_get_stats(&stats);
    TEST_ASSERT_EQUAL(VOICE_STATE_RECORDING, stats.current_state);
}

/* ------------------------------------------------------------------ */
/* Test: Error handling                                               */
/* ------------------------------------------------------------------ */

void test_audio_start_error(void)
{
    mock_error = 1;

    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    /* Should stay in idle on error */
    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());

    voice_stats_t stats;
    voice_recorder_get_stats(&stats);
    TEST_ASSERT_EQUAL_INT(1, stats.error_count);
}

void test_tick_error_in_recording(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);

    mock_error = 1;
    int ret = voice_recorder_tick();

    TEST_ASSERT_EQUAL_INT(-1, ret);
}

/* ------------------------------------------------------------------ */
/* Test: Timeout event                                                */
/* ------------------------------------------------------------------ */

void test_timeout_stops_recording(void)
{
    voice_recorder_process_event(VOICE_EVENT_BUTTON_PRESS);
    voice_recorder_process_event(VOICE_EVENT_TIMEOUT);

    TEST_ASSERT_EQUAL(VOICE_STATE_IDLE, voice_recorder_get_state());
    TEST_ASSERT_EQUAL_INT(1, audio_stop_count);
    TEST_ASSERT_EQUAL_INT(1, ws_send_audio_end_count);
}

/* ------------------------------------------------------------------ */
/* Main                                                               */
/* ------------------------------------------------------------------ */

int main(void)
{
    UNITY_BEGIN();

    /* Initial state */
    RUN_TEST(test_initial_state_is_idle);
    RUN_TEST(test_tick_in_idle_does_nothing);

    /* Button press */
    RUN_TEST(test_button_press_starts_recording);
    RUN_TEST(test_button_press_in_recording_ignored);

    /* Button release */
    RUN_TEST(test_button_release_stops_recording);
    RUN_TEST(test_button_release_in_idle_ignored);

    /* Recording tick flow */
    RUN_TEST(test_tick_in_recording_processes_audio);
    RUN_TEST(test_multiple_ticks_in_recording);
    RUN_TEST(test_complete_recording_flow);

    /* Statistics */
    RUN_TEST(test_stats_record_count);
    RUN_TEST(test_stats_encode_count);
    RUN_TEST(test_stats_current_state);

    /* Error handling */
    RUN_TEST(test_audio_start_error);
    RUN_TEST(test_tick_error_in_recording);

    /* Timeout */
    RUN_TEST(test_timeout_stops_recording);

    return UNITY_END();
}
