#include <stdio.h>
#include "audio_engine.h"
#include "board_config.h"
#include "dns_server.h"
#include "http_server.h"
#include "led_engine.h"
#include "nvs_manager.h"
#include "preset_store.h"
#include "wifi_ap.h"

#ifdef ESP_PLATFORM
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "xmas_main";

void app_main(void) {
    ESP_LOGI(TAG, "AITY Xmas Tree 2026 Captive Portal Firmware v%s", XMAS_FIRMWARE_VERSION);
    ESP_LOGI(TAG, "Board: Seeed Studio XIAO ESP32-C6 | LEDs: GPIO%d (%d) | Speaker: GPIO%d",
             LED_STRIP_GPIO_PIN, LED_STRIP_NUM_LEDS, SPEAKER_LEDC_GPIO_PIN);

    // 1. Initialize NVS flash storage
    nvs_manager_init();

    // 2. Initialize LED & Audio engines and restore saved state + presets
    led_engine_init();
    audio_engine_init();
    nvs_apply_saved_state_to_engines();
    preset_store_init();

    // 3. Start real-time FreeRTOS tasks for LEDs (50 FPS) and Audio (RTTTL PWM)
    xTaskCreate(led_engine_task, "led_engine", 4096, NULL, 6, NULL);
    xTaskCreate(audio_engine_task, "audio_engine", 4096, NULL, 5, NULL);

    // 4. Bring up Wi-Fi SoftAP + Captive Portal DNS + HTTP Web Server
    if (!wifi_ap_start()) {
        ESP_LOGE(TAG, "Failed to start Wi-Fi SoftAP");
        return;
    }
    dns_server_start();
    if (!http_server_start()) {
        ESP_LOGE(TAG, "Failed to start HTTP server");
        return;
    }

    ESP_LOGI(TAG, "Zero-install Captive Portal ready! Connect to Wi-Fi \"%s\" -> http://%s/",
             XMAS_AP_SSID, XMAS_AP_IP_STR);
}
#endif
