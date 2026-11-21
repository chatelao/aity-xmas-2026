#ifndef HTTP_SERVER_H
#define HTTP_SERVER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Host-testable helpers for captive portal detection & REST JSON API
bool http_is_captive_portal_probe_uri(const char *uri);
bool http_is_portal_host(const char *host);

size_t http_build_status_json(char *out_buf, size_t buf_size, uint32_t uptime_s, uint8_t sta_count);
bool http_handle_lighting_json(const char *json_body);
bool http_handle_audio_json(const char *json_body);
bool http_handle_preset_save_json(const char *json_body);
bool http_handle_preset_apply_json(const char *json_body);
bool http_handle_preset_delete_json(const char *json_body);

bool http_server_start(void);

#ifdef __cplusplus
}
#endif

#endif // HTTP_SERVER_H
