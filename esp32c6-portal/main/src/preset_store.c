#include <stdio.h>
#include <string.h>
#include "preset_store.h"
#include "led_engine.h"
#include "audio_engine.h"
#include "nvs_manager.h"

#ifdef ESP_PLATFORM
#include "nvs.h"
#endif

#define PRESETS_NVS_KEY "presets_blob"
#define PRESETS_BLOB_MAGIC 0x584D4153UL // "XMAS"

typedef struct {
    uint32_t magic;
    uint32_t count;
    tree_preset_t items[PRESET_MAX_COUNT];
} preset_blob_t;

static tree_preset_t s_presets[PRESET_MAX_COUNT];
static size_t s_preset_count = 0;
static uint32_t s_next_id = 1;

static void load_default_presets(void) {
    s_preset_count = 3;
    memset(s_presets, 0, sizeof(s_presets));

    // Matches default presets in chatelao/android-xmas-tree-app PresetRepository.kt
    snprintf(s_presets[0].id, PRESET_ID_MAX_LEN, "default-classic");
    snprintf(s_presets[0].name, PRESET_NAME_MAX_LEN, "Klassische Weihnachten");
    s_presets[0].pattern_id = PATTERN_FESTIVE_CANDLE;
    s_presets[0].palette_id = 0;
    s_presets[0].red = 255;
    s_presets[0].green = 60;
    s_presets[0].blue = 10;
    s_presets[0].brightness = 85;
    s_presets[0].speed = 45;
    s_presets[0].melody_id = MELODY_JINGLE_BELLS;
    s_presets[0].volume = 70;
    s_presets[0].tempo = 100;

    snprintf(s_presets[1].id, PRESET_ID_MAX_LEN, "default-rainbow");
    snprintf(s_presets[1].name, PRESET_NAME_MAX_LEN, "Regenbogen-Party");
    s_presets[1].pattern_id = PATTERN_RAINBOW_WAVE;
    s_presets[1].palette_id = 0;
    s_presets[1].red = 0;
    s_presets[1].green = 255;
    s_presets[1].blue = 128;
    s_presets[1].brightness = 90;
    s_presets[1].speed = 75;
    s_presets[1].melody_id = MELODY_DECK_THE_HALLS;
    s_presets[1].volume = 75;
    s_presets[1].tempo = 110;

    snprintf(s_presets[2].id, PRESET_ID_MAX_LEN, "default-silent-night");
    snprintf(s_presets[2].name, PRESET_NAME_MAX_LEN, "Gemuetliche Stille Nacht");
    s_presets[2].pattern_id = PATTERN_TWINKLE;
    s_presets[2].palette_id = 0;
    s_presets[2].red = 255;
    s_presets[2].green = 200;
    s_presets[2].blue = 100;
    s_presets[2].brightness = 55;
    s_presets[2].speed = 30;
    s_presets[2].melody_id = MELODY_SILENT_NIGHT;
    s_presets[2].volume = 50;
    s_presets[2].tempo = 95;
}

static void persist_presets_to_nvs(void) {
#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    if (nvs_open(NVS_NAMESPACE_NAME, NVS_READWRITE, &handle) != ESP_OK) {
        return;
    }
    preset_blob_t blob;
    memset(&blob, 0, sizeof(blob));
    blob.magic = PRESETS_BLOB_MAGIC;
    blob.count = (uint32_t)s_preset_count;
    memcpy(blob.items, s_presets, sizeof(tree_preset_t) * s_preset_count);
    if (nvs_set_blob(handle, PRESETS_NVS_KEY, &blob, sizeof(blob)) == ESP_OK) {
        nvs_commit(handle);
    }
    nvs_close(handle);
#endif
}

void preset_store_init(void) {
    load_default_presets();
    s_next_id = 1;

#ifdef ESP_PLATFORM
    nvs_handle_t handle;
    if (nvs_open(NVS_NAMESPACE_NAME, NVS_READONLY, &handle) == ESP_OK) {
        preset_blob_t blob;
        size_t len = sizeof(blob);
        if (nvs_get_blob(handle, PRESETS_NVS_KEY, &blob, &len) == ESP_OK &&
            len == sizeof(blob) &&
            blob.magic == PRESETS_BLOB_MAGIC &&
            blob.count <= PRESET_MAX_COUNT) {
            s_preset_count = blob.count;
            memcpy(s_presets, blob.items, sizeof(tree_preset_t) * s_preset_count);
        }
        nvs_close(handle);
    }
#endif
}

size_t preset_store_count(void) {
    return s_preset_count;
}

bool preset_store_get(size_t index, tree_preset_t *out_preset) {
    if (index >= s_preset_count || out_preset == NULL) {
        return false;
    }
    *out_preset = s_presets[index];
    return true;
}

bool preset_store_find_by_id(const char *id, tree_preset_t *out_preset) {
    if (id == NULL || id[0] == '\0') return false;
    for (size_t i = 0; i < s_preset_count; i++) {
        if (strcmp(s_presets[i].id, id) == 0) {
            if (out_preset != NULL) *out_preset = s_presets[i];
            return true;
        }
    }
    return false;
}

