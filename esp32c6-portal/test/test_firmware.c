#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "audio_engine.h"
#include "board_config.h"
#include "dns_server.h"
#include "http_server.h"
#include "led_engine.h"
#include "nvs_manager.h"
#include "preset_store.h"
#include "web_ui_gz.h"

static void test_board_config(void) {
    assert(LED_STRIP_GPIO_PIN == 18);
    assert(LED_STRIP_NUM_LEDS == 60);
    assert(SPEAKER_LEDC_GPIO_PIN == 0);
    assert(XIAO_RF_SWITCH_ENABLE_GPIO == 3);
    assert(XIAO_RF_SWITCH_SELECT_GPIO == 14);
    assert(strcmp(XMAS_AP_IP_STR, "192.168.4.1") == 0);
    printf("[PASS] test_board_config\n");
}

static void test_led_engine_all_patterns(void) {
    led_engine_init();
    ws2812b_rmt_config_t rmt = led_engine_get_rmt_timing();
    assert(rmt.gpio_pin == 18);
    assert(rmt.clock_hz == 10000000UL);

    rgb_color_t pixels[LED_STRIP_NUM_LEDS];

    // Invalid calls
    assert(!led_engine_render_frame(NULL, 0, pixels, LED_STRIP_NUM_LEDS));
    led_engine_cmd_t bad = { .pattern_id = (pattern_id_t)99, .brightness = 50, .speed = 50 };
    assert(!led_engine_send_command(&bad));

    // All 13 patterns render cleanly
    for (uint8_t p = 0; p < PATTERN_COUNT; p++) {
        led_engine_cmd_t cmd = {
            .pattern_id = (pattern_id_t)p,
            .red = 255,
            .green = 120,
            .blue = 40,
            .brightness = 80,
            .speed = 50,
            .palette_id = 0
        };
        assert(led_engine_send_command(&cmd));
        assert(led_engine_render_frame(&cmd, 25, pixels, LED_STRIP_NUM_LEDS));
        if (p == PATTERN_OFF) {
            for (int i = 0; i < LED_STRIP_NUM_LEDS; i++) {
                assert(pixels[i].r == 0 && pixels[i].g == 0 && pixels[i].b == 0);
            }
        } else if (p == PATTERN_STATIC) {
            assert(pixels[0].r == 204 && pixels[0].g == 96 && pixels[0].b == 32);
        } else {
            uint32_t sum = 0;
            for (int i = 0; i < LED_STRIP_NUM_LEDS; i++) {
                sum += pixels[i].r + pixels[i].g + pixels[i].b;
            }
            assert(sum > 0);
        }
    }

    // All 10 TwinkleFOX palettes
    for (uint8_t pal = 0; pal < TWINKLE_PALETTE_COUNT; pal++) {
        led_engine_cmd_t cmd = {
            .pattern_id = PATTERN_TWINKLE_FOX,
            .brightness = 100,
            .speed = 60,
            .palette_id = pal
        };
        assert(led_engine_render_frame(&cmd, 100, pixels, LED_STRIP_NUM_LEDS));
    }

    // Segments manual selection (Star Outer = 6)
    led_engine_cmd_t seg_cmd = {
        .pattern_id = PATTERN_SEGMENTS,
        .brightness = 100,
        .speed = 50,
        .palette_id = 6
    };
    assert(led_engine_render_frame(&seg_cmd, 0, pixels, LED_STRIP_NUM_LEDS));
    assert(pixels[0].r == 0 && pixels[0].g == 0 && pixels[0].b == 0); // Lower bough off
    assert(pixels[51].r == 255 && pixels[51].g == 180 && pixels[51].b == 0); // Star outer gold

    printf("[PASS] test_led_engine_all_patterns\n");
}

