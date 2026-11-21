#include <stdio.h>
#include <string.h>
#include "nvs_manager.h"
#include "led_engine.h"
#include "audio_engine.h"

#ifdef ESP_PLATFORM
#include "nvs.h"
#include "nvs_flash.h"
#endif

static const nvs_saved_state_t s_factory_defaults = {
    .pattern_id = PATTERN_TWINKLE_FOX,
    .palette_id = 0,
    .red = 255,
    .green = 120,
    .blue = 30,
    .brightness = 70,
    .speed = 50,
    .melody_id = MELODY_SILENT,
    .volume = 60,
    .tempo = 100
};

static nvs_saved_state_t s_nvs_state;
static bool s_nvs_initialized = false;
static system_error_code_t s_error_code = ERROR_CODE_OK;

static nvs_saved_state_t clamp_state(const nvs_saved_state_t *in) {
    nvs_saved_state_t out = *in;
    if (!protocol_is_valid_pattern(out.pattern_id)) out.pattern_id = PATTERN_TWINKLE_FOX;
    if (out.palette_id >= TWINKLE_PALETTE_COUNT) out.palette_id = 0;
    if (out.brightness > 100) out.brightness = 100;
    if (out.speed < 1) out.speed = 1;
    if (out.speed > 100) out.speed = 100;
    if (!protocol_is_valid_melody(out.melody_id)) out.melody_id = MELODY_SILENT;
    if (out.volume > 100) out.volume = 100;
    if (out.tempo < 50) out.tempo = 50;
    if (out.tempo > 200) out.tempo = 200;
    return out;
}

void nvs_manager_init(void) {
    s_nvs_state = s_factory_defaults;
    s_error_code = ERROR_CODE_OK;

#ifdef ESP_PLATFORM
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        if (nvs_flash_erase() == ESP_OK) {
            err = nvs_flash_init();
        }
    }
    if (err != ESP_OK) {
        s_nvs_initialized = false;
        s_error_code = ERROR_CODE_NVS_ERROR;
        return;
    }
#endif
    s_nvs_initialized = true;
}

bool nvs_manager_is_initialized(void) {
    return s_nvs_initialized;
}

system_error_code_t nvs_manager_get_error_code(void) {
    return s_error_code;
}

void nvs_manager_set_error_code(system_error_code_t code) {
    s_error_code = code;
}

bool nvs_save_system_state(const nvs_saved_state_t *state) {
    if (state == NULL) return false;
    if (!s_nvs_initialized) {
        nvs_manager_init();
        if (!s_nvs_initialized) return false;
    }

    nvs_saved_state_t sanitized = clamp_state(state);
    s_nvs_state = sanitized;

#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    if (nvs_open(NVS_NAMESPACE_NAME, NVS_READWRITE, &handle) != ESP_OK) {
        s_error_code = ERROR_CODE_NVS_ERROR;
        return false;
    }

    bool ok = true;
    ok &= (nvs_set_u8(handle, "pattern_id", sanitized.pattern_id) == ESP_OK);
    ok &= (nvs_set_u8(handle, "palette_id", sanitized.palette_id) == ESP_OK);
    ok &= (nvs_set_u8(handle, "red", sanitized.red) == ESP_OK);
    ok &= (nvs_set_u8(handle, "green", sanitized.green) == ESP_OK);
    ok &= (nvs_set_u8(handle, "blue", sanitized.blue) == ESP_OK);
    ok &= (nvs_set_u8(handle, "brightness", sanitized.brightness) == ESP_OK);
    ok &= (nvs_set_u8(handle, "speed", sanitized.speed) == ESP_OK);
    ok &= (nvs_set_u8(handle, "melody_id", sanitized.melody_id) == ESP_OK);
    ok &= (nvs_set_u8(handle, "volume", sanitized.volume) == ESP_OK);
    ok &= (nvs_set_u8(handle, "tempo", sanitized.tempo) == ESP_OK);

    if (ok) ok &= (nvs_commit(handle) == ESP_OK);
    nvs_close(handle);

    if (!ok) {
        s_error_code = ERROR_CODE_NVS_ERROR;
        return false;
    }
#endif
    return true;
}

bool nvs_load_system_state(nvs_saved_state_t *out_state) {
    if (out_state == NULL) return false;
    if (!s_nvs_initialized) {
        nvs_manager_init();
        if (!s_nvs_initialized) return false;
    }

#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    if (nvs_open(NVS_NAMESPACE_NAME, NVS_READONLY, &handle) == ESP_OK) {
        nvs_saved_state_t loaded = s_factory_defaults;
        (void)nvs_get_u8(handle, "pattern_id", &loaded.pattern_id);
        (void)nvs_get_u8(handle, "palette_id", &loaded.palette_id);
        (void)nvs_get_u8(handle, "red", &loaded.red);
        (void)nvs_get_u8(handle, "green", &loaded.green);
        (void)nvs_get_u8(handle, "blue", &loaded.blue);
        (void)nvs_get_u8(handle, "brightness", &loaded.brightness);
        (void)nvs_get_u8(handle, "speed", &loaded.speed);
        (void)nvs_get_u8(handle, "melody_id", &loaded.melody_id);
        (void)nvs_get_u8(handle, "volume", &loaded.volume);
        (void)nvs_get_u8(handle, "tempo", &loaded.tempo);
        nvs_close(handle);
        s_nvs_state = clamp_state(&loaded);
    }
#endif

    *out_state = s_nvs_state;
    return true;
}

bool nvs_apply_saved_state_to_engines(void) {
    nvs_saved_state_t saved;
    if (!nvs_load_system_state(&saved)) return false;

    led_engine_cmd_t led_cmd = {
        .pattern_id = (pattern_id_t)saved.pattern_id,
        .red = saved.red,
        .green = saved.green,
        .blue = saved.blue,
        .brightness = saved.brightness,
        .speed = saved.speed,
        .palette_id = saved.palette_id
    };

    audio_engine_cmd_t audio_cmd = {
        .melody_id = (melody_id_t)saved.melody_id,
        .playback_state = AUDIO_STATE_STOP, // Never auto-blast buzzer on boot
        .volume = saved.volume,
        .tempo = saved.tempo
    };

    return led_engine_send_command(&led_cmd) && audio_engine_send_command(&audio_cmd);
}

bool nvs_save_current_engine_state(void) {
    led_engine_cmd_t led;
    audio_engine_cmd_t audio;
    led_engine_get_current_state(&led);
    audio_engine_get_current_state(&audio);

    nvs_saved_state_t state = {
        .pattern_id = (uint8_t)led.pattern_id,
        .palette_id = led.palette_id,
        .red = led.red,
        .green = led.green,
        .blue = led.blue,
        .brightness = led.brightness,
        .speed = led.speed,
        .melody_id = (uint8_t)audio.melody_id,
        .volume = audio.volume,
        .tempo = audio.tempo
    };
    return nvs_save_system_state(&state);
}
