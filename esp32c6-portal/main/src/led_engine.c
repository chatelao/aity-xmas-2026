#include <math.h>
#include <stdio.h>
#include <string.h>
#include "led_engine.h"
#include "nvs_manager.h"

#ifdef ESP_PLATFORM
#include "driver/rmt_tx.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"
#include "freertos/task.h"
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifdef ESP_PLATFORM
static const char *TAG = "led_engine";
static portMUX_TYPE s_led_mux = portMUX_INITIALIZER_UNLOCKED;
static rmt_channel_handle_t s_led_chan = NULL;
static rmt_encoder_handle_t s_bytes_encoder = NULL;
#endif

static led_engine_cmd_t s_current_led_state = {
    .pattern_id = PATTERN_TWINKLE_FOX,
    .red = 255,
    .green = 120,
    .blue = 30,
    .brightness = 70,
    .speed = 50,
    .palette_id = 0
};

typedef struct {
    float x;
    float y;
    uint8_t seg;
} pixel_coord_t;

// Exact 60-LED PCB coordinates from aity-xmas-2026 (in mm)
static const pixel_coord_t s_pixel_coords[LED_STRIP_NUM_LEDS] = {
    // Segment 0: Lower Bough (0..17)
    {38.862f,  8.912f, 0}, {37.076f,  6.998f, 0}, {35.100f,  5.281f, 0},
    {32.956f,  3.781f, 0}, {30.667f,  2.512f, 0}, {28.257f,  1.491f, 0},
    {25.754f,  0.726f, 0}, {23.184f,  0.227f, 0}, {20.577f,  0.000f, 0},
    {17.960f,  0.046f, 0}, {15.362f,  0.365f, 0}, {12.812f,  0.955f, 0},
    {10.337f,  1.807f, 0}, { 7.965f,  2.914f, 0}, { 5.722f,  4.262f, 0},
    { 3.631f,  5.838f, 0}, { 1.717f,  7.623f, 0}, { 0.000f,  9.599f, 0},
    // Segment 1: Middle Bough (18..31)
    {36.328f, 14.954f, 1}, {33.885f, 14.017f, 1}, {31.357f, 13.340f, 1},
    {28.773f, 12.932f, 1}, {26.159f, 12.796f, 1}, {23.546f, 12.934f, 1},
    {20.961f, 13.344f, 1}, {18.434f, 14.022f, 1}, {15.991f, 14.961f, 1},
    {13.660f, 16.149f, 1}, {11.465f, 17.576f, 1}, { 9.432f, 19.223f, 1},
    { 7.582f, 21.074f, 1}, { 5.936f, 23.109f, 1},
    // Segment 2: Upper Bough (32..44)
    {36.468f, 25.383f, 2}, {33.855f, 25.247f, 2}, {31.243f, 25.385f, 2},
    {28.658f, 25.795f, 2}, {26.131f, 26.473f, 2}, {23.688f, 27.412f, 2},
    {21.357f, 28.601f, 2}, {19.163f, 30.027f, 2}, {17.130f, 31.674f, 2},
    {15.280f, 33.525f, 2}, {13.634f, 35.559f, 2}, {12.209f, 37.754f, 2},
    {11.022f, 40.087f, 2},
    // Segment 3: Stem (45..49)
    {19.869f, 39.313f, 3}, {21.903f, 40.961f, 3}, {23.754f, 42.812f, 3},
    {25.401f, 44.846f, 3}, {27.009f, 46.640f, 3},
    // Segment 4: Star (50..59)
    {18.349f, 58.095f, 4}, {17.189f, 56.466f, 4}, {14.681f, 63.964f, 4},
    {16.589f, 63.365f, 4}, {21.247f, 66.711f, 4}, {21.207f, 68.551f, 4},
    {27.692f, 64.094f, 4}, {25.796f, 63.456f, 4}, {23.828f, 57.956f, 4},
    {25.013f, 56.345f, 4}
};