static void test_audio_engine(void) {
    audio_engine_init();
    audio_ledc_config_t cfg = audio_engine_get_ledc_config();
    assert(cfg.gpio_pin == 0);
    assert(cfg.is_initialized);

    assert(audio_engine_calc_duty(0, 10) == 0);
    assert(audio_engine_calc_duty(100, 10) == 512);
    assert(audio_engine_note_to_freq('a', false, 4) == 440);
    assert(audio_engine_note_to_freq('a', false, 5) == 880);
    assert(audio_engine_note_to_freq('p', false, 5) == 0);

    // Parse all 4 musical melodies
    for (uint8_t m = MELODY_JINGLE_BELLS; m < MELODY_COUNT; m++) {
        const char *score = audio_engine_get_rtttl_score((melody_id_t)m);
        assert(score != NULL && strlen(score) > 10);
        uint8_t dd = 0, oct = 0;
        uint16_t bpm = 0;
        assert(audio_engine_parse_rtttl_defaults(score, &dd, &oct, &bpm));
        assert(bpm >= 80 && bpm <= 200);
    }

    // Playback state transitions
    audio_engine_cmd_t play_cmd = {
        .melody_id = MELODY_JINGLE_BELLS,
        .playback_state = AUDIO_STATE_PLAY,
        .volume = 75,
        .tempo = 100
    };
    assert(audio_engine_send_command(&play_cmd));
    assert(audio_engine_playback_step());
    audio_playback_state_t pb;
    audio_engine_get_playback_state(&pb);
    assert(pb.is_playing && pb.current_freq_hz > 0 && pb.current_note_duration_ms > 0);

    play_cmd.playback_state = AUDIO_STATE_PAUSE;
    assert(audio_engine_send_command(&play_cmd));
    assert(audio_engine_playback_step());
    audio_engine_get_playback_state(&pb);
    assert(pb.is_paused && pb.current_freq_hz == 0);

    play_cmd.playback_state = AUDIO_STATE_STOP;
    assert(audio_engine_send_command(&play_cmd));
    assert(!audio_engine_playback_step());

    // Direct tone validation
    assert(audio_engine_play_tone(523, 250, 70));
    assert(!audio_engine_play_tone(10, 250, 70));

    printf("[PASS] test_audio_engine\n");
}

static void test_nvs_and_presets(void) {
    nvs_manager_init();
    assert(nvs_manager_is_initialized());

    nvs_saved_state_t st = {
        .pattern_id = PATTERN_PLASMA,
        .palette_id = 3,
        .red = 10, .green = 200, .blue = 250,
        .brightness = 150, // should clamp to 100
        .speed = 0,        // should clamp to 1
        .melody_id = MELODY_SILENT_NIGHT,
        .volume = 80,
        .tempo = 250       // should clamp to 200
    };
    assert(nvs_save_system_state(&st));
    nvs_saved_state_t loaded;
    assert(nvs_load_system_state(&loaded));
    assert(loaded.pattern_id == PATTERN_PLASMA);
    assert(loaded.brightness == 100);
    assert(loaded.speed == 1);
    assert(loaded.tempo == 200);

    preset_store_init();
    assert(preset_store_count() == 3);

    tree_preset_t custom = {
        .name = "My \"Festive\" Mode",
        .pattern_id = PATTERN_TWINKLE_FOX,
        .palette_id = 6,
        .red = 20, .green = 160, .blue = 255,
        .brightness = 90, .speed = 65,
        .melody_id = MELODY_WE_WISH_YOU,
        .volume = 55, .tempo = 105
    };
    tree_preset_t saved;
    assert(preset_store_save(&custom, &saved));
    assert(preset_store_count() == 4);
    assert(preset_store_apply(saved.id));

    led_engine_cmd_t led;
    audio_engine_cmd_t audio;
    led_engine_get_current_state(&led);
    audio_engine_get_current_state(&audio);
    assert(led.pattern_id == PATTERN_TWINKLE_FOX && led.palette_id == 6);
    assert(audio.melody_id == MELODY_WE_WISH_YOU && audio.playback_state == AUDIO_STATE_PLAY);

    char json[2048];
    size_t jlen = preset_store_to_json(json, sizeof(json));
    assert(jlen > 50);
    assert(strstr(json, "Klassische Weihnachten") != NULL);
    assert(strstr(json, "My \\\"Festive\\\" Mode") != NULL);

    assert(preset_store_delete(saved.id));
    assert(preset_store_count() == 3);
    assert(!preset_store_delete("non-existent-id"));

    printf("[PASS] test_nvs_and_presets\n");
}

