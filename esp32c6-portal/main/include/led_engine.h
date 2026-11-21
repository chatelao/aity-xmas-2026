#ifndef LED_ENGINE_H
#define LED_ENGINE_H

#include <stdbool.h>
#include <stdint.h>
#include "board_config.h"
#include "protocol_spec.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    pattern_id_t pattern_id;
    uint8_t red;
    uint8_t green;
    uint8_t blue;
    uint8_t brightness; // 0..100
    uint8_t speed;      // 1..100
    uint8_t palette_id; // 0..9 (TwinkleFOX palette / Shockwave epicenter / Segment mode)
} led_engine_cmd_t;

typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} rgb_color_t;

typedef struct {
    uint8_t gpio_pin;
    uint32_t clock_hz;
    uint16_t t0h_ns;
    uint16_t t0l_ns;
    uint16_t t1h_ns;
    uint16_t t1l_ns;
    uint32_t reset_ns;
} ws2812b_rmt_config_t;

void led_engine_init(void);
void led_engine_task(void *param);
bool led_engine_send_command(const led_engine_cmd_t *cmd);
void led_engine_get_current_state(led_engine_cmd_t *out_state);
ws2812b_rmt_config_t led_engine_get_rmt_timing(void);

// Pure rendering function (host-testable and used by ESP32-C6 FreeRTOS task)
bool led_engine_render_frame(const led_engine_cmd_t *cmd,
                             uint32_t frame_index,
                             rgb_color_t *out_pixels,
                             uint16_t num_leds);

#ifdef __cplusplus
}
#endif

#endif // LED_ENGINE_H