static const float s_epicenters[EPICENTER_COUNT][2] = {
    {21.1591f, 61.9003f}, // 0: Star
    {23.7540f, 42.8120f}, // 1: Stem
    {19.4310f, 34.2755f}, // 2: Tree Center
    {20.5770f, 12.7960f}  // 3: Base
};

static const rgb_color_t s_seg_colors[6] = {
    {  0, 180, 255}, // VSeg 0: Lower Bough (Ice Blue)
    {  0, 255,  80}, // VSeg 1: Middle Bough (Emerald)
    {120,   0, 255}, // VSeg 2: Upper Bough (Violet)
    {255,   0, 140}, // VSeg 3: Stem (Pink)
    {255,  40,   0}, // VSeg 4: Star Inner (Fire Red)
    {255, 180,   0}  // VSeg 5: Star Outer (Gold)
};

// TwinkleFOX palette base colors
#define TF_RED         {255,   0,   0}
#define TF_GREEN       {  0, 255,   0}
#define TF_BLUE        {  0,   0, 255}
#define TF_WHITE       {255, 255, 255}
#define TF_C9_RED      {184,   4,   0}
#define TF_C9_ORANGE   {144,  44,   2}
#define TF_C9_GREEN    {  4,  98,   2}
#define TF_C9_BLUE     {  7,   7,  88}
#define TF_C9_WHITE    {224, 160,  64}
#define TF_FAIRY_FULL  {255, 157,  42}
#define TF_FAIRY_HALF  {127,  78,  21}
#define TF_FAIRY_QTR   { 63,  39,  10}
#define TF_HOLLY_GRN   {  0,  88,  12}
#define TF_HOLLY_RED   {176,   4,   2}
#define TF_SNOW_WHITE  {224, 240, 255}
#define TF_SNOW_HALF   { 48,  56,  64}
#define TF_ICE_BLUE1   { 12,  60, 180}
#define TF_ICE_BLUE2   { 24, 128, 255}
#define TF_ICE_BLUE3   {160, 220, 255}
#define TF_MAGENTA     {255,   0, 200}
#define TF_LIGHT_GREEN {100, 255, 120}
#define TF_MINT_CYAN   {  0, 220, 255}
#define TF_SOFT_VIOLET {170,  80, 255}

