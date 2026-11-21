#include <string.h>
#include "wifi_ap.h"
#include "board_config.h"

#ifdef ESP_PLATFORM
#include "driver/gpio.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#endif

#ifdef ESP_PLATFORM
static const char *TAG = "wifi_ap";
#endif

static volatile uint8_t s_station_count = 0;

void wifi_ap_configure_xiao_antenna(void) {
#ifdef ESP_PLATFORM
    // Seeed Studio XIAO ESP32-C6 RF Switch:
    //   GPIO 3  = LOW enables RF switch power
    //   GPIO 14 = LOW selects onboard ceramic antenna, HIGH selects external U.FL
    gpio_config_t rf_cfg = {
        .pin_bit_mask = (1ULL << XIAO_RF_SWITCH_ENABLE_GPIO) | (1ULL << XIAO_RF_SWITCH_SELECT_GPIO),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&rf_cfg);
    gpio_set_level(XIAO_RF_SWITCH_ENABLE_GPIO, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(XIAO_RF_SWITCH_SELECT_GPIO, XIAO_USE_EXTERNAL_ANTENNA ? 1 : 0);

    // Status LED on GPIO 15 (active LOW)
    gpio_config_t led_cfg = {
        .pin_bit_mask = (1ULL << XIAO_STATUS_LED_GPIO),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&led_cfg);
    gpio_set_level(XIAO_STATUS_LED_GPIO, 1); // OFF initially (active LOW)

    ESP_LOGI(TAG, "XIAO ESP32-C6 RF switch enabled (%s antenna)",
             XIAO_USE_EXTERNAL_ANTENNA ? "external U.FL" : "onboard ceramic");
#endif
}

#ifdef ESP_PLATFORM
static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data) {
    (void)arg;
    if (event_base == WIFI_EVENT) {
        if (event_id == WIFI_EVENT_AP_STACONNECTED) {
            wifi_event_ap_staconnected_t *ev = (wifi_event_ap_staconnected_t *)event_data;
            s_station_count++;
            gpio_set_level(XIAO_STATUS_LED_GPIO, 0); // LED ON while client connected
            ESP_LOGI(TAG, "Station " MACSTR " joined (total=%u)", MAC2STR(ev->mac), s_station_count);
        } else if (event_id == WIFI_EVENT_AP_STADISCONNECTED) {
            wifi_event_ap_stadisconnected_t *ev = (wifi_event_ap_stadisconnected_t *)event_data;
            if (s_station_count > 0) s_station_count--;
            if (s_station_count == 0) {
                gpio_set_level(XIAO_STATUS_LED_GPIO, 1); // LED OFF when idle
            }
            ESP_LOGI(TAG, "Station " MACSTR " left (total=%u)", MAC2STR(ev->mac), s_station_count);
        }
    }
}
#endif

bool wifi_ap_start(void) {
    s_station_count = 0;

#ifdef ESP_PLATFORM
    wifi_ap_configure_xiao_antenna();

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_t *ap_netif = esp_netif_create_default_wifi_ap();
    if (ap_netif == NULL) {
        ESP_LOGE(TAG, "Failed to create default Wi-Fi AP netif");
        return false;
    }

    // Configure static AP IP (192.168.4.1/24)
    esp_netif_dhcps_stop(ap_netif);
    esp_netif_ip_info_t ip_info = {0};
    IP4_ADDR(&ip_info.ip, XMAS_AP_IP_OCTET_0, XMAS_AP_IP_OCTET_1, XMAS_AP_IP_OCTET_2, XMAS_AP_IP_OCTET_3);
    IP4_ADDR(&ip_info.gw, XMAS_AP_IP_OCTET_0, XMAS_AP_IP_OCTET_1, XMAS_AP_IP_OCTET_2, XMAS_AP_IP_OCTET_3);
    IP4_ADDR(&ip_info.netmask, 255, 255, 255, 0);
    esp_netif_set_ip_info(ap_netif, &ip_info);
    esp_netif_dhcps_start(ap_netif);

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, NULL));

    wifi_config_t wifi_cfg = {0};
    strncpy((char *)wifi_cfg.ap.ssid, XMAS_AP_SSID, sizeof(wifi_cfg.ap.ssid) - 1);
    wifi_cfg.ap.ssid_len = (uint8_t)strlen(XMAS_AP_SSID);
    wifi_cfg.ap.channel = XMAS_AP_CHANNEL;
    wifi_cfg.ap.max_connection = XMAS_AP_MAX_CLIENTS;
    if (strlen(XMAS_AP_PASSWORD) == 0) {
        wifi_cfg.ap.authmode = WIFI_AUTH_OPEN;
    } else {
        strncpy((char *)wifi_cfg.ap.password, XMAS_AP_PASSWORD, sizeof(wifi_cfg.ap.password) - 1);
        wifi_cfg.ap.authmode = WIFI_AUTH_WPA2_PSK;
    }

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &wifi_cfg));
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "SoftAP started: SSID=\"%s\" IP=%s (open zero-install captive portal)",
             XMAS_AP_SSID, XMAS_AP_IP_STR);
#endif
    return true;
}

uint8_t wifi_ap_get_station_count(void) {
    return s_station_count;
}

uint32_t wifi_ap_get_uptime_seconds(void) {
#ifdef ESP_PLATFORM
    return (uint32_t)(esp_timer_get_time() / 1000000LL);
#else
    return 0;
#endif
}
