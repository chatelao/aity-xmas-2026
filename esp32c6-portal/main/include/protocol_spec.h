#ifndef PROTOCOL_SPEC_H
#define PROTOCOL_SPEC_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Pattern IDs (100% parity with chatelao/android-xmas-tree-app)
typedef enum {
    PATTERN_OFF            = 0,
    PATTERN_STATIC         = 1,
    PATTERN_RAINBOW_WAVE   = 2,
    PATTERN_SPARKLE        = 3,
    PATTERN_FESTIVE_CANDLE = 4,
    PATTERN_TWINKLE        = 5,
    PATTERN_COMET_CHASE    = 6,
    PATTERN_SEGMENTS       = 7,
    PATTERN_RADIAL_WAVE    = 8,
    PATTERN_PLASMA         = 9,
    PATTERN_POLAR_VORTEX   = 10,
    PATTERN_GRAVITY_PULSE  = 11,
    PATTERN_TWINKLE_FOX    = 12
} pattern_id_t;

#define PATTERN_COUNT         13
#define TWINKLE_PALETTE_COUNT 10
#define EPICENTER_COUNT       4
#define SEGMENT_MODE_COUNT    7

// Melody IDs (100% parity with chatelao/android-xmas-tree-app)
typedef enum {
    MELODY_SILENT         = 0,
    MELODY_JINGLE_BELLS   = 1,
    MELODY_WE_WISH_YOU    = 2,
    MELODY_SILENT_NIGHT   = 3,
    MELODY_DECK_THE_HALLS = 4
} melody_id_t;

#define MELODY_COUNT 5

// Playback States
typedef enum {
    AUDIO_STATE_STOP  = 0,
    AUDIO_STATE_PLAY  = 1,
    AUDIO_STATE_PAUSE = 2
} audio_state_t;

// Tree Hardware Types
typedef enum {
    TREE_TYPE_PCB  = 0,
    TREE_TYPE_HOLZ = 1
} tree_type_t;

#define TREE_TYPE_COUNT 2

// System Error Codes
typedef enum {
    ERROR_CODE_OK               = 0x00,
    ERROR_CODE_NVS_ERROR        = 0x01,
    ERROR_CODE_LED_TIMING_ERROR = 0x02
} system_error_code_t;

static inline bool protocol_is_valid_pattern(uint8_t id) {
    return id < PATTERN_COUNT;
}

static inline bool protocol_is_valid_melody(uint8_t id) {
    return id < MELODY_COUNT;
}

static inline bool protocol_is_valid_playback_state(uint8_t state) {
    return state <= AUDIO_STATE_PAUSE;
}

static inline bool protocol_is_valid_tree_type(uint8_t type) {
    return type < TREE_TYPE_COUNT;
}

#ifdef __cplusplus
}
#endif

#endif // PROTOCOL_SPEC_H