static const rgb_color_t s_twinkle_palettes[TWINKLE_PALETTE_COUNT][16] = {
    // 0: Retro C9
    {TF_C9_RED, TF_C9_ORANGE, TF_C9_RED, TF_C9_ORANGE, TF_C9_ORANGE, TF_C9_RED, TF_C9_ORANGE, TF_C9_RED,
     TF_C9_GREEN, TF_C9_GREEN, TF_C9_GREEN, TF_C9_GREEN, TF_C9_BLUE, TF_C9_BLUE, TF_C9_BLUE, TF_C9_WHITE},
    // 1: Holly
    {TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN,
     TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_GRN, TF_HOLLY_RED},
    // 2: Fairy Light
    {TF_FAIRY_FULL, TF_FAIRY_FULL, TF_FAIRY_FULL, TF_FAIRY_FULL, TF_FAIRY_HALF, TF_FAIRY_HALF, TF_FAIRY_FULL, TF_FAIRY_FULL,
     TF_FAIRY_QTR, TF_FAIRY_QTR, TF_FAIRY_FULL, TF_FAIRY_FULL, TF_FAIRY_FULL, TF_FAIRY_FULL, TF_FAIRY_FULL, TF_FAIRY_FULL},
    // 3: Red-Green-White
    {TF_RED, TF_RED, TF_RED, TF_RED, TF_RED, TF_RED, TF_RED, TF_GREEN,
     TF_GREEN, TF_GREEN, TF_GREEN, TF_GREEN, TF_GREEN, TF_GREEN, TF_WHITE, TF_WHITE},
    // 4: Candy Cane
    {TF_RED, TF_RED, TF_RED, TF_RED, TF_RED, TF_RED, TF_RED, TF_RED,
     TF_WHITE, TF_WHITE, TF_WHITE, TF_WHITE, TF_WHITE, TF_WHITE, TF_WHITE, TF_WHITE},
    // 5: Glitter Snow
    {TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF,
     TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_HALF, TF_SNOW_WHITE},
    // 6: Ice Crystal
    {TF_ICE_BLUE1, TF_ICE_BLUE1, TF_ICE_BLUE1, TF_ICE_BLUE1, TF_ICE_BLUE1, TF_ICE_BLUE1, TF_ICE_BLUE1, TF_ICE_BLUE1,
     TF_ICE_BLUE2, TF_ICE_BLUE2, TF_ICE_BLUE2, TF_ICE_BLUE2, TF_ICE_BLUE2, TF_ICE_BLUE3, TF_ICE_BLUE3, TF_SNOW_WHITE},
    // 7: Blue Winter Night
    {TF_BLUE, TF_BLUE, TF_BLUE, TF_BLUE, TF_BLUE, TF_BLUE, TF_BLUE, TF_BLUE,
     TF_BLUE, TF_BLUE, TF_BLUE, TF_BLUE, TF_BLUE, TF_WHITE, TF_WHITE, TF_WHITE},
    // 8: Rainbow
    {{255,0,0},{255,64,0},{255,128,0},{255,192,0},{255,255,0},{128,255,0},{0,255,0},{0,255,128},
     {0,255,255},{0,128,255},{0,0,255},{64,0,255},{128,0,255},{192,0,255},{255,0,255},{255,0,128}},
    // 9: Magenta-Green
    {TF_MAGENTA, TF_MAGENTA, TF_MAGENTA, TF_MAGENTA, TF_MAGENTA, TF_SOFT_VIOLET, TF_SOFT_VIOLET, TF_SOFT_VIOLET,
     TF_LIGHT_GREEN, TF_LIGHT_GREEN, TF_LIGHT_GREEN, TF_LIGHT_GREEN, TF_LIGHT_GREEN, TF_MINT_CYAN, TF_MINT_CYAN, TF_MINT_CYAN}
};

#ifdef ESP_PLATFORM
static bool led_rmt_init(void) {
    if (s_led_chan != NULL && s_bytes_encoder != NULL) {
        return true;
    }

    rmt_tx_channel_config_t tx_chan_cfg = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .gpio_num = LED_STRIP_GPIO_PIN,
        .mem_block_symbols = 64,
        .resolution_hz = 10000000, // 10 MHz -> 100 ns per tick
        .trans_queue_depth = 4,
    };

    if (rmt_new_tx_channel(&tx_chan_cfg, &s_led_chan) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create RMT TX channel on GPIO %d", LED_STRIP_GPIO_PIN);
        nvs_manager_set_error_code(ERROR_CODE_LED_TIMING_ERROR);
        return false;
    }

    // WS2812B bit timing at 10 MHz (1 tick = 100 ns):
    //   0-bit: 400 ns HIGH, 800 ns LOW
    //   1-bit: 800 ns HIGH, 500 ns LOW
    rmt_bytes_encoder_config_t bytes_cfg = {
        .bit0 = {
            .level0 = 1,
            .duration0 = 4,
            .level1 = 0,
            .duration1 = 8,
        },
        .bit1 = {
            .level0 = 1,
            .duration0 = 8,
            .level1 = 0,
            .duration1 = 5,
        },
        .flags.msb_first = 1,
    };

    if (rmt_new_bytes_encoder(&bytes_cfg, &s_bytes_encoder) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create RMT bytes encoder");
        nvs_manager_set_error_code(ERROR_CODE_LED_TIMING_ERROR);
        return false;
    }

    if (rmt_enable(s_led_chan) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable RMT TX channel");
        nvs_manager_set_error_code(ERROR_CODE_LED_TIMING_ERROR);
        return false;
    }

    ESP_LOGI(TAG, "WS2812B RMT driver ready on GPIO %d (%d LEDs)", LED_STRIP_GPIO_PIN, LED_STRIP_NUM_LEDS);
    return true;
}

