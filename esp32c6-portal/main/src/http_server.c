#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "http_server.h"
#include "audio_engine.h"
#include "board_config.h"
#include "led_engine.h"
#include "nvs_manager.h"
#include "preset_store.h"
#include "web_ui_gz.h"
#include "wifi_ap.h"

#ifdef ESP_PLATFORM
#include "esp_http_server.h"
#include "esp_log.h"
#endif

#ifdef ESP_PLATFORM
static const char *TAG = "http_server";
static httpd_handle_t s_server = NULL;
#endif

// --- Minimal, safe JSON helpers (zero external dependencies) ---

static const char *find_json_value(const char *json, const char *key) {
    if (json == NULL || key == NULL) return NULL;
    char pattern[64];
    int n = snprintf(pattern, sizeof(pattern), "\"%s\"", key);
    if (n <= 0 || (size_t)n >= sizeof(pattern)) return NULL;

    const char *p = json;
    while ((p = strstr(p, pattern)) != NULL) {
        p += n;
        while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
        if (*p == ':') {
            p++;
            while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
            return p;
        }
    }
    return NULL;
}

static bool json_get_int(const char *json, const char *key, int *out_val) {
    const char *v = find_json_value(json, key);
    if (v == NULL || out_val == NULL) return false;
    if (*v != '-' && !isdigit((unsigned char)*v)) return false;
    char *end = NULL;
    long parsed = strtol(v, &end, 10);
    if (end == v) return false;
    *out_val = (int)parsed;
    return true;
}

static bool json_get_string(const char *json, const char *key, char *out_buf, size_t out_size) {
    const char *v = find_json_value(json, key);
    if (v == NULL || out_buf == NULL || out_size == 0 || *v != '"') return false;
    v++;
    size_t pos = 0;
    while (*v != '\0' && *v != '"' && pos + 1 < out_size) {
        if (*v == '\\' && *(v + 1) != '\0') {
            v++;
        }
        out_buf[pos++] = *v++;
    }
    out_buf[pos] = '\0';
    return (*v == '"');
}

// --- Captive Portal URI & Host Detection ---

static const char *const s_probe_uris[] = {
    "/generate_204",
    "/gen_204",
    "/hotspot-detect.html",
    "/library/test/success.html",
    "/connecttest.txt",
    "/ncsi.txt",
    "/redirect",
    "/fwlink",
    "/canonical.html",
    "/success.txt",
    "/mobile/status.php",
    NULL
};

bool http_is_captive_portal_probe_uri(const char *uri) {
    if (uri == NULL) return false;
    for (size_t i = 0; s_probe_uris[i] != NULL; i++) {
        if (strcmp(uri, s_probe_uris[i]) == 0) {
            return true;
        }
    }
    return false;
}

bool http_is_portal_host(const char *host) {
    if (host == NULL || host[0] == '\0') return true;
    // Strip optional :80 port suffix
    size_t ip_len = strlen(XMAS_AP_IP_STR);
    if (strncmp(host, XMAS_AP_IP_STR, ip_len) == 0 &&
        (host[ip_len] == '\0' || host[ip_len] == ':')) {
        return true;
    }
    if (strncmp(host, "xmastree.local", 14) == 0 &&
        (host[14] == '\0' || host[14] == ':')) {
        return true;
    }
    return false;
}

// --- REST JSON Handlers (Pure logic, host-testable) ---

size_t http_build_status_json(char *out_buf, size_t buf_size, uint32_t uptime_s, uint8_t sta_count) {
    if (out_buf == NULL || buf_size < 32) return 0;

    led_engine_cmd_t led;
    audio_engine_cmd_t audio;
    led_engine_get_current_state(&led);
    audio_engine_get_current_state(&audio);

    int n = snprintf(
        out_buf,
        buf_size,
        "{\"uptime\":%lu,\"pattern_id\":%u,\"palette_id\":%u,"
        "\"red\":%u,\"green\":%u,\"blue\":%u,"
        "\"brightness\":%u,\"speed\":%u,"
        "\"tree_type\":\"%s\","
        "\"melody_id\":%u,\"playback_state\":%u,\"volume\":%u,\"tempo\":%u,"
        "\"sta_count\":%u,\"error_code\":%u,"
        "\"ssid\":\"%s\",\"ip\":\"%s\",\"firmware\":\"%s\"}",
        (unsigned long)uptime_s,
        (unsigned)led.pattern_id,
        (unsigned)led.palette_id,
        (unsigned)led.red,
        (unsigned)led.green,
        (unsigned)led.blue,
        (unsigned)led.brightness,
        (unsigned)led.speed,
        (led.tree_type == TREE_TYPE_HOLZ) ? "Holz" : "PCB",
        (unsigned)audio.melody_id,
        (unsigned)audio.playback_state,
        (unsigned)audio.volume,
        (unsigned)audio.tempo,
        (unsigned)sta_count,
        (unsigned)nvs_manager_get_error_code(),
        XMAS_AP_SSID,
        XMAS_AP_IP_STR,
        XMAS_FIRMWARE_VERSION
    );

    if (n < 0) return 0;
    return ((size_t)n >= buf_size) ? (buf_size - 1) : (size_t)n;
}