static void test_dns_captive_portal(void) {
    const uint8_t ap_ip[4] = {192, 168, 4, 1};
    // Minimal DNS query for "connectivitycheck.gstatic.com" Type A (0x0001) Class IN (0x0001)
    uint8_t query_a[] = {
        0x12, 0x34, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x07, 'e','x','a','m','p','l','e',
        0x03, 'c','o','m',
        0x00,
        0x00, 0x01, // QTYPE = A
        0x00, 0x01  // QCLASS = IN
    };
    uint8_t resp[DNS_MAX_PACKET_SIZE];
    size_t rlen = dns_server_build_response(query_a, sizeof(query_a), resp, sizeof(resp), ap_ip);
    assert(rlen == sizeof(query_a) + 16);
    assert(resp[0] == 0x12 && resp[1] == 0x34); // Transaction ID preserved
    assert((resp[2] & 0x80) != 0);              // QR = 1 (response)
    assert(resp[7] == 0x01);                    // ANCOUNT = 1
    assert(resp[rlen - 4] == 192 && resp[rlen - 3] == 168 &&
           resp[rlen - 2] == 4 && resp[rlen - 1] == 1);

    // Type AAAA (0x001C) query -> NOERROR with 0 answers
    uint8_t query_aaaa[sizeof(query_a)];
    memcpy(query_aaaa, query_a, sizeof(query_a));
    query_aaaa[sizeof(query_aaaa) - 3] = 0x1C;
    size_t rlen_aaaa = dns_server_build_response(query_aaaa, sizeof(query_aaaa), resp, sizeof(resp), ap_ip);
    assert(rlen_aaaa == sizeof(query_aaaa));
    assert(resp[7] == 0x00); // ANCOUNT = 0

    // Malformed short packet rejected
    uint8_t short_pkt[8] = {0};
    assert(dns_server_build_response(short_pkt, sizeof(short_pkt), resp, sizeof(resp), ap_ip) == 0);

    printf("[PASS] test_dns_captive_portal\n");
}

static void test_http_portal_and_api(void) {
    assert(http_is_captive_portal_probe_uri("/generate_204"));
    assert(http_is_captive_portal_probe_uri("/hotspot-detect.html"));
    assert(http_is_captive_portal_probe_uri("/connecttest.txt"));
    assert(http_is_captive_portal_probe_uri("/canonical.html"));
    assert(!http_is_captive_portal_probe_uri("/api/status"));

    assert(http_is_portal_host("192.168.4.1"));
    assert(http_is_portal_host("192.168.4.1:80"));
    assert(http_is_portal_host("xmastree.local"));
    assert(!http_is_portal_host("connectivitycheck.gstatic.com"));
    assert(!http_is_portal_host("captive.apple.com"));

    // Lighting API
    assert(http_handle_lighting_json(
        "{\"pattern_id\":12,\"palette_id\":4,\"red\":255,\"green\":0,\"blue\":80,\"brightness\":88,\"speed\":62}"));
    assert(!http_handle_lighting_json("{\"pattern_id\":99}"));

    // Audio API
    assert(http_handle_audio_json(
        "{\"melody_id\":3,\"playback_state\":1,\"volume\":65,\"tempo\":115}"));
    assert(!http_handle_audio_json("{\"tempo\":10}"));

    // Status JSON
    char status[512];
    size_t slen = http_build_status_json(status, sizeof(status), 42, 2);
    assert(slen > 50);
    assert(strstr(status, "\"uptime\":42") != NULL);
    assert(strstr(status, "\"pattern_id\":12") != NULL);
    assert(strstr(status, "\"palette_id\":4") != NULL);
    assert(strstr(status, "\"melody_id\":3") != NULL);
    assert(strstr(status, "\"sta_count\":2") != NULL);
    assert(strstr(status, "\"ssid\":\"AITY-Xmas-Tree\"") != NULL);

    // Presets API
    preset_store_init();
    assert(http_handle_preset_save_json("{\"name\":\"Portal Test\"}"));
    assert(preset_store_count() == 4);
    assert(http_handle_preset_apply_json("{\"id\":\"default-classic\"}"));
    assert(http_handle_preset_delete_json("{\"id\":\"default-rainbow\"}"));
    assert(preset_store_count() == 3);

    // Embedded gzipped Web UI magic bytes (0x1f 0x8b)
    assert(WEB_UI_GZ_LEN > 500);
    assert(WEB_UI_GZ_DATA[0] == 0x1f && WEB_UI_GZ_DATA[1] == 0x8b);

    printf("[PASS] test_http_portal_and_api\n");
}

int main(void) {
    test_board_config();
    test_led_engine_all_patterns();
    test_audio_engine();
    test_nvs_and_presets();
    test_dns_captive_portal();
    test_http_portal_and_api();
    printf("\nAll ESP32-C6 Captive Portal firmware unit tests PASSED!\n");
    return 0;
}