static void led_rmt_flush(const rgb_color_t *pixels, uint16_t num_leds) {
    if (s_led_chan == NULL || s_bytes_encoder == NULL) {
        return;
    }

    uint8_t grb_buf[LED_STRIP_NUM_LEDS * 3];
    uint16_t count = (num_leds > LED_STRIP_NUM_LEDS) ? LED_STRIP_NUM_LEDS : num_leds;
    for (uint16_t i = 0; i < count; i++) {
        grb_buf[i * 3 + 0] = pixels[i].g;
        grb_buf[i * 3 + 1] = pixels[i].r;
        grb_buf[i * 3 + 2] = pixels[i].b;
    }

    rmt_transmit_config_t tx_cfg = {
        .loop_count = 0,
        .flags.eot_level = 0,
    };
    if (rmt_transmit(s_led_chan, s_bytes_encoder, grb_buf, count * 3, &tx_cfg) == ESP_OK) {
        rmt_tx_wait_all_done(s_led_chan, pdMS_TO_TICKS(50));
    }
}
#endif

void led_engine_init(void) {
#ifdef ESP_PLATFORM
    portENTER_CRITICAL(&s_led_mux);
#endif
    s_current_led_state.pattern_id = PATTERN_TWINKLE_FOX;
    s_current_led_state.red = 255;
    s_current_led_state.green = 120;
    s_current_led_state.blue = 30;
    s_current_led_state.brightness = 70;
    s_current_led_state.speed = 50;
    s_current_led_state.palette_id = 0;
#ifdef ESP_PLATFORM
    portEXIT_CRITICAL(&s_led_mux);
    led_rmt_init();
#endif
}

void led_engine_task(void *param) {
    (void)param;
#ifdef ESP_PLATFORM
    led_rmt_init();
    rgb_color_t frame[LED_STRIP_NUM_LEDS];
    uint32_t frame_idx = 0;

    for (;;) {
        led_engine_cmd_t cmd;
        led_engine_get_current_state(&cmd);
        if (led_engine_render_frame(&cmd, frame_idx++, frame, LED_STRIP_NUM_LEDS)) {
            led_rmt_flush(frame, LED_STRIP_NUM_LEDS);
        }
        vTaskDelay(pdMS_TO_TICKS(LED_FRAME_PERIOD_MS));
    }
#endif
}

bool led_engine_send_command(const led_engine_cmd_t *cmd) {
    if (cmd == NULL || !protocol_is_valid_pattern((uint8_t)cmd->pattern_id)) {
        return false;
    }
    led_engine_cmd_t sanitized = *cmd;
    if (sanitized.brightness > 100) sanitized.brightness = 100;
    if (sanitized.speed < 1) sanitized.speed = 1;
    if (sanitized.speed > 100) sanitized.speed = 100;
    if (sanitized.palette_id >= TWINKLE_PALETTE_COUNT) sanitized.palette_id = 0;

#ifdef ESP_PLATFORM
    portENTER_CRITICAL(&s_led_mux);
#endif
    s_current_led_state = sanitized;
#ifdef ESP_PLATFORM
    portEXIT_CRITICAL(&s_led_mux);
#endif
    return true;
}

void led_engine_get_current_state(led_engine_cmd_t *out_state) {
    if (out_state == NULL) {
        return;
    }
#ifdef ESP_PLATFORM
    portENTER_CRITICAL(&s_led_mux);
#endif
    *out_state = s_current_led_state;
#ifdef ESP_PLATFORM
    portEXIT_CRITICAL(&s_led_mux);
#endif
}

ws2812b_rmt_config_t led_engine_get_rmt_timing(void) {
    ws2812b_rmt_config_t config = {
        .gpio_pin = LED_STRIP_GPIO_PIN,
        .clock_hz = 10000000UL,
        .t0h_ns = 400,
        .t0l_ns = 800,
        .t1h_ns = 800,
        .t1l_ns = 500,
        .reset_ns = 280000UL
    };
    return config;
}