static bool ascii_ieq(const char *a, const char *b) {
    while (*a && *b) {
        char ca = (*a >= 'A' && *a <= 'Z') ? (char)(*a + 32) : *a;
        char cb = (*b >= 'A' && *b <= 'Z') ? (char)(*b + 32) : *b;
        if (ca != cb) return false;
        a++;
        b++;
    }
    return *a == '\0' && *b == '\0';
}

bool http_handle_lighting_json(const char *json_body) {
    if (json_body == NULL) return false;

    led_engine_cmd_t cmd;
    led_engine_get_current_state(&cmd);

    int val = 0;
    if (json_get_int(json_body, "pattern_id", &val)) {
        if (val < 0 || !protocol_is_valid_pattern((uint8_t)val)) return false;
        cmd.pattern_id = (pattern_id_t)val;
    }
    if (json_get_int(json_body, "palette_id", &val)) {
        if (val < 0 || val >= TWINKLE_PALETTE_COUNT) return false;
        cmd.palette_id = (uint8_t)val;
    }
    if (json_get_int(json_body, "red", &val)) {
        if (val < 0 || val > 255) return false;
        cmd.red = (uint8_t)val;
    }
    if (json_get_int(json_body, "green", &val)) {
        if (val < 0 || val > 255) return false;
        cmd.green = (uint8_t)val;
    }
    if (json_get_int(json_body, "blue", &val)) {
        if (val < 0 || val > 255) return false;
        cmd.blue = (uint8_t)val;
    }
    if (json_get_int(json_body, "brightness", &val)) {
        if (val < 0 || val > 100) return false;
        cmd.brightness = (uint8_t)val;
    }
    if (json_get_int(json_body, "speed", &val)) {
        if (val < 1 || val > 100) return false;
        cmd.speed = (uint8_t)val;
    }
    char tt_str[16];
    if (json_get_string(json_body, "tree_type", tt_str, sizeof(tt_str))) {
        if (ascii_ieq(tt_str, "holz")) {
            cmd.tree_type = TREE_TYPE_HOLZ;
        } else if (ascii_ieq(tt_str, "pcb")) {
            cmd.tree_type = TREE_TYPE_PCB;
        } else {
            return false;
        }
    } else if (json_get_int(json_body, "tree_type", &val)) {
        if (val < 0 || !protocol_is_valid_tree_type((uint8_t)val)) return false;
        cmd.tree_type = (uint8_t)val;
    }

    if (!led_engine_send_command(&cmd)) return false;
    nvs_save_current_engine_state();
    return true;
}

bool http_handle_audio_json(const char *json_body) {
    if (json_body == NULL) return false;

    audio_engine_cmd_t cmd;
    audio_engine_get_current_state(&cmd);

    int freq_hz = 0;
    if (json_get_int(json_body, "freq_hz", &freq_hz) && freq_hz > 0) {
        int dur_ms = 250;
        int vol = cmd.volume;
        (void)json_get_int(json_body, "duration_ms", &dur_ms);
        (void)json_get_int(json_body, "volume", &vol);
        if (vol < 0) vol = 0;
        if (vol > 100) vol = 100;
        return audio_engine_play_tone((uint16_t)freq_hz, (uint32_t)dur_ms, (uint8_t)vol);
    }

    int val = 0;
    if (json_get_int(json_body, "melody_id", &val)) {
        if (val < 0 || !protocol_is_valid_melody((uint8_t)val)) return false;
        cmd.melody_id = (melody_id_t)val;
    }
    if (json_get_int(json_body, "playback_state", &val)) {
        if (val < 0 || !protocol_is_valid_playback_state((uint8_t)val)) return false;
        cmd.playback_state = (audio_state_t)val;
    }
    if (json_get_int(json_body, "volume", &val)) {
        if (val < 0 || val > 100) return false;
        cmd.volume = (uint8_t)val;
    }
    if (json_get_int(json_body, "tempo", &val)) {
        if (val < 50 || val > 200) return false;
        cmd.tempo = (uint8_t)val;
    }

    if (!audio_engine_send_command(&cmd)) return false;
    nvs_save_current_engine_state();
    return true;
}

