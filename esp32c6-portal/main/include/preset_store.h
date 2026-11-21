#ifndef PRESET_STORE_H
#define PRESET_STORE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define PRESET_MAX_COUNT 16
#define PRESET_ID_MAX_LEN 24
#define PRESET_NAME_MAX_LEN 36

typedef struct {
    char id[PRESET_ID_MAX_LEN];
    char name[PRESET_NAME_MAX_LEN];
    uint8_t pattern_id;
    uint8_t palette_id;
    uint8_t red;
    uint8_t green;
    uint8_t blue;
    uint8_t brightness;
    uint8_t speed;
    uint8_t melody_id;
    uint8_t volume;
    uint8_t tempo;
} tree_preset_t;

void preset_store_init(void);
size_t preset_store_count(void);
bool preset_store_get(size_t index, tree_preset_t *out_preset);
bool preset_store_find_by_id(const char *id, tree_preset_t *out_preset);
bool preset_store_save(const tree_preset_t *preset, tree_preset_t *out_saved);
bool preset_store_delete(const char *id);
bool preset_store_apply(const char *id);
size_t preset_store_to_json(char *out_buf, size_t buf_size);

#ifdef __cplusplus
}
#endif

#endif // PRESET_STORE_H