static void hsv_to_rgb(uint8_t hue, uint8_t val, uint8_t *r, uint8_t *g, uint8_t *b) {
    if (val == 0) {
        *r = 0;
        *g = 0;
        *b = 0;
        return;
    }
    uint8_t region = hue / 43;
    uint8_t remainder = (uint8_t)((hue - (region * 43)) * 6);
    uint8_t q = (uint8_t)((val * (255 - remainder)) >> 8);
    uint8_t t = (uint8_t)((val * remainder) >> 8);
    switch (region) {
        case 0: *r = val; *g = t;   *b = 0;   break;
        case 1: *r = q;   *g = val; *b = 0;   break;
        case 2: *r = 0;   *g = val; *b = t;   break;
        case 3: *r = 0;   *g = q;   *b = val; break;
        case 4: *r = t;   *g = 0;   *b = val; break;
        default: *r = val; *g = 0;  *b = q;   break;
    }
}

static uint8_t get_virtual_segment(uint16_t idx) {
    if (idx < 18) return 0;
    if (idx < 32) return 1;
    if (idx < 45) return 2;
    if (idx < 50) return 3;
    if (idx == 50 || idx == 53 || idx == 54 || idx == 57 || idx == 58) return 4;
    return 5;
}

static uint8_t attack_decay_wave8(uint8_t i) {
    if (i < 86) {
        return (uint8_t)(i * 3);
    }
    i -= 86;
    return (uint8_t)(255 - (i + (i >> 1)));
}

static rgb_color_t compute_one_twinkle(uint32_t ms,
                                       uint16_t salt,
                                       const rgb_color_t palette16[16],
                                       uint8_t speed,
                                       uint8_t density) {
    uint16_t prng16 = (uint16_t)(((salt + 1U) * 2053U + 1384U) & 0xFFFFU);
    uint8_t shift = (speed <= 8U) ? (uint8_t)(8U - speed) : 0U;
    uint32_t my_clock30 = (ms >> shift) & 0x3FFFFFFFUL;

    uint16_t clock_offset = prng16;
    prng16 = (uint16_t)((prng16 * 2053U + 1384U) & 0xFFFFU);
    uint16_t speed_mult = (uint16_t)(((((prng16 & 0xFFU) >> 4) + (prng16 & 0x0FU)) & 0x0FU) + 0x08U);

    uint32_t my_clock = ((my_clock30 * speed_mult) >> 3) + clock_offset;
    uint8_t my_unique8 = (uint8_t)((prng16 >> 8) & 0xFFU);

    uint16_t ticks = (uint16_t)((my_clock >> 8) & 0xFFFFU);
    uint8_t phase = (uint8_t)(my_clock & 0xFFU);

    uint16_t wave_hash = (uint16_t)(((ticks * 2053U) + 1384U + my_unique8) & 0xFFFFU);
    uint8_t slowcycle8 = (uint8_t)(((wave_hash >> 8) + (wave_hash & 0xFFU)) & 0xFFU);
    uint8_t color_index = (uint8_t)((slowcycle8 - salt) & 0xFFU);

    rgb_color_t c = {0, 0, 0};
    if (((slowcycle8 & 0x0EU) >> 1) < density) {
        uint8_t bri = attack_decay_wave8(phase);
        if (bri > 0) {
            rgb_color_t base = palette16[(color_index >> 4) & 0x0F];
            uint16_t scale = (uint16_t)bri + 1U;
            c.r = (uint8_t)((base.r * scale) >> 8);
            c.g = (uint8_t)((base.g * scale) >> 8);
            c.b = (uint8_t)((base.b * scale) >> 8);

            if (phase >= 128) {
                uint8_t cooling = (uint8_t)((phase - 128U) * 2U);
                c.g = (uint8_t)((c.g * (256U - (cooling >> 1))) >> 8);
                c.b = (uint8_t)((c.b * (256U - cooling)) >> 8);
            }
        }
    }
    return c;
}