bool http_handle_preset_save_json(const char *json_body) {
    if (json_body == NULL) return false;

    tree_preset_t p;
    memset(&p, 0, sizeof(p));

    if (!json_get_string(json_body, "name", p.name, sizeof(p.name)) || p.name[0] == '\0') {
        return false;
    }
    (void)json_get_string(json_body, "id", p.id, sizeof(p.id));

    // Seed with current engine state, then override with any fields provided in JSON
    led_engine_cmd_t led;
    audio_engine_cmd_t audio;
    led_engine_get_current_state(&led);
    audio_engine_get_current_state(&audio);

    p.pattern_id = (uint8_t)led.pattern_id;
    p.palette_id = led.palette_id;
    p.red = led.red;
    p.green = led.green;
    p.blue = led.blue;
    p.brightness = led.brightness;
    p.speed = led.speed;
    p.melody_id = (uint8_t)audio.melody_id;
    p.volume = audio.volume;
    p.tempo = audio.tempo;

    int val = 0;
    if (json_get_int(json_body, "pattern_id", &val)) p.pattern_id = (uint8_t)val;
    if (json_get_int(json_body, "palette_id", &val)) p.palette_id = (uint8_t)val;
    if (json_get_int(json_body, "red", &val))        p.red = (uint8_t)val;
    if (json_get_int(json_body, "green", &val))      p.green = (uint8_t)val;
    if (json_get_int(json_body, "blue", &val))       p.blue = (uint8_t)val;
    if (json_get_int(json_body, "brightness", &val)) p.brightness = (uint8_t)val;
    if (json_get_int(json_body, "speed", &val))      p.speed = (uint8_t)val;
    if (json_get_int(json_body, "melody_id", &val))  p.melody_id = (uint8_t)val;
    if (json_get_int(json_body, "volume", &val))     p.volume = (uint8_t)val;
    if (json_get_int(json_body, "tempo", &val))      p.tempo = (uint8_t)val;

    return preset_store_save(&p, NULL);
}

bool http_handle_preset_apply_json(const char *json_body) {
    if (json_body == NULL) return false;
    char id[PRESET_ID_MAX_LEN] = {0};
    if (!json_get_string(json_body, "id", id, sizeof(id)) || id[0] == '\0') {
        return false;
    }
    return preset_store_apply(id);
}

bool http_handle_preset_delete_json(const char *json_body) {
    if (json_body == NULL) return false;
    char id[PRESET_ID_MAX_LEN] = {0};
    if (!json_get_string(json_body, "id", id, sizeof(id)) || id[0] == '\0') {
        return false;
    }
    return preset_store_delete(id);
}

// --- ESP-IDF HTTP Server Integration ---

#ifdef ESP_PLATFORM

static esp_err_t send_portal_redirect(httpd_req_t *req) {
    httpd_resp_set_status(req, "302 Found");
    httpd_resp_set_hdr(req, "Location", "http://" XMAS_AP_IP_STR "/");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store, no-cache, must-revalidate");
    return httpd_resp_send(req, NULL, 0);
}

static bool read_req_body(httpd_req_t *req, char *buf, size_t buf_size) {
    if (req->content_len <= 0 || (size_t)req->content_len >= buf_size) {
        return false;
    }
    int total = 0;
    while (total < req->content_len) {
        int r = httpd_req_recv(req, buf + total, req->content_len - total);
        if (r <= 0) {
            if (r == HTTPD_SOCK_ERR_TIMEOUT) continue;
            return false;
        }
        total += r;
    }
    buf[total] = '\0';
    return true;
}

static esp_err_t send_status_response(httpd_req_t *req) {
    char json[512];
    size_t len = http_build_status_json(
        json, sizeof(json), wifi_ap_get_uptime_seconds(), wifi_ap_get_station_count());
    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    return httpd_resp_send(req, json, (ssize_t)len);
}

static esp_err_t send_presets_response(httpd_req_t *req) {
    char *json = (char *)malloc(4096);
    if (json == NULL) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }
    size_t len = preset_store_to_json(json, 4096);
    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    esp_err_t err = httpd_resp_send(req, json, (ssize_t)len);
    free(json);
    return err;
}