static void sanitize_preset(tree_preset_t *p) {
    if (!protocol_is_valid_pattern(p->pattern_id)) p->pattern_id = PATTERN_OFF;
    if (p->palette_id >= TWINKLE_PALETTE_COUNT) p->palette_id = 0;
    if (p->brightness > 100) p->brightness = 100;
    if (p->speed < 1) p->speed = 1;
    if (p->speed > 100) p->speed = 100;
    if (!protocol_is_valid_melody(p->melody_id)) p->melody_id = MELODY_SILENT;
    if (p->volume > 100) p->volume = 100;
    if (p->tempo < 50) p->tempo = 50;
    if (p->tempo > 200) p->tempo = 200;
    p->id[PRESET_ID_MAX_LEN - 1] = '\0';
    p->name[PRESET_NAME_MAX_LEN - 1] = '\0';
}

bool preset_store_save(const tree_preset_t *preset, tree_preset_t *out_saved) {
    if (preset == NULL || preset->name[0] == '\0') return false;

    tree_preset_t item = *preset;
    sanitize_preset(&item);

    if (item.id[0] == '\0') {
        snprintf(item.id, PRESET_ID_MAX_LEN, "user-%lu", (unsigned long)s_next_id++);
        // Avoid collision with existing IDs
        while (preset_store_find_by_id(item.id, NULL)) {
            snprintf(item.id, PRESET_ID_MAX_LEN, "user-%lu", (unsigned long)s_next_id++);
        }
    }

    // Update existing preset if ID matches
    for (size_t i = 0; i < s_preset_count; i++) {
        if (strcmp(s_presets[i].id, item.id) == 0) {
            s_presets[i] = item;
            persist_presets_to_nvs();
            if (out_saved != NULL) *out_saved = item;
            return true;
        }
    }

    if (s_preset_count >= PRESET_MAX_COUNT) {
        return false;
    }

    s_presets[s_preset_count++] = item;
    persist_presets_to_nvs();
    if (out_saved != NULL) *out_saved = item;
    return true;
}

bool preset_store_delete(const char *id) {
    if (id == NULL || id[0] == '\0') return false;
    for (size_t i = 0; i < s_preset_count; i++) {
        if (strcmp(s_presets[i].id, id) == 0) {
            for (size_t j = i; j + 1 < s_preset_count; j++) {
                s_presets[j] = s_presets[j + 1];
            }
            s_preset_count--;
            persist_presets_to_nvs();
            return true;
        }
    }
    return false;
}

bool preset_store_apply(const char *id) {
    tree_preset_t p;
    if (!preset_store_find_by_id(id, &p)) {
        return false;
    }

    led_engine_cmd_t led = {
        .pattern_id = (pattern_id_t)p.pattern_id,
        .red = p.red,
        .green = p.green,
        .blue = p.blue,
        .brightness = p.brightness,
        .speed = p.speed,
        .palette_id = p.palette_id
    };
    audio_engine_cmd_t audio = {
        .melody_id = (melody_id_t)p.melody_id,
        .playback_state = (p.melody_id == MELODY_SILENT) ? AUDIO_STATE_STOP : AUDIO_STATE_PLAY,
        .volume = p.volume,
        .tempo = p.tempo
    };

    if (!led_engine_send_command(&led) || !audio_engine_send_command(&audio)) {
        return false;
    }
    nvs_save_current_engine_state();
    return true;
}

static size_t append_json_escaped(char *buf, size_t buf_size, size_t pos, const char *str) {
    for (const char *p = str; *p != '\0' && pos + 2 < buf_size; p++) {
        if (*p == '"' || *p == '\\') {
            buf[pos++] = '\\';
            buf[pos++] = *p;
        } else if ((unsigned char)*p >= 0x20) {
            buf[pos++] = *p;
        }
    }
    if (pos < buf_size) buf[pos] = '\0';
    return pos;
}

size_t preset_store_to_json(char *out_buf, size_t buf_size) {
    if (out_buf == NULL || buf_size < 4) return 0;

    size_t pos = 0;
    out_buf[pos++] = '[';
    for (size_t i = 0; i < s_preset_count; i++) {
        const tree_preset_t *p = &s_presets[i];
        if (i > 0 && pos + 1 < buf_size) out_buf[pos++] = ',';
        int n = snprintf(out_buf + pos, buf_size - pos, "{\"id\":\"");
        if (n < 0 || pos + (size_t)n >= buf_size) break;
        pos += (size_t)n;
        pos = append_json_escaped(out_buf, buf_size, pos, p->id);

        n = snprintf(out_buf + pos, buf_size - pos, "\",\"name\":\"");
        if (n < 0 || pos + (size_t)n >= buf_size) break;
        pos += (size_t)n;
        pos = append_json_escaped(out_buf, buf_size, pos, p->name);

        n = snprintf(
            out_buf + pos,
            buf_size - pos,
            "\",\"pattern_id\":%u,\"palette_id\":%u,\"red\":%u,\"green\":%u,\"blue\":%u,"
            "\"brightness\":%u,\"speed\":%u,\"melody_id\":%u,\"volume\":%u,\"tempo\":%u}",
            p->pattern_id, p->palette_id, p->red, p->green, p->blue,
            p->brightness, p->speed, p->melody_id, p->volume, p->tempo
        );
        if (n < 0 || pos + (size_t)n >= buf_size) break;
        pos += (size_t)n;
    }
    if (pos + 2 <= buf_size) {
        out_buf[pos++] = ']';
        out_buf[pos] = '\0';
    } else {
        out_buf[buf_size - 1] = '\0';
    }
    return pos;
}