static rgb_color_t scale_rgb(rgb_color_t c, uint8_t bright_pct) {
    rgb_color_t out = {
        (uint8_t)(((uint16_t)c.r * bright_pct) / 100U),
        (uint8_t)(((uint16_t)c.g * bright_pct) / 100U),
        (uint8_t)(((uint16_t)c.b * bright_pct) / 100U)
    };
    return out;
}

bool led_engine_render_frame(const led_engine_cmd_t *cmd,
                             uint32_t frame_index,
                             rgb_color_t *out_pixels,
                             uint16_t num_leds) {
    if (cmd == NULL || out_pixels == NULL || num_leds == 0) {
        return false;
    }

    uint8_t bright = (cmd->brightness > 100) ? 100 : cmd->brightness;
    uint8_t spd = (cmd->speed == 0) ? 1 : cmd->speed;

    switch (cmd->pattern_id) {
        case PATTERN_OFF: {
            memset(out_pixels, 0, sizeof(rgb_color_t) * num_leds);
            break;
        }

        case PATTERN_STATIC: {
            rgb_color_t c = scale_rgb((rgb_color_t){cmd->red, cmd->green, cmd->blue}, bright);
            for (uint16_t i = 0; i < num_leds; i++) {
                out_pixels[i] = c;
            }
            break;
        }

        case PATTERN_RAINBOW_WAVE: {
            uint8_t val = (uint8_t)((255U * bright) / 100U);
            for (uint16_t i = 0; i < num_leds; i++) {
                uint8_t hue = (uint8_t)(((i * 256U / num_leds) + (frame_index * spd / 5U)) % 256U);
                hsv_to_rgb(hue, val, &out_pixels[i].r, &out_pixels[i].g, &out_pixels[i].b);
            }
            break;
        }

        case PATTERN_SPARKLE: {
            uint8_t dim_r = (uint8_t)((uint16_t)cmd->red * bright / 300U);
            uint8_t dim_g = (uint8_t)((uint16_t)cmd->green * bright / 300U);
            uint8_t dim_b = (uint8_t)((uint16_t)cmd->blue * bright / 300U);

            uint8_t bright_r = (uint8_t)((uint16_t)cmd->red * bright / 100U);
            uint8_t bright_g = (uint8_t)((uint16_t)cmd->green * bright / 100U);
            uint8_t bright_b = (uint8_t)((uint16_t)cmd->blue * bright / 100U);

            for (uint16_t i = 0; i < num_leds; i++) {
                uint32_t hash = (i * 2654435761u + frame_index * spd * 1103515245u) & 0xFFFFFFu;
                if ((hash % 100u) < 15u) {
                    out_pixels[i] = (rgb_color_t){bright_r, bright_g, bright_b};
                } else {
                    out_pixels[i] = (rgb_color_t){dim_r, dim_g, dim_b};
                }
            }
            break;
        }

        case PATTERN_FESTIVE_CANDLE: {
            uint8_t base_r = (uint8_t)((uint16_t)cmd->red * bright / 100U);
            uint8_t base_g = (uint8_t)((uint16_t)cmd->green * bright / 100U);
            uint8_t base_b = (uint8_t)((uint16_t)cmd->blue * bright / 100U);

            for (uint16_t i = 0; i < num_leds; i++) {
                uint32_t flicker = ((i * 17u + frame_index * spd * 7u) % 50u);
                out_pixels[i].r = base_r;
                out_pixels[i].g = (uint8_t)((base_g * (50u + flicker)) / 100u);
                out_pixels[i].b = (uint8_t)(base_b / 4u);
            }
            break;
        }

        case PATTERN_TWINKLE: {
            for (uint16_t i = 0; i < num_leds; i++) {
                uint8_t phase = (uint8_t)((i * 37u + frame_index * spd / 2u) % 256u);
                uint8_t factor = (phase < 128u) ? (uint8_t)(phase * 2u) : (uint8_t)((255u - phase) * 2u);
                out_pixels[i].r = (uint8_t)((uint32_t)cmd->red * bright / 100u * factor / 255u);
                out_pixels[i].g = (uint8_t)((uint32_t)cmd->green * bright / 100u * factor / 255u);
                out_pixels[i].b = (uint8_t)((uint32_t)cmd->blue * bright / 100u * factor / 255u);
            }
            break;
        }

        case PATTERN_COMET_CHASE: {
            bool is_black = (cmd->red == 0 && cmd->green == 0 && cmd->blue == 0);
            uint8_t hr = is_black ? 0   : cmd->red;
            uint8_t hg = is_black ? 220 : cmd->green;
            uint8_t hb = is_black ? 255 : cmd->blue;
            uint16_t head = (uint16_t)(((frame_index * spd) / 10U) % num_leds);
            for (uint16_t i = 0; i < num_leds; i++) {
                uint16_t dist = (head >= i) ? (uint16_t)(head - i) : (uint16_t)(num_leds - i + head);
                if (dist < 8U) {
                    rgb_color_t c = {
                        (uint8_t)(hr >> dist),
                        (uint8_t)(hg >> dist),
                        (uint8_t)(hb >> dist)
                    };
                    out_pixels[i] = scale_rgb(c, bright);
                } else {
                    out_pixels[i] = (rgb_color_t){0, 0, 0};
                }
            }
            break;
        }

        case PATTERN_SEGMENTS: {
            uint8_t active_vseg = (cmd->palette_id >= 1 && cmd->palette_id <= 6)
                ? (uint8_t)(cmd->palette_id - 1U)
                : (uint8_t)(((frame_index * spd) / 300U) % 6U);
            for (uint16_t i = 0; i < num_leds; i++) {
                if (get_virtual_segment(i) == active_vseg) {
                    out_pixels[i] = scale_rgb(s_seg_colors[active_vseg], bright);
                } else {
                    out_pixels[i] = (rgb_color_t){0, 0, 0};
                }
            }
            break;
        }

        case PATTERN_RADIAL_WAVE: {
            uint8_t epi_idx = (uint8_t)(cmd->palette_id % EPICENTER_COUNT);
            float ox = s_epicenters[epi_idx][0];
            float oy = s_epicenters[epi_idx][1];
            float radius = fmodf((float)frame_index * (0.4f + (float)spd * 0.03f), 95.0f);
            const float wave_width = 9.0f;

            for (uint16_t i = 0; i < num_leds; i++) {
                uint16_t ci = i % LED_STRIP_NUM_LEDS;
                float dx = s_pixel_coords[ci].x - ox;
                float dy = s_pixel_coords[ci].y - oy;
                float dist = sqrtf(dx * dx + dy * dy);
                float d = fabsf(dist - radius);
                if (d < wave_width) {
                    float intensity = 1.0f - (d / wave_width);
                    float intensity_sq = intensity * intensity;
                    rgb_color_t base = s_seg_colors[s_pixel_coords[ci].seg % 5];
                    uint16_t white_boost = (uint16_t)(180.0f * intensity_sq * intensity_sq);
                    uint16_t r = (uint16_t)((float)base.r * intensity_sq) + white_boost;
                    uint16_t g = (uint16_t)((float)base.g * intensity_sq) + white_boost;
                    uint16_t b = (uint16_t)((float)base.b * intensity_sq) + white_boost;
                    rgb_color_t c = {
                        (r > 255) ? 255 : (uint8_t)r,
                        (g > 255) ? 255 : (uint8_t)g,
                        (b > 255) ? 255 : (uint8_t)b
                    };
                    out_pixels[i] = scale_rgb(c, bright);
                } else {
                    out_pixels[i] = (rgb_color_t){0, 0, 0};
                }
            }
            break;
        }

        case PATTERN_PLASMA: {
            float t = (float)frame_index * (0.01f + (float)spd * 0.0012f);
            float cx = s_epicenters[2][0];
            float cy = s_epicenters[2][1];
            uint8_t val = (uint8_t)((255U * bright) / 100U);

            for (uint16_t i = 0; i < num_leds; i++) {
                uint16_t ci = i % LED_STRIP_NUM_LEDS;
                float dx = s_pixel_coords[ci].x - cx;
                float dy = s_pixel_coords[ci].y - cy;
                float nx = dx * 0.08f;
                float ny = dy * 0.08f;
                float r = sqrtf(dx * dx + dy * dy);
                float v1 = sinf(nx + t * 2.1f);
                float v2 = sinf(ny + t * 1.7f);
                float v3 = sinf((nx + ny + r * 0.12f) - t * 2.5f);
                float hue_f = fmodf((v1 + v2 + v3) * 0.16f + (float)s_pixel_coords[ci].seg * 0.04f + 4.0f, 1.0f);
                uint8_t hue = (uint8_t)(hue_f * 255.0f);
                hsv_to_rgb(hue, val, &out_pixels[i].r, &out_pixels[i].g, &out_pixels[i].b);
            }
            break;
        }

        case PATTERN_POLAR_VORTEX: {
            float t = (float)frame_index * (0.01f + (float)spd * 0.0012f);
            float cx = s_epicenters[2][0];
            float cy = s_epicenters[2][1];
            float angle_sweep = t * 3.5f;

            for (uint16_t i = 0; i < num_leds; i++) {
                uint16_t ci = i % LED_STRIP_NUM_LEDS;
                float dx = s_pixel_coords[ci].x - cx;
                float dy = s_pixel_coords[ci].y - cy;
                float r = sqrtf(dx * dx + dy * dy);
                float theta = atan2f(dy, dx);
                float wave = (sinf(theta * 2.0f - angle_sweep + r * 0.15f) + 1.0f) * 0.5f;
                float hue_f = fmodf((theta / (2.0f * (float)M_PI)) + t * 0.1f + 2.0f, 1.0f);
                uint8_t hue = (uint8_t)(hue_f * 255.0f);
                uint8_t val = (uint8_t)(((255.0f * bright) / 100.0f) * wave);
                hsv_to_rgb(hue, val, &out_pixels[i].r, &out_pixels[i].g, &out_pixels[i].b);
            }
            break;
        }

        case PATTERN_GRAVITY_PULSE: {
            float t = (float)frame_index * (0.01f + (float)spd * 0.0012f);
            float y_front = 68.551f - fmodf(t * 48.0f, 80.0f);

            for (uint16_t i = 0; i < num_leds; i++) {
                uint16_t ci = i % LED_STRIP_NUM_LEDS;
                float dist_y = s_pixel_coords[ci].y - y_front;
                if (dist_y >= 0.0f && dist_y < 22.0f) {
                    float val_f = 1.0f - (dist_y / 22.0f);
                    float hue_f = fmodf((float)s_pixel_coords[ci].seg * 0.08f + dist_y * 0.01f, 1.0f);
                    uint8_t hue = (uint8_t)(hue_f * 255.0f);
                    uint8_t val = (uint8_t)(((255.0f * bright) / 100.0f) * val_f);
                    hsv_to_rgb(hue, val, &out_pixels[i].r, &out_pixels[i].g, &out_pixels[i].b);
                } else {
                    out_pixels[i] = (rgb_color_t){0, 0, 0};
                }
            }
            break;
        }

        case PATTERN_TWINKLE_FOX: {
            uint8_t pal_idx = (uint8_t)(cmd->palette_id % TWINKLE_PALETTE_COUNT);
            uint8_t tf_speed = (uint8_t)((spd * 8U) / 100U);
            if (tf_speed < 2U) tf_speed = 2U;
            uint8_t tf_density = 5U;
            uint32_t ms = frame_index * LED_FRAME_PERIOD_MS;

            for (uint16_t i = 0; i < num_leds; i++) {
                const rgb_color_t *pal = (i >= 50U) ? s_twinkle_palettes[2] : s_twinkle_palettes[pal_idx];
                rgb_color_t c = compute_one_twinkle(ms, i, pal, tf_speed, tf_density);
                out_pixels[i] = scale_rgb(c, bright);
            }
            break;
        }

        default:
            return false;
    }

    return true;
}