static esp_err_t root_get_handler(httpd_req_t *req) {
    char host[128] = {0};
    if (httpd_req_get_hdr_value_str(req, "Host", host, sizeof(host)) == ESP_OK) {
        if (!http_is_portal_host(host)) {
            return send_portal_redirect(req);
        }
    }
    httpd_resp_set_type(req, "text/html; charset=utf-8");
    httpd_resp_set_hdr(req, "Content-Encoding", "gzip");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    return httpd_resp_send(req, (const char *)WEB_UI_GZ_DATA, (ssize_t)WEB_UI_GZ_LEN);
}

static esp_err_t probe_get_handler(httpd_req_t *req) {
    return send_portal_redirect(req);
}

static esp_err_t status_get_handler(httpd_req_t *req) {
    return send_status_response(req);
}

static esp_err_t lighting_post_handler(httpd_req_t *req) {
    char body[512];
    if (!read_req_body(req, body, sizeof(body)) || !http_handle_lighting_json(body)) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Invalid lighting payload");
        return ESP_OK;
    }
    return send_status_response(req);
}

static esp_err_t audio_post_handler(httpd_req_t *req) {
    char body[512];
    if (!read_req_body(req, body, sizeof(body)) || !http_handle_audio_json(body)) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Invalid audio payload");
        return ESP_OK;
    }
    return send_status_response(req);
}

static esp_err_t presets_get_handler(httpd_req_t *req) {
    return send_presets_response(req);
}

static esp_err_t presets_post_handler(httpd_req_t *req) {
    char body[512];
    if (!read_req_body(req, body, sizeof(body)) || !http_handle_preset_save_json(body)) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Invalid preset payload");
        return ESP_OK;
    }
    return send_presets_response(req);
}

static esp_err_t presets_apply_post_handler(httpd_req_t *req) {
    char body[256];
    if (!read_req_body(req, body, sizeof(body)) || !http_handle_preset_apply_json(body)) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Preset not found");
        return ESP_OK;
    }
    return send_status_response(req);
}

static esp_err_t presets_delete_post_handler(httpd_req_t *req) {
    char body[256];
    if (!read_req_body(req, body, sizeof(body)) || !http_handle_preset_delete_json(body)) {
        httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "Preset not found");
        return ESP_OK;
    }
    return send_presets_response(req);
}

static esp_err_t not_found_redirect_handler(httpd_req_t *req, httpd_err_code_t err) {
    (void)err;
    return send_portal_redirect(req);
}

#endif // ESP_PLATFORM

bool http_server_start(void) {
#ifdef ESP_PLATFORM
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = XMAS_HTTP_PORT;
    config.max_uri_handlers = 24;
    config.lru_purge_enable = true;

    if (httpd_start(&s_server, &config) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start HTTP server");
        return false;
    }

    const httpd_uri_t routes[] = {
        { .uri = "/",                   .method = HTTP_GET,  .handler = root_get_handler },
        { .uri = "/api/status",         .method = HTTP_GET,  .handler = status_get_handler },
        { .uri = "/api/lighting",       .method = HTTP_POST, .handler = lighting_post_handler },
        { .uri = "/api/audio",          .method = HTTP_POST, .handler = audio_post_handler },
        { .uri = "/api/presets",        .method = HTTP_GET,  .handler = presets_get_handler },
        { .uri = "/api/presets",        .method = HTTP_POST, .handler = presets_post_handler },
        { .uri = "/api/presets/apply",  .method = HTTP_POST, .handler = presets_apply_post_handler },
        { .uri = "/api/presets/delete", .method = HTTP_POST, .handler = presets_delete_post_handler },
    };
    for (size_t i = 0; i < sizeof(routes) / sizeof(routes[0]); i++) {
        httpd_register_uri_handler(s_server, &routes[i]);
    }

    // Register explicit captive portal probe endpoints for Android, iOS, macOS, Windows, Firefox
    for (size_t i = 0; s_probe_uris[i] != NULL; i++) {
        httpd_uri_t probe_route = {
            .uri = s_probe_uris[i],
            .method = HTTP_GET,
            .handler = probe_get_handler
        };
        httpd_register_uri_handler(s_server, &probe_route);
    }

    // Redirect any other unknown URI to http://192.168.4.1/
    httpd_register_err_handler(s_server, HTTPD_404_NOT_FOUND, not_found_redirect_handler);

    ESP_LOGI(TAG, "Captive Portal HTTP server running at http://%s/", XMAS_AP_IP_STR);
#endif
    return true;
}
